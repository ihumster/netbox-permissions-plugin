"""Tests for reverse_lookup."""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.resolver.reverse import reverse_lookup

pytestmark = pytest.mark.django_db


def test_unrestricted_perm_matches_any_object(regular_user, make_objectperm, site_dc1, site_ct):
    make_objectperm("all-sites-read", actions=["view"], users=[regular_user])
    rows = reverse_lookup(site_ct, site_dc1.pk)
    assert any(r.rule.permission_name == "all-sites-read" for r in rows)


def test_constraints_filter_by_slug(regular_user, make_objectperm, site_dc1, site_dc2, site_ct):
    make_objectperm(
        "dc1-only",
        actions=["view"],
        users=[regular_user],
        constraints={"slug": "dc1"},
    )
    rows_dc1 = reverse_lookup(site_ct, site_dc1.pk)
    rows_dc2 = reverse_lookup(site_ct, site_dc2.pk)
    assert any(r.rule.permission_name == "dc1-only" for r in rows_dc1)
    assert all(r.rule.permission_name != "dc1-only" for r in rows_dc2)


def test_or_constraints_match_either(regular_user, make_objectperm, site_dc1, site_dc2, site_ct):
    make_objectperm(
        "dc1-or-dc2",
        actions=["view"],
        users=[regular_user],
        constraints=[{"slug": "dc1"}, {"slug": "dc2"}],
    )
    for site in (site_dc1, site_dc2):
        rows = reverse_lookup(site_ct, site.pk)
        assert any(r.rule.permission_name == "dc1-or-dc2" for r in rows)


def test_never_match_constraints_are_skipped(regular_user, make_objectperm, site_dc1, site_ct):
    make_objectperm(
        "blocked",
        actions=["view"],
        users=[regular_user],
        constraints=[],  # NetBox idiom for "never matches"
    )
    rows = reverse_lookup(site_ct, site_dc1.pk)
    assert all(r.rule.permission_name != "blocked" for r in rows)


def test_action_filter(regular_user, make_objectperm, site_dc1, site_ct):
    make_objectperm("read-only", actions=["view"], users=[regular_user])
    make_objectperm("write", actions=["change"], users=[regular_user])
    rows_view = reverse_lookup(site_ct, site_dc1.pk, action="view")
    rows_change = reverse_lookup(site_ct, site_dc1.pk, action="change")
    assert any(r.rule.permission_name == "read-only" for r in rows_view)
    assert all(r.rule.permission_name != "write" for r in rows_view)
    assert any(r.rule.permission_name == "write" for r in rows_change)


def test_superuser_appears_in_results(superuser, site_dc1, site_ct):
    rows = reverse_lookup(site_ct, site_dc1.pk)
    superuser_rows = [r for r in rows if r.rule.permission_name == "<superuser>"]
    assert len(superuser_rows) == 1
    grantees = superuser_rows[0].grantees
    assert any(g.label == "root" for g in grantees)
