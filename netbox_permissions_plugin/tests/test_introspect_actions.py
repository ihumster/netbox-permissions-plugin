"""Tests for the action introspection layer."""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.introspection.actions import list_actions_for_cts

pytestmark = pytest.mark.django_db


def test_standard_actions_always_present(site_ct):
    actions = list_actions_for_cts([site_ct])
    for name in ("view", "add", "change", "delete"):
        assert name in actions
        assert actions[name].is_standard is True
        assert actions[name].applicable_cts == ("*",)
        assert actions[name].source == "django.builtin"


def test_standard_actions_apply_to_any_ct(site_ct):
    actions = list_actions_for_cts([site_ct])
    assert actions["view"].applies_to("dcim.site")
    assert actions["view"].applies_to("ipam.prefix")


def test_run_action_for_script_ct(db):
    from django.contrib.contenttypes.models import ContentType

    script_ct = ContentType.objects.get(app_label="extras", model="script")
    actions = list_actions_for_cts([script_ct])
    assert "run" in actions
    run = actions["run"]
    assert run.is_standard is False
    assert run.applicable_cts == ("extras.script",)
    assert run.source == "extras.Script"


def test_run_action_absent_for_unrelated_ct(site_ct):
    actions = list_actions_for_cts([site_ct])
    assert "run" not in actions


def test_mixed_ct_set_emits_run_only_once(db, site_ct):
    """When Script is one of several CTs, ``run`` should appear once."""
    from django.contrib.contenttypes.models import ContentType

    script_ct = ContentType.objects.get(app_label="extras", model="script")
    actions = list_actions_for_cts([site_ct, script_ct])
    # Only one entry in the result dict regardless of how many CTs match.
    assert "run" in actions
    assert actions["run"].applicable_cts == ("extras.script",)


def test_empty_ct_set_still_has_standard_actions():
    """Standard CRUD must surface even with an empty CT iterable."""
    actions = list_actions_for_cts([])
    assert set(actions.keys()) == {"view", "add", "change", "delete"}


def test_applies_to_universal():
    """ActionDescriptor.applies_to returns True for ``*``-applicable actions
    regardless of CT label.
    """
    actions = list_actions_for_cts([])
    assert actions["view"].applies_to("anything.at.all")
