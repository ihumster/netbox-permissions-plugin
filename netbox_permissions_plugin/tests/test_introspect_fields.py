"""Tests for the field introspection layer.

Covers:

* native ORM fields land with correct ``FieldType``;
* FK / M2M fields carry a dotted ``fk_target``;
* fields with ``choices`` collapse to SELECT, choices normalized to str pairs;
* hidden fields (``id``, timestamps, ``custom_field_data``) are filtered;
* ``extras.CustomField`` rows surface as ``CF_*`` descriptors, with the
  correct lookup name prefix and CF-type mapping.
"""

from __future__ import annotations

import pytest

from netbox_permissions_plugin.introspection.fields import list_fields
from netbox_permissions_plugin.introspection.types import FieldType

pytestmark = pytest.mark.django_db


# --- Native field discovery -------------------------------------------------


def test_native_text_field(site_ct):
    fields = list_fields(site_ct)
    by_name = {f.name: f for f in fields}
    name_field = by_name["name"]
    # ``name`` on Site is a CharField -- should land as TEXT.
    assert name_field.type == FieldType.TEXT
    assert name_field.is_custom_field is False
    assert "icontains" in name_field.lookups


def test_native_slug_field_is_text(site_ct):
    fields = {f.name: f for f in list_fields(site_ct)}
    assert fields["slug"].type == FieldType.TEXT


def test_native_select_field_collapses_to_choices(site_ct):
    """Site.status has choices => SELECT, with non-empty choices tuple."""
    fields = {f.name: f for f in list_fields(site_ct)}
    status = fields["status"]
    assert status.type == FieldType.SELECT
    assert status.choices is not None
    assert len(status.choices) > 0
    # All choice values normalized to str.
    assert all(isinstance(v, str) and isinstance(label, str) for v, label in status.choices)


def test_hidden_fields_are_filtered(site_ct):
    names = {f.name for f in list_fields(site_ct)}
    assert "id" not in names
    assert "created" not in names
    assert "last_updated" not in names
    assert "custom_field_data" not in names


def test_fk_field_carries_target_label(db):
    """Device.site is a FK to dcim.Site -- target label must be ``dcim.site``."""
    from django.contrib.contenttypes.models import ContentType

    device_ct = ContentType.objects.get(app_label="dcim", model="device")
    fields = {f.name: f for f in list_fields(device_ct)}
    site = fields["site"]
    assert site.type == FieldType.FK
    assert site.fk_target == "dcim.site"


def test_m2m_field_carries_target_label(db):
    """Device.tags is M2M to extras.Tag -- target ``extras.tag``."""
    from django.contrib.contenttypes.models import ContentType

    device_ct = ContentType.objects.get(app_label="dcim", model="device")
    fields = {f.name: f for f in list_fields(device_ct)}
    if "tags" not in fields:
        pytest.skip("Device.tags not present in this NetBox version")
    tags = fields["tags"]
    assert tags.type == FieldType.M2M
    assert tags.fk_target == "extras.tag"


def test_unknown_content_type_returns_empty(db):
    from django.contrib.contenttypes.models import ContentType

    # ``contenttype`` itself has no plugin-relevant model_class quirks,
    # but a CT for a non-registered app_label/model_name yields None.
    ct = ContentType(app_label="nonexistent", model="ghost")
    assert list_fields(ct) == ()


# --- Custom field discovery -------------------------------------------------


@pytest.fixture
def cf_text_for_site(db, site_ct):
    """Create a text-type CustomField on dcim.Site for the test below."""
    from extras.models import CustomField

    cf = CustomField.objects.create(
        name="owner_team",
        label="Owner team",
        type="text",
    )
    cf.object_types.set([site_ct])
    return cf


def test_custom_text_field_is_discovered(cf_text_for_site, site_ct):
    fields = {f.name: f for f in list_fields(site_ct)}
    cf_name = "custom_field_data__owner_team"
    assert cf_name in fields
    cf = fields[cf_name]
    assert cf.is_custom_field is True
    assert cf.type == FieldType.CF_TEXT
    assert cf.label.startswith("Owner team")
    assert "icontains" in cf.lookups


def test_custom_field_not_attached_is_skipped(db):
    """CFs not assigned to the target CT must not leak in."""
    from django.contrib.contenttypes.models import ContentType
    from extras.models import CustomField

    rack_ct = ContentType.objects.get(app_label="dcim", model="rack")
    site_ct = ContentType.objects.get(app_label="dcim", model="site")
    cf = CustomField.objects.create(name="rack_only_cf", label="Rack-only", type="text")
    cf.object_types.set([rack_ct])  # attached to Rack only

    site_fields = {f.name for f in list_fields(site_ct)}
    assert "custom_field_data__rack_only_cf" not in site_fields
