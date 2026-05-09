"""Tests for compute_effective."""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.resolver.effective import compute_effective
from netbox_permissions_plugin.resolver.types import RuleSource

pytestmark = pytest.mark.django_db


def test_inactive_user_gets_empty_rules(inactive_user):
    eff = compute_effective(inactive_user)
    assert eff.is_active is False
    assert eff.rules == ()


def test_superuser_gets_synthetic_rule(superuser):
    eff = compute_effective(superuser)
    assert eff.is_superuser is True
    assert len(eff.rules) == 1
    assert eff.rules[0].source == RuleSource.SUPERUSER
    assert eff.rules[0].constraints is None


def test_direct_assignment(regular_user, make_objectperm):
    make_objectperm("read-all-sites", actions=["view"], users=[regular_user])
    eff = compute_effective(regular_user)
    assert len(eff.rules) == 1
    r = eff.rules[0]
    assert r.source == RuleSource.DIRECT
    assert r.actions == ("view",)
    assert r.permission_name == "read-all-sites"
    assert r.object_type_label == "dcim.site"


def test_assignment_via_group(regular_user, group_a, make_objectperm):
    regular_user.groups.add(group_a)
    make_objectperm("dc-engineers-write", actions=["view", "change"], groups=[group_a])
    eff = compute_effective(regular_user)
    assert len(eff.rules) == 1
    r = eff.rules[0]
    assert r.source == RuleSource.GROUP
    assert r.via_group is not None
    assert r.via_group.group_name == "dc-engineers"


def test_same_perm_direct_and_via_group_emits_both(regular_user, group_a, make_objectperm):
    regular_user.groups.add(group_a)
    make_objectperm(
        "noc-readonly",
        actions=["view"],
        users=[regular_user],
        groups=[group_a],
    )
    eff = compute_effective(regular_user)
    sources = sorted(r.source.value for r in eff.rules)
    assert sources == ["direct", "group"]


def test_disabled_perm_is_filtered_out(regular_user, make_objectperm):
    make_objectperm("disabled", actions=["view"], users=[regular_user], enabled=False)
    eff = compute_effective(regular_user)
    assert eff.rules == ()


def test_multiple_content_types_expand_to_multiple_rules(regular_user, make_objectperm, db):
    from django.contrib.contenttypes.models import ContentType

    site_ct = ContentType.objects.get(app_label="dcim", model="site")
    rack_ct = ContentType.objects.get(app_label="dcim", model="rack")
    make_objectperm(
        "site-and-rack",
        actions=["view"],
        users=[regular_user],
        content_types=[site_ct, rack_ct],
    )
    eff = compute_effective(regular_user)
    labels = sorted(r.object_type_label for r in eff.rules)
    assert labels == ["dcim.rack", "dcim.site"]
