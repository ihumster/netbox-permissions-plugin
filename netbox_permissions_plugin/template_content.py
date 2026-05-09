"""PluginTemplateExtension -- adds a "Permissions" tab on the detail page of any
NetBox object with the reverse_lookup table.

Discovered via ``template_extensions`` in PluginConfig.
In stage 1 we render the reverse_lookup result without an action filter so the
full access list is visible at a glance.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension

from .resolver.reverse import reverse_lookup


class _ObjectPermissionsTab(PluginTemplateExtension):
    """Base class -- concrete subclasses set the ``models`` attribute."""

    def right_page(self):
        obj = self.context["object"]
        ct = ContentType.objects.get_for_model(obj.__class__)
        rows = reverse_lookup(ct, obj.pk)
        return self.render(
            "netbox_permissions_plugin/_object_tab.html",
            extra_context={"perm_rows": rows},
        )


# Models that get the tab. Extend as needed; for the MVP we cover the most
# frequently audited ones. Could also be looped over all NetBoxModel subclasses.
_TARGETS = [
    "dcim.device",
    "dcim.site",
    "dcim.rack",
    "ipam.prefix",
    "ipam.ipaddress",
    "tenancy.tenant",
    "virtualization.virtualmachine",
    "circuits.circuit",
    "extras.script",
]


def _make_extensions() -> list[type[PluginTemplateExtension]]:
    extensions: list[type[PluginTemplateExtension]] = []
    for label in _TARGETS:
        cls = type(
            f"PermissionsTab__{label.replace('.', '_')}",
            (_ObjectPermissionsTab,),
            {"models": [label]},
        )
        extensions.append(cls)
    return extensions


template_extensions = _make_extensions()
