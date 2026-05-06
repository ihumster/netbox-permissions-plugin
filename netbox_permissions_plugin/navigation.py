"""Боковая навигация NetBox.

Регистрируем три пункта меню в собственной группе «Permissions Audit».
"""

from __future__ import annotations

from netbox.plugins import PluginMenu, PluginMenuItem

_items = (
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

menu = PluginMenu(
    label="Permissions Audit",
    groups=(("Audit", _items),),
    icon_class="mdi mdi-shield-account",
)
