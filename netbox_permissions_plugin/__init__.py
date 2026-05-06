"""NetBox Permissions Plugin.

MVP, этап 1 — read-only аудит:

* «Effective permissions for user/group» — что реально может пользователь.
* «Reverse lookup by object» — кто имеет доступ к конкретному объекту.
* «Tester» — единичная проверка allow/deny с трассой.

Запись (CRUD ObjectPermission, constraint builder) — в этапе 2.
"""

from __future__ import annotations

from netbox.plugins import PluginConfig

__version__ = "0.1.0"


class NetBoxPermissionsPluginConfig(PluginConfig):
    name = "netbox_permissions_plugin"
    verbose_name = "Permissions Audit"
    description = (
        "Аудит эффективных прав в NetBox: что может пользователь, "
        "кто имеет доступ к объекту, единичная проверка allow/deny."
    )
    version = __version__
    author = "Alexander"
    author_email = "padla2k@gmail.com"
    base_url = "permissions"
    min_version = "4.4.0"
    required_settings = []
    default_settings = {
        # Список имён групп, которые управляются внешним IdP и которые плагин
        # помечает в UI как «managed externally». Записать в них из плагина
        # будет нельзя (актуально для этапа 2).
        "external_groups": [],
        # Имя backend-класса MembershipProvider; точка кастомизации для
        # источников членства типа SAML/OIDC claims.
        "membership_providers": [
            "netbox_permissions_plugin.resolver.membership.DjangoMembershipProvider",
        ],
        # Сколько объектов показывать в превью при reverse-lookup.
        "preview_sample_size": 25,
    }


config = NetBoxPermissionsPluginConfig
