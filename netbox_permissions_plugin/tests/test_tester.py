"""Tests for explain (Permission tester)."""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.resolver import explain
from netbox_permissions_plugin.resolver.types import DenyReason


pytestmark = pytest.mark.django_db


def test_inactive_user_denied_with_reason(inactive_user, site_dc1, site_ct):
    res = explain(inactive_user, site_ct, site_dc1.pk, "view")
    assert res.allowed is False
    assert res.deny_reason == DenyReason.INACTIVE


def test_superuser_always_allowed(superuser, site_dc1, site_ct):
    res = explain(superuser, site_ct, site_dc1.pk, "delete")
    assert res.allowed is True


def test_no_perm_for_action(regular_user, make_objectperm, site_dc1, site_ct):
    make_objectperm("only-view", actions=["view"], users=[regular_user])
    res = explain(regular_user, site_ct, site_dc1.pk, "delete")
    assert res.allowed is False
    assert res.deny_reason == DenyReason.NO_OBJECT_PERM


def test_constraints_match_allows(regular_user, make_objectperm, site_dc1, site_ct):
    make_objectperm(
        "dc1-write",
        actions=["change"],
        users=[regular_user],
        constraints={"slug": "dc1"},
    )
    res = explain(regular_user, site_ct, site_dc1.pk, "change")
    assert res.allowed is True
    assert any(r.permission_name == "dc1-write" for r in res.matched_rules)


def test_constraints_dont_match_denies_with_reason(
    regular_user, make_objectperm, site_dc1, site_dc2, site_ct
):
    make_objectperm(
        "dc1-only",
        actions=["change"],
        users=[regular_user],
        constraints={"slug": "dc1"},
    )
    res = explain(regular_user, site_ct, site_dc2.pk, "change")
    assert res.allowed is False
    assert res.deny_reason == DenyReason.CONSTRAINTS_NOT_MATCHED
    # Candidates are returned in matched_rules for debugging.
    assert any(r.permission_name == "dc1-only" for r in res.matched_rules)


def test_custom_action_run(regular_user, make_objectperm, db):
    """Custom action ``run`` (NetBox script execution) flows the same way as standard ones."""
    from django.contrib.contenttypes.models import ContentType
    # Use dcim.site as a neutral target -- we just verify the action string is
    # serialized into the actions JSONField and matched as expected.
    site_ct = ContentType.objects.get(app_label="dcim", model="site")
    from dcim.models import Site

    site = Site.objects.create(name="X", slug="x")
    make_objectperm("can-run", actions=["run"], users=[regular_user])
    res = explain(regular_user, site_ct, site.pk, "run")
    assert res.allowed is True
