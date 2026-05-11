"""DRF serializers for the plugin's models.

* ``ConstraintSnippetSerializer`` -- ``NetBoxModelSerializer`` base, so we
  inherit ``display`` / ``custom_fields`` / ``tags`` / ``url`` handling for
  free. ``brief_fields`` is required by NetBox 4.x for the brief
  representation used in nested objects.
* ``PermissionAuditEventSerializer`` -- plain ``ModelSerializer`` because
  ``PermissionAuditEvent`` is not a ``NetBoxModel`` (no journal, no
  custom fields, no tags). Read-only by design.
"""

from __future__ import annotations

from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from ..models import ConstraintSnippet, PermissionAuditEvent


class ConstraintSnippetSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_permissions_plugin-api:constraintsnippet-detail",
    )

    class Meta:
        model = ConstraintSnippet
        fields = (
            "id",
            "url",
            "display",
            "name",
            "description",
            "body",
            "object_types",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name")


class PermissionAuditEventSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    target_type = serializers.StringRelatedField()

    class Meta:
        model = PermissionAuditEvent
        fields = (
            "id",
            "timestamp",
            "user",
            "action",
            "target_type",
            "target_id",
            "payload",
            "ip_address",
        )
        read_only_fields = fields  # immutable log
