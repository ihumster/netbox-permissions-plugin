"""``ConstraintSnippet`` -- named, reusable JSON constraint fragment.

Stage-2 building block: snippets let an admin save commonly-used filter
chunks like ``{"slug": "dc1"}`` or ``{"tenant__name": "ACME"}`` once and
reference them by name when building ObjectPermission constraints in the
visual builder (PR D). Object-type assignment limits which CTs the
builder will offer the snippet against, so a "site = DC1" snippet is not
suggested for ``ipam.prefix``.

Inherits from ``NetBoxModel`` so it gets ``created``, ``last_updated``,
``custom_field_data``, ``tags``, journaling, and changelog entries out
of the box -- same UX as any other NetBox object.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel


class ConstraintSnippet(NetBoxModel):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Short, unique identifier shown in the builder dropdown.",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    body = models.JSONField(
        # blank=True so that empty containers (``[]`` -- the NetBox "never
        # matches" idiom -- and ``{}`` -- the unrestricted form) are not
        # rejected by Django's form-level blank check. Structural validity
        # is enforced by ``clean()`` below.
        blank=True,
        help_text=(
            "NetBox-style constraints: a JSON object for AND semantics, "
            'e.g. {"slug": "dc1"}; or a JSON array of objects for OR semantics, '
            'e.g. [{"slug": "dc1"}, {"slug": "dc2"}].'
        ),
    )
    object_types = models.ManyToManyField(
        to=ContentType,
        related_name="+",
        blank=True,
        help_text=(
            "Content types the snippet is applicable to. Leave empty to make "
            "it available regardless of target CT."
        ),
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "constraint snippet"
        verbose_name_plural = "constraint snippets"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse(
            "plugins:netbox_permissions_plugin:constraintsnippet",
            args=[self.pk],
        )

    def clean(self) -> None:
        """Reject body shapes that are not valid NetBox constraints.

        Accepted:
          * ``dict``                     -- AND semantics
          * ``list[dict]``               -- OR semantics
          * ``[]``                       -- never matches (rare, but legal idiom)

        Rejected:
          * non-list / non-dict top level
          * list with any non-dict item
        """
        super().clean()
        body = self.body
        if isinstance(body, dict):
            return
        if isinstance(body, list):
            for i, chunk in enumerate(body):
                if not isinstance(chunk, dict):
                    raise ValidationError({"body": f"Item {i} is not a JSON object."})
            return
        raise ValidationError({"body": "Must be a JSON object or array of objects."})
