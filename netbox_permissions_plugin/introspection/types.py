"""DTOs returned by the introspection layer.

All types are frozen dataclasses and enums so they serialize cleanly and
can be compared in tests.

Field types are split into "native" (for ORM fields) and ``CF_*`` (for
``extras.CustomField`` rows). The builder UI uses the prefix to decide
where to source values and which lookup operators to offer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class FieldType(StrEnum):
    """Logical type of a field, used to drive the builder UI widget choice."""

    # Native ORM field types.
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    URL = "url"
    JSON = "json"
    FK = "fk"  # ForeignKey / OneToOneField
    M2M = "m2m"  # ManyToManyField
    SELECT = "select"  # field.choices is non-empty
    MULTISELECT = "multiselect"  # rare in stock NetBox, kept for symmetry

    # Custom-field counterparts. The wire-format names match
    # `extras.CustomField.type` plus the ``cf_`` prefix.
    CF_TEXT = "cf_text"
    CF_LONGTEXT = "cf_longtext"
    CF_INTEGER = "cf_integer"
    CF_DECIMAL = "cf_decimal"
    CF_BOOLEAN = "cf_boolean"
    CF_DATE = "cf_date"
    CF_DATETIME = "cf_datetime"
    CF_URL = "cf_url"
    CF_JSON = "cf_json"
    CF_SELECT = "cf_select"
    CF_MULTISELECT = "cf_multiselect"
    CF_OBJECT = "cf_object"
    CF_MULTIOBJECT = "cf_multiobject"


# Default Django ORM lookups per logical type. The builder UI uses these as
# the operator dropdown; entries are advisory, not enforced -- a constraint
# writer can still hand-craft any lookup that Django supports.
_LOOKUPS_TEXT = (
    "exact",
    "iexact",
    "contains",
    "icontains",
    "startswith",
    "endswith",
    "regex",
    "isnull",
)
_LOOKUPS_NUMBER = ("exact", "gt", "gte", "lt", "lte", "in", "isnull")
_LOOKUPS_DATETIME = ("exact", "gt", "gte", "lt", "lte", "isnull", "range")
_LOOKUPS_BOOLEAN = ("exact", "isnull")
_LOOKUPS_FK = ("exact", "in", "isnull")
_LOOKUPS_M2M = ("contains", "in", "isnull")
_LOOKUPS_SELECT = ("exact", "in", "isnull")
_LOOKUPS_MULTISELECT = ("contains", "isnull")
_LOOKUPS_JSON = ("exact", "isnull")
_LOOKUPS_URL = _LOOKUPS_TEXT


_DEFAULT_LOOKUPS: dict[FieldType, tuple[str, ...]] = {
    FieldType.TEXT: _LOOKUPS_TEXT,
    FieldType.INTEGER: _LOOKUPS_NUMBER,
    FieldType.DECIMAL: _LOOKUPS_NUMBER,
    FieldType.BOOLEAN: _LOOKUPS_BOOLEAN,
    FieldType.DATE: _LOOKUPS_DATETIME,
    FieldType.DATETIME: _LOOKUPS_DATETIME,
    FieldType.URL: _LOOKUPS_URL,
    FieldType.JSON: _LOOKUPS_JSON,
    FieldType.FK: _LOOKUPS_FK,
    FieldType.M2M: _LOOKUPS_M2M,
    FieldType.SELECT: _LOOKUPS_SELECT,
    FieldType.MULTISELECT: _LOOKUPS_MULTISELECT,
    # Custom fields reuse the same lookup sets as their native counterparts.
    FieldType.CF_TEXT: _LOOKUPS_TEXT,
    FieldType.CF_LONGTEXT: _LOOKUPS_TEXT,
    FieldType.CF_INTEGER: _LOOKUPS_NUMBER,
    FieldType.CF_DECIMAL: _LOOKUPS_NUMBER,
    FieldType.CF_BOOLEAN: _LOOKUPS_BOOLEAN,
    FieldType.CF_DATE: _LOOKUPS_DATETIME,
    FieldType.CF_DATETIME: _LOOKUPS_DATETIME,
    FieldType.CF_URL: _LOOKUPS_URL,
    FieldType.CF_JSON: _LOOKUPS_JSON,
    FieldType.CF_SELECT: _LOOKUPS_SELECT,
    FieldType.CF_MULTISELECT: _LOOKUPS_MULTISELECT,
    FieldType.CF_OBJECT: _LOOKUPS_FK,
    FieldType.CF_MULTIOBJECT: _LOOKUPS_M2M,
}


def default_lookups_for(type_: FieldType) -> tuple[str, ...]:
    """Public helper -- builder UI uses this for the operator dropdown."""
    return _DEFAULT_LOOKUPS.get(type_, ())


@dataclass(frozen=True)
class FieldDescriptor:
    """A field that can appear in an ObjectPermission constraint.

    ``name`` is the ORM lookup prefix as used in ``Q(**{name: value})``:

    * for native fields it equals the Django field name (e.g. ``"slug"``);
    * for FK fields it is the field name -- NOT ``"<name>_id"`` -- so that
      ``{"site": <id>}`` matches NetBox-style constraints;
    * for custom fields it is ``"custom_field_data__<cf_name>"``.

    ``label`` is the human-readable verbose name.

    ``fk_target`` is the dotted CT label (``"app.model"``) of the related
    model for FK / M2M / CF_OBJECT / CF_MULTIOBJECT, otherwise ``None``.
    """

    name: str
    label: str
    type: FieldType
    is_custom_field: bool = False
    choices: tuple[tuple[str, str], ...] | None = None
    fk_target: str | None = None
    lookups: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ActionDescriptor:
    """An action that can appear in ObjectPermission.actions.

    ``applicable_cts`` is a tuple of dotted CT labels (``"app.model"``) where
    the action makes sense. A single-element tuple ``("*",)`` means the
    action applies to any CT (true for the standard CRUD four).
    """

    name: str
    label: str
    is_standard: bool
    applicable_cts: tuple[str, ...]
    source: str

    def applies_to(self, ct_label: str) -> bool:
        if self.applicable_cts == ("*",):
            return True
        return ct_label in self.applicable_cts
