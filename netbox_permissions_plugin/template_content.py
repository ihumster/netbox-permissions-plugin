"""PluginTemplateExtension registry.

Empty in stage 1: the per-object "Permissions" view is now a proper detail
tab registered via ``register_model_view`` in ``views/object_tab.py`` rather
than a side card injected via ``right_page()``. Keep this module so NetBox's
extension auto-discovery does not log a missing-module warning, and so we
have a place to add small UI tweaks (buttons, banners) in later stages.
"""

from __future__ import annotations

template_extensions: list = []
