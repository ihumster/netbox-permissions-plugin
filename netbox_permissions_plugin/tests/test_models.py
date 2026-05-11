"""Tests for the plugin's own models.

These tests require migrations to have been applied -- run
``python manage.py migrate`` against the test DB before ``pytest``.
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from netbox_permissions_plugin.models import (
    ActionType,
    ConstraintSnippet,
    PermissionAuditEvent,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# ConstraintSnippet
# ---------------------------------------------------------------------------


def test_snippet_str():
    snippet = ConstraintSnippet.objects.create(name="dc1-only", body={"slug": "dc1"})
    assert str(snippet) == "dc1-only"


def test_snippet_get_absolute_url():
    snippet = ConstraintSnippet.objects.create(name="dc1-only", body={"slug": "dc1"})
    assert snippet.get_absolute_url().endswith(f"/{snippet.pk}/")


def test_snippet_clean_accepts_dict():
    s = ConstraintSnippet(name="x", body={"slug": "dc1"})
    s.full_clean()  # must not raise


def test_snippet_clean_accepts_list_of_dicts():
    s = ConstraintSnippet(name="x", body=[{"slug": "dc1"}, {"slug": "dc2"}])
    s.full_clean()


def test_snippet_clean_accepts_empty_list():
    """``[]`` is the NetBox idiom for "never matches" -- legal."""
    s = ConstraintSnippet(name="x", body=[])
    s.full_clean()


def test_snippet_clean_rejects_top_level_string():
    s = ConstraintSnippet(name="x", body="not-a-json-object")
    with pytest.raises(ValidationError) as exc:
        s.full_clean()
    assert "body" in exc.value.message_dict


def test_snippet_clean_rejects_list_with_non_dict_items():
    s = ConstraintSnippet(name="x", body=[{"slug": "dc1"}, "garbage"])
    with pytest.raises(ValidationError) as exc:
        s.full_clean()
    assert "body" in exc.value.message_dict


def test_snippet_object_types_optional(db):
    """An unrestricted snippet (no object_types) is valid."""
    from django.contrib.contenttypes.models import ContentType

    s = ConstraintSnippet.objects.create(name="any-ct", body={"slug": "x"})
    assert s.object_types.count() == 0

    site_ct = ContentType.objects.get(app_label="dcim", model="site")
    s.object_types.add(site_ct)
    assert s.object_types.count() == 1


# ---------------------------------------------------------------------------
# PermissionAuditEvent
# ---------------------------------------------------------------------------


def test_audit_event_created_with_minimal_fields(regular_user):
    ev = PermissionAuditEvent.objects.create(
        user=regular_user,
        action=ActionType.VIEW_EFFECTIVE,
    )
    assert ev.pk is not None
    assert ev.timestamp is not None
    assert ev.payload == {}


def test_audit_event_action_choices_cover_expected_set():
    """Sanity: the action enum has the codes we expect to emit later."""
    expected = {
        "view_effective",
        "view_reverse",
        "view_tester",
        "create_perm",
        "update_perm",
        "delete_perm",
        "create_snippet",
        "update_snippet",
        "delete_snippet",
        "dry_run",
    }
    assert {value for value, _ in ActionType.choices} == expected


def test_audit_event_str_with_user(regular_user):
    ev = PermissionAuditEvent.objects.create(
        user=regular_user,
        action=ActionType.VIEW_EFFECTIVE,
    )
    assert "alice" in str(ev)
    assert "view_effective" in str(ev)


def test_audit_event_str_without_user():
    ev = PermissionAuditEvent.objects.create(
        user=None,
        action=ActionType.DRY_RUN,
    )
    assert "<system>" in str(ev)


def test_audit_event_generic_target(regular_user, site_dc1, site_ct):
    """``target`` is a generic FK and can point at any model row."""
    ev = PermissionAuditEvent.objects.create(
        user=regular_user,
        action=ActionType.VIEW_REVERSE,
        target_type=site_ct,
        target_id=site_dc1.pk,
        payload={"action_filter": "view"},
    )
    assert ev.target == site_dc1
    assert ev.payload["action_filter"] == "view"


def test_audit_event_ordering_is_newest_first(regular_user):
    """Default ordering is ``-timestamp``."""
    PermissionAuditEvent.objects.create(user=regular_user, action=ActionType.VIEW_TESTER)
    PermissionAuditEvent.objects.create(user=regular_user, action=ActionType.VIEW_EFFECTIVE)
    pair = list(PermissionAuditEvent.objects.all()[:2])
    assert pair[0].timestamp >= pair[1].timestamp
