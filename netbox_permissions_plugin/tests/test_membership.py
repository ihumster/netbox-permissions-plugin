"""Tests for MembershipProvider."""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.resolver.membership import (
    DjangoMembershipProvider,
    collect_memberships,
)
from netbox_permissions_plugin.resolver.types import MembershipSource

pytestmark = pytest.mark.django_db


def test_django_provider_returns_local_for_user_groups(regular_user, group_a, group_b):
    regular_user.groups.add(group_a, group_b)
    provider = DjangoMembershipProvider()
    out = sorted(provider.memberships(regular_user), key=lambda m: m.group_name)
    assert [m.group_name for m in out] == ["dc-engineers", "noc-readonly"]
    assert all(m.source == MembershipSource.LOCAL for m in out)


def test_collect_memberships_dedupes_by_group_id(regular_user, group_a, settings):
    regular_user.groups.add(group_a)
    settings.PLUGINS_CONFIG = {
        "netbox_permissions_plugin": {
            "membership_providers": [
                "netbox_permissions_plugin.resolver.membership.DjangoMembershipProvider",
                "netbox_permissions_plugin.resolver.membership.DjangoMembershipProvider",
            ]
        }
    }
    out = collect_memberships(regular_user)
    assert len(out) == 1
    assert out[0].group_name == "dc-engineers"


def test_collect_memberships_for_user_without_groups(regular_user):
    out = collect_memberships(regular_user)
    assert out == ()
