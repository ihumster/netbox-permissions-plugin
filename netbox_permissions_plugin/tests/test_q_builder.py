"""Tests for constraints -> Q serialization.

This test does NOT need the DB or any Django models; it runs fast.
"""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.resolver._q import NeverMatch, constraints_to_q


def test_none_constraints_means_unrestricted():
    q = constraints_to_q(None)
    assert q.children == []


def test_empty_dict_is_unrestricted():
    q = constraints_to_q({})
    assert q.children == []


def test_dict_constraints_become_and():
    q = constraints_to_q({"slug": "dc1", "tenant_id": 5})
    assert q.connector == "AND"
    assert ("slug", "dc1") in q.children
    assert ("tenant_id", 5) in q.children


def test_list_constraints_become_or():
    q = constraints_to_q([{"slug": "dc1"}, {"slug": "dc2"}])
    assert q.connector == "OR"


def test_empty_list_means_never():
    with pytest.raises(NeverMatch):
        constraints_to_q([])


def test_non_dict_chunks_are_skipped_safely():
    q = constraints_to_q([{"slug": "dc1"}, "garbage", {"slug": "dc2"}])  # type: ignore[list-item]
    # "Garbage" chunks must be ignored without making the rule overly permissive.
    assert q.connector == "OR"
