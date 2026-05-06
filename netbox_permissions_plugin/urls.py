"""Plugin URL configuration.

The ``/plugins/permissions/`` prefix is added automatically by NetBox from
``PluginConfig.base_url``.
"""

from __future__ import annotations

from django.urls import path

from .views import effective, reverse_lookup, tester

app_name = "netbox_permissions_plugin"

urlpatterns = [
    path("", effective.EffectivePermissionsView.as_view(), name="effective"),
    path("effective/", effective.EffectivePermissionsView.as_view(), name="effective_alias"),
    path("reverse/", reverse_lookup.ReverseLookupView.as_view(), name="reverse"),
    path("tester/", tester.TesterView.as_view(), name="tester"),
]
