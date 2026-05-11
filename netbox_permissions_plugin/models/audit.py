"""``PermissionAuditEvent`` -- immutable log of plugin actions.

Why a separate stream rather than NetBox's ``extras.ObjectChange``:

* ObjectChange covers writes to NetBoxModel-derived objects, including
  ``users.ObjectPermission`` in 4.x. That captures **what changed**.
* It does not cover **reads** -- which is exactly what compliance tends
  to care about ("who opened the effective-permissions page for user
  Ivanov last Tuesday").

We therefore record both:

  * ``view_*``  -- audit-page reads (user-targeted, object-targeted, ...);
  * ``create_perm`` / ``update_perm`` / ``delete_perm`` -- writes against
    ``users.ObjectPermission`` initiated through the plugin's UI
    (stage 2 PR D);
  * ``create_snippet`` / ``update_snippet`` / ``delete_snippet`` --
    writes against ``ConstraintSnippet``;
  * ``dry_run`` -- preview without commit.

The model is a plain Django ``Model`` (no ``NetBoxModel``) on purpose: we
do **not** want changelog entries about audit entries, and the data is
append-only -- there is no edit/delete UI for it.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from utilities.querysets import RestrictedQuerySet


class ActionType(models.TextChoices):
    """Closed set of action codes emitted into the audit stream.

    String values stay short and snake_case so they index well and remain
    stable across renames. Labels are what shows up in the UI table.
    """

    # Reads (audit-page views).
    VIEW_EFFECTIVE = "view_effective", "View effective permissions"
    VIEW_REVERSE = "view_reverse", "Reverse lookup"
    VIEW_TESTER = "view_tester", "Permission tester"

    # Writes against users.ObjectPermission (stage 2 PR D).
    CREATE_PERM = "create_perm", "Create ObjectPermission"
    UPDATE_PERM = "update_perm", "Update ObjectPermission"
    DELETE_PERM = "delete_perm", "Delete ObjectPermission"

    # Writes against our own models.
    CREATE_SNIPPET = "create_snippet", "Create constraint snippet"
    UPDATE_SNIPPET = "update_snippet", "Update constraint snippet"
    DELETE_SNIPPET = "delete_snippet", "Delete constraint snippet"

    # Preview / dry-run (stage 2 PR C/D).
    DRY_RUN = "dry_run", "Dry-run preview"


class PermissionAuditEvent(models.Model):
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Server-side creation time; cannot be modified after insert.",
    )
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="User who triggered the action (NULL if SSO bootstrap / system).",
    )
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        db_index=True,
    )

    # Optional generic-FK target. For ``view_effective`` it points at the
    # User whose perms were inspected; for ``view_reverse`` -- at the
    # inspected object; for write actions -- at the modified
    # ObjectPermission / snippet. Nullable because some actions
    # (``dry_run``) are CT-only and have no concrete row.
    target_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    target = GenericForeignKey(ct_field="target_type", fk_field="target_id")

    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Free-form per-action details: for writes -- a diff of changed "
            "fields; for views -- the query parameters."
        ),
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # NetBox's generic ObjectListView / ObjectView call ``queryset.restrict(
    # user, action)`` in their permission check; that method lives on
    # ``RestrictedQuerySet``. We don't inherit from NetBoxModel (the log is
    # immutable, no journal/tags/CFs), so we wire RestrictedQuerySet as the
    # default manager ourselves.
    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("-timestamp",)
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["action", "-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
        ]
        # Custom permission so we can gate the audit-log list view
        # independently of who can edit ObjectPermission itself.
        permissions: ClassVar[list[tuple[str, str]]] = [
            ("view_auditevent", "Can view permission audit events"),
        ]
        verbose_name = "permission audit event"
        verbose_name_plural = "permission audit events"

    def __str__(self) -> str:
        who = self.user.username if self.user_id else "<system>"
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} -- {self.action} by {who}"

    def get_absolute_url(self) -> str:
        return reverse(
            "plugins:netbox_permissions_plugin:permissionauditevent",
            args=[self.pk],
        )
