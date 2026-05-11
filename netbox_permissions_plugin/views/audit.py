"""Read-only views for ``PermissionAuditEvent``.

Audit events are immutable: only a list page and a detail page. No edit,
no delete, no bulk operations in the UI. Programmatic deletion (e.g.
retention policy) belongs in a separate management command or admin task.
"""

from __future__ import annotations

from typing import ClassVar

from netbox.views import generic

from ..filtersets import PermissionAuditEventFilterSet
from ..models import PermissionAuditEvent
from ..tables import PermissionAuditEventTable


class PermissionAuditEventListView(generic.ObjectListView):
    queryset = PermissionAuditEvent.objects.select_related("user", "target_type")
    table = PermissionAuditEventTable
    filterset = PermissionAuditEventFilterSet
    # No filterset_form -- the audit page is intentionally minimal; the
    # standard NetBox column filter widgets in the table header are enough.

    # Hide add/edit/delete buttons even from users who happen to have the
    # underlying Django permission -- the log is append-only by design.
    # NetBox 4.x ``ActionsMixin.actions`` is a dict of
    # ``action_name -> required_permissions_set``; we keep only export.
    actions: ClassVar[dict[str, set[str]]] = {"export": set()}


class PermissionAuditEventView(generic.ObjectView):
    queryset = PermissionAuditEvent.objects.select_related("user", "target_type")
