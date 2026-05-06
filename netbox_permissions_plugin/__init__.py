"""NetBox Permissions Plugin.

MVP, stage 1 — read-only audit:

* "Effective permissions for user/group" — what the user actually can do.
* "Reverse lookup by object" — who has access to a specific object.
* "Tester" — single allow/deny check with a trace of matched rules.

Write features (CRUD ObjectPermission, constraint builder) are planned for stage 2.
"""

from __future__ import annotations

from netbox.plugins import PluginConfig

__version__ = "0.1.0"


class NetBoxPermissionsPluginConfig(PluginConfig):
    name = "netbox_permissions_plugin"
    verbose_name = "Permissions Audit"
    description = (
        "Audit of effective permissions in NetBox: what a user can do, "
        "who has access to an object, and a single allow/deny check."
    )
    version = __version__
    author = "Alexander"
    author_email = "ihumster@ihumster.ru"
    base_url = "permissions"
    min_version = "4.4.0"
    required_settings = []
    default_settings = {
        # Names of groups managed by the external IdP. The plugin marks them as
        # "managed externally" in the UI. In stage 2, write operations against
        # these groups will be blocked.
        "external_groups": [],
        # Dotted paths of MembershipProvider classes. This is the extension
        # point for SAML/OIDC group claim sources.
        "membership_providers": [
            "netbox_permissions_plugin.resolver.membership.DjangoMembershipProvider",
        ],
        # Number of objects shown in the reverse-lookup preview.
        "preview_sample_size": 25,
    }


config = NetBoxPermissionsPluginConfig
