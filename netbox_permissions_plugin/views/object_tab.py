"""Per-model "Permissions" tab on object detail pages.

Replaces the legacy ``PluginTemplateExtension.right_page()`` card. Uses
NetBox 4.x ``register_model_view`` so each target model gets a proper tab
next to "Main", "Comments", "Changelog", "Journal".

Loaded eagerly from ``PluginConfig.ready()`` so the decorators register at
app startup.

Tab visibility is currently gated by the standard ``users.view_objectpermission``
Django permission. In a later stage we will introduce a dedicated
``view_effective_permissions`` codename on the plugin and switch to it.
"""

from __future__ import annotations

from circuits.models import Circuit
from dcim.models import Device, Rack, Site
from django.contrib.contenttypes.models import ContentType
from extras.models import Script
from ipam.models import IPAddress, Prefix
from netbox.views.generic import ObjectView
from tenancy.models import Tenant
from utilities.views import ViewTab, register_model_view
from virtualization.models import VirtualMachine

from ..resolver.reverse import reverse_lookup


class _PermissionsTabBase(ObjectView):
    """Common implementation for the per-model Permissions tab."""

    template_name = "netbox_permissions_plugin/object_permissions_tab.html"
    tab = ViewTab(
        label="Permissions",
        permission="users.view_objectpermission",
    )

    def get_extra_context(self, request, instance):
        ct = ContentType.objects.get_for_model(instance.__class__)
        return {"perm_rows": reverse_lookup(ct, instance.pk)}


# Concrete subclasses needed because register_model_view binds the queryset
# to a specific model. The class body itself is uniform via _PermissionsTabBase.
@register_model_view(Device, name="permissions", path="permissions")
class DevicePermissionsView(_PermissionsTabBase):
    queryset = Device.objects.all()


@register_model_view(Site, name="permissions", path="permissions")
class SitePermissionsView(_PermissionsTabBase):
    queryset = Site.objects.all()


@register_model_view(Rack, name="permissions", path="permissions")
class RackPermissionsView(_PermissionsTabBase):
    queryset = Rack.objects.all()


@register_model_view(Prefix, name="permissions", path="permissions")
class PrefixPermissionsView(_PermissionsTabBase):
    queryset = Prefix.objects.all()


@register_model_view(IPAddress, name="permissions", path="permissions")
class IPAddressPermissionsView(_PermissionsTabBase):
    queryset = IPAddress.objects.all()


@register_model_view(Tenant, name="permissions", path="permissions")
class TenantPermissionsView(_PermissionsTabBase):
    queryset = Tenant.objects.all()


@register_model_view(VirtualMachine, name="permissions", path="permissions")
class VirtualMachinePermissionsView(_PermissionsTabBase):
    queryset = VirtualMachine.objects.all()


@register_model_view(Circuit, name="permissions", path="permissions")
class CircuitPermissionsView(_PermissionsTabBase):
    queryset = Circuit.objects.all()


@register_model_view(Script, name="permissions", path="permissions")
class ScriptPermissionsView(_PermissionsTabBase):
    queryset = Script.objects.all()
