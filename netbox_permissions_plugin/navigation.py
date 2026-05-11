"""NetBox sidebar navigation.

Two groups under one top-level menu:

* ``Audit`` -- the three read-only stage-1 pages;
* ``Stage 2`` -- the writeable / management pages introduced in stage 2.
"""

from __future__ import annotations

from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

_audit_items = (
    PluginMenuItem(
        link="plugins:netbox_permissions_plugin:effective",
        link_text="Effective permissions",
        permissions=["users.view_objectpermission"],
    ),
    PluginMenuItem(
        link="plugins:netbox_permissions_plugin:reverse",
        link_text="Reverse lookup",
        permissions=["users.view_objectpermission"],
    ),
    PluginMenuItem(
        link="plugins:netbox_permissions_plugin:tester",
        link_text="Permission tester",
        permissions=["users.view_objectpermission"],
    ),
)

_stage2_items = (
    PluginMenuItem(
        link="plugins:netbox_permissions_plugin:constraintsnippet_list",
        link_text="Constraint snippets",
        permissions=["netbox_permissions_plugin.view_constraintsnippet"],
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_permissions_plugin:constraintsnippet_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                permissions=["netbox_permissions_plugin.add_constraintsnippet"],
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:netbox_permissions_plugin:permissionauditevent_list",
        link_text="Audit events",
        permissions=["netbox_permissions_plugin.view_auditevent"],
    ),
)

menu = PluginMenu(
    label="Permissions Audit",
    groups=(
        ("Audit", _audit_items),
        ("Stage 2", _stage2_items),
    ),
    icon_class="mdi mdi-shield-account",
)
