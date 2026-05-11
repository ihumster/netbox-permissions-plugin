"""Plugin URL configuration.

The ``/plugins/permissions/`` prefix is added automatically by NetBox from
``PluginConfig.base_url``.

URL naming convention for object views follows the NetBox/Django default
``<model_lower>``, ``<model_lower>_list``, ``<model_lower>_add``,
``<model_lower>_edit``, ``<model_lower>_delete``, ``<model_lower>_bulk_delete``,
``<model_lower>_changelog``, ``<model_lower>_journal``. NetBox's generic
templates (and ``NetBoxTable`` action columns) reverse these by convention.
"""

from __future__ import annotations

from django.urls import path
from netbox.views.generic import ObjectChangeLogView, ObjectJournalView

from .models import ConstraintSnippet
from .views import audit as audit_views
from .views import effective, reverse_lookup, tester
from .views import snippet as snippet_views

app_name = "netbox_permissions_plugin"

urlpatterns = [
    # ---- Stage 1 audit pages ------------------------------------------------
    path("", effective.EffectivePermissionsView.as_view(), name="effective"),
    path(
        "effective/",
        effective.EffectivePermissionsView.as_view(),
        name="effective_alias",
    ),
    path("reverse/", reverse_lookup.ReverseLookupView.as_view(), name="reverse"),
    path("tester/", tester.TesterView.as_view(), name="tester"),
    # ---- Stage 2 ConstraintSnippet CRUD ------------------------------------
    path(
        "constraint-snippets/",
        snippet_views.ConstraintSnippetListView.as_view(),
        name="constraintsnippet_list",
    ),
    path(
        "constraint-snippets/add/",
        snippet_views.ConstraintSnippetEditView.as_view(),
        name="constraintsnippet_add",
    ),
    path(
        "constraint-snippets/delete/",
        snippet_views.ConstraintSnippetBulkDeleteView.as_view(),
        name="constraintsnippet_bulk_delete",
    ),
    path(
        "constraint-snippets/<int:pk>/",
        snippet_views.ConstraintSnippetView.as_view(),
        name="constraintsnippet",
    ),
    path(
        "constraint-snippets/<int:pk>/edit/",
        snippet_views.ConstraintSnippetEditView.as_view(),
        name="constraintsnippet_edit",
    ),
    path(
        "constraint-snippets/<int:pk>/delete/",
        snippet_views.ConstraintSnippetDeleteView.as_view(),
        name="constraintsnippet_delete",
    ),
    # NetBoxModel gives us changelog/journal entries for free; the URLs need
    # to be wired manually so the standard ``NetBoxTable`` actions column and
    # NetBox's generic detail template can reverse them.
    path(
        "constraint-snippets/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="constraintsnippet_changelog",
        kwargs={"model": ConstraintSnippet},
    ),
    path(
        "constraint-snippets/<int:pk>/journal/",
        ObjectJournalView.as_view(),
        name="constraintsnippet_journal",
        kwargs={"model": ConstraintSnippet},
    ),
    # ---- Stage 2 PermissionAuditEvent (read-only) --------------------------
    path(
        "audit-events/",
        audit_views.PermissionAuditEventListView.as_view(),
        name="permissionauditevent_list",
    ),
    path(
        "audit-events/<int:pk>/",
        audit_views.PermissionAuditEventView.as_view(),
        name="permissionauditevent",
    ),
]
