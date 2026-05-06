"""Plugin settings access with default values.

NetBox stores plugin settings under ``settings.PLUGINS_CONFIG[<plugin_name>]``.
Reading those settings should always go through the helpers below so that:

1. defaults live in one place;
2. mypy / IDE get type hints;
3. tests can override single keys via ``@override_settings``.
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
    """Return a plugin setting, falling back to the registered default."""
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
