"""REST API viewsets for the plugin's models.

``NetBoxModelViewSet`` gives us full CRUD + bulk + filterset + brief
representation handling for ``ConstraintSnippet``. ``PermissionAuditEvent``
gets a ``ReadOnlyModelViewSet`` because the log is append-only.
"""

from __future__ import annotations

from netbox.api.viewsets import NetBoxModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet

from ..filtersets import ConstraintSnippetFilterSet, PermissionAuditEventFilterSet
from ..models import ConstraintSnippet, PermissionAuditEvent
from .serializers import ConstraintSnippetSerializer, PermissionAuditEventSerializer


class ConstraintSnippetViewSet(NetBoxModelViewSet):
    queryset = ConstraintSnippet.objects.prefetch_related("object_types", "tags")
    serializer_class = ConstraintSnippetSerializer
    filterset_class = ConstraintSnippetFilterSet


class PermissionAuditEventViewSet(ReadOnlyModelViewSet):
    queryset = PermissionAuditEvent.objects.select_related("user", "target_type")
    serializer_class = PermissionAuditEventSerializer
    filterset_class = PermissionAuditEventFilterSet
