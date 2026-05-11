"""NetBox-style tables for the plugin's own models.

Each table extends ``NetBoxTable`` so it picks up the standard search,
pagination, column toggling, and bulk-action chrome at no cost.
"""

from __future__ import annotations

import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import ConstraintSnippet, PermissionAuditEvent


class ConstraintSnippetTable(NetBoxTable):
    name = tables.Column(linkify=True)
    object_types_count = columns.LinkedCountColumn(
        viewname="plugins:netbox_permissions_plugin:constraintsnippet_list",
        url_params={"object_types_id": "pk"},
        verbose_name="Object types",
    )
    body = tables.Column(verbose_name="Constraint body")
    tags = columns.TagColumn()

    class Meta(NetBoxTable.Meta):
        model = ConstraintSnippet
        fields = (
            "pk",
            "id",
            "name",
            "description",
            "body",
            "object_types_count",
            "tags",
            "created",
            "last_updated",
        )
        default_columns = ("name", "description", "object_types_count", "body")


class PermissionAuditEventTable(NetBoxTable):
    timestamp = tables.DateTimeColumn(linkify=True, format="Y-m-d H:i:s")
    user = tables.Column(linkify=True)
    action = columns.ChoiceFieldColumn()
    target_type = tables.Column(verbose_name="Target type")
    target_id = tables.Column(verbose_name="Target id")
    ip_address = tables.Column(verbose_name="IP")

    # Audit events have no actions menu (immutable). Hide it.
    actions = columns.ActionsColumn(actions=())

    class Meta(NetBoxTable.Meta):
        model = PermissionAuditEvent
        fields = (
            "pk",
            "id",
            "timestamp",
            "user",
            "action",
            "target_type",
            "target_id",
            "ip_address",
        )
        default_columns = ("timestamp", "user", "action", "target_type", "target_id")
