"""URL routing for the plugin's REST API.

NetBox auto-discovers ``netbox_permissions_plugin.api.urls.urlpatterns`` and
mounts it under ``/api/plugins/permissions/`` (the plugin's ``base_url``).

Route names are ``constraintsnippet-list``, ``constraintsnippet-detail``,
etc., reachable via
``plugins-api:netbox_permissions_plugin-api:constraintsnippet-detail``.
"""

from __future__ import annotations

from netbox.api.routers import NetBoxRouter

from .views import ConstraintSnippetViewSet, PermissionAuditEventViewSet

app_name = "netbox_permissions_plugin-api"

router = NetBoxRouter()
router.register("constraint-snippets", ConstraintSnippetViewSet)
router.register("audit-events", PermissionAuditEventViewSet)

urlpatterns = router.urls
