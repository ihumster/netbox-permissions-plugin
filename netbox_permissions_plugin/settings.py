"""Доступ к настройкам плагина с правильными дефолтами.

NetBox кладёт настройки плагина в settings.PLUGINS_CONFIG[<plugin_name>].
Любое чтение настроек должно идти через эти хелперы, чтобы:
1. дефолты были в одном месте;
2. mypy/IDE имели подсказки;
3. тесты могли подменять конкретные ключи через @override_settings.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

PLUGIN_NAME = "netbox_permissions_plugin"

_DEFAULTS: dict[str, Any] = {
    "external_groups": [],
    "membership_providers": [
        "netbox_permissions_plugin.resolver.membership.DjangoMembershipProvider",
    ],
    "preview_sample_size": 25,
}


def get(key: str) -> Any:
    """Вернуть значение настройки плагина с применением дефолта."""
    cfg = getattr(settings, "PLUGINS_CONFIG", {}).get(PLUGIN_NAME, {})
    if key in cfg:
        return cfg[key]
    if key in _DEFAULTS:
        return _DEFAULTS[key]
    raise KeyError(f"Unknown plugin setting: {key!r}")


def external_groups() -> list[str]:
    return list(get("external_groups"))


def preview_sample_size() -> int:
    return int(get("preview_sample_size"))


def membership_provider_paths() -> list[str]:
    return list(get("membership_providers"))
