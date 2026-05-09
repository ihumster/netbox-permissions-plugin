"""Resolver -- the audit core.

This package knows nothing about HTTP, forms, or templates: only Python and
the Django ORM. Keeping it pure lets unit tests run fast without touching the
view layer.

Note: this ``__init__.py`` intentionally does NOT re-export submodules.
Some of them (``reverse``, ``tester``, ``effective``) import Django models
(e.g. ``ContentType``) at module level, which fails to import when the Django
apps registry is not initialized -- e.g. during the resolver-only test slice
that runs without NetBox. Import directly from submodules instead:

    from netbox_permissions_plugin.resolver.effective import compute_effective
    from netbox_permissions_plugin.resolver.reverse import reverse_lookup
    from netbox_permissions_plugin.resolver.tester import explain
    from netbox_permissions_plugin.resolver.types import ResolvedRule, ...
"""
