"""Field discovery for the constraint builder.

``list_fields(content_type)`` returns the union of:

1. native ORM fields on the model (skipping reverse relations and internal
   bookkeeping like ``id``/``last_updated`` -- those are uninteresting to
   the builder UI);
2. custom fields registered against this CT in ``extras.CustomField``.

Custom field names are prefixed with ``custom_field_data__`` so the value
is a valid ORM lookup against the underlying ``custom_field_data`` JSONField.

Heavy imports (Django models, NetBox apps) are deferred so this module
can be imported without a configured Django apps registry. The functions
themselves do require Django to be ready -- they are called from views.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import FieldDescriptor, FieldType, default_lookups_for

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Field as DjangoField


# Names of Django model fields the builder UI should hide. They are either
# implementation noise (``id`` is implicit), values the user cannot mutate
# from a constraint, or NetBox-internal tracking that no one wants to
# filter on at the ObjectPermission level.
_HIDDEN_NATIVE_FIELDS = frozenset(
    {
        "id",
        "created",
        "last_updated",
        "custom_field_data",  # exposed via CF discovery below, not the raw JSON
    }
)


def list_fields(content_type: ContentType) -> tuple[FieldDescriptor, ...]:
    """Return descriptors for all builder-relevant fields on ``content_type``."""
    model = content_type.model_class()
    if model is None:
        return ()

    out: list[FieldDescriptor] = []
    out.extend(_native_fields(model))
    out.extend(_custom_fields(content_type))
    return tuple(out)


def _native_fields(model) -> list[FieldDescriptor]:
    """Iterate ``model._meta.get_fields()`` and translate to FieldDescriptor."""
    from django.db.models import (
        BooleanField,
        DateField,
        DateTimeField,
        DecimalField,
        FloatField,
        IntegerField,
        JSONField,
        URLField,
    )

    out: list[FieldDescriptor] = []
    for f in model._meta.get_fields():
        # Skip reverse relations (auto_created and remote): the builder
        # cannot use them in a constraint that targets THIS model's rows.
        if getattr(f, "auto_created", False) and not getattr(f, "concrete", False):
            continue
        if not getattr(f, "concrete", True):
            continue

        name = f.name
        if name in _HIDDEN_NATIVE_FIELDS:
            continue

        # ``choices`` overrides the base mapping: any field with a non-empty
        # ``choices`` is rendered as a SELECT regardless of underlying type.
        choices = getattr(f, "choices", None)
        if choices:
            out.append(_select_descriptor(f))
            continue

        # Relation fields. Use the many_to_many / many_to_one / one_to_one
        # flags rather than isinstance(ManyToManyField) so we correctly
        # classify django-taggit's ``TaggableManager`` (NetBox's
        # ``NetBoxModel.tags``), which is a Field but not a ManyToManyField
        # subclass.
        if getattr(f, "many_to_many", False):
            out.append(_fk_or_m2m_descriptor(f, FieldType.M2M))
            continue
        if getattr(f, "many_to_one", False) or getattr(f, "one_to_one", False):
            out.append(_fk_or_m2m_descriptor(f, FieldType.FK))
            continue
        if isinstance(f, BooleanField):
            out.append(_simple_descriptor(f, FieldType.BOOLEAN))
            continue
        if isinstance(f, IntegerField):
            out.append(_simple_descriptor(f, FieldType.INTEGER))
            continue
        if isinstance(f, DecimalField | FloatField):
            out.append(_simple_descriptor(f, FieldType.DECIMAL))
            continue
        if isinstance(f, DateTimeField):
            out.append(_simple_descriptor(f, FieldType.DATETIME))
            continue
        if isinstance(f, DateField):
            out.append(_simple_descriptor(f, FieldType.DATE))
            continue
        if isinstance(f, URLField):
            out.append(_simple_descriptor(f, FieldType.URL))
            continue
        if isinstance(f, JSONField):
            out.append(_simple_descriptor(f, FieldType.JSON))
            continue

        # CharField, SlugField, TextField, EmailField, IPAddressField, ...
        # All collapse to TEXT.
        out.append(_simple_descriptor(f, FieldType.TEXT))

    return out


def _simple_descriptor(f: DjangoField, type_: FieldType) -> FieldDescriptor:
    return FieldDescriptor(
        name=f.name,
        label=_label_for(f),
        type=type_,
        lookups=default_lookups_for(type_),
    )


def _select_descriptor(f: DjangoField) -> FieldDescriptor:
    # Django ``choices`` is a sequence of (value, label) tuples; normalize
    # to a tuple-of-tuples of plain strings for the wire format.
    raw_choices = tuple(f.choices)
    norm = tuple((str(v), str(label)) for v, label in raw_choices)
    return FieldDescriptor(
        name=f.name,
        label=_label_for(f),
        type=FieldType.SELECT,
        choices=norm,
        lookups=default_lookups_for(FieldType.SELECT),
    )


def _fk_or_m2m_descriptor(f: DjangoField, type_: FieldType) -> FieldDescriptor:
    target = f.related_model
    fk_target = f"{target._meta.app_label}.{target._meta.model_name}" if target else None
    return FieldDescriptor(
        name=f.name,
        label=_label_for(f),
        type=type_,
        fk_target=fk_target,
        lookups=default_lookups_for(type_),
    )


def _label_for(f: DjangoField) -> str:
    label = getattr(f, "verbose_name", None) or f.name
    return str(label)


# --- Custom fields ----------------------------------------------------------


# Map ``extras.CustomField.type`` values (NetBox 4.x) to our FieldType.
# Names taken from ``core.choices.CustomFieldTypeChoices`` -- kept as plain
# strings so we don't need to import that module at type-checking time.
_CF_TYPE_MAP: dict[str, FieldType] = {
    "text": FieldType.CF_TEXT,
    "longtext": FieldType.CF_LONGTEXT,
    "integer": FieldType.CF_INTEGER,
    "decimal": FieldType.CF_DECIMAL,
    "boolean": FieldType.CF_BOOLEAN,
    "date": FieldType.CF_DATE,
    "datetime": FieldType.CF_DATETIME,
    "url": FieldType.CF_URL,
    "json": FieldType.CF_JSON,
    "select": FieldType.CF_SELECT,
    "multiselect": FieldType.CF_MULTISELECT,
    "object": FieldType.CF_OBJECT,
    "multiobject": FieldType.CF_MULTIOBJECT,
}


def _custom_fields(content_type: ContentType) -> list[FieldDescriptor]:
    """Discover ``extras.CustomField`` rows assignable to this CT."""
    # Lazy import: extras.CustomField pulls in the apps registry.
    from extras.models import CustomField

    qs = CustomField.objects.filter(object_types=content_type)
    out: list[FieldDescriptor] = []
    for cf in qs:
        type_ = _CF_TYPE_MAP.get(cf.type)
        if type_ is None:
            # Unknown CF type (added in a newer NetBox we don't recognize);
            # surface it as JSON so the user can still write raw constraints.
            type_ = FieldType.CF_JSON

        choices = _cf_choices(cf, type_)
        fk_target = _cf_fk_target(cf, type_)

        out.append(
            FieldDescriptor(
                name=f"custom_field_data__{cf.name}",
                label=f"{cf.label or cf.name} [CF]",
                type=type_,
                is_custom_field=True,
                choices=choices,
                fk_target=fk_target,
                lookups=default_lookups_for(type_),
            )
        )
    return out


def _cf_choices(cf, type_: FieldType) -> tuple[tuple[str, str], ...] | None:
    """Pull choices from the CF's choice set, if applicable."""
    if type_ not in (FieldType.CF_SELECT, FieldType.CF_MULTISELECT):
        return None
    choice_set = getattr(cf, "choice_set", None)
    if not choice_set:
        return None
    # NetBox stores choices on ``CustomFieldChoiceSet.extra_choices``
    # as a list of [value, label] pairs.
    raw = getattr(choice_set, "extra_choices", None) or ()
    return tuple((str(v), str(label)) for v, label in raw)


def _cf_fk_target(cf, type_: FieldType) -> str | None:
    """For object / multiobject CFs return the target CT label."""
    if type_ not in (FieldType.CF_OBJECT, FieldType.CF_MULTIOBJECT):
        return None
    target = getattr(cf, "related_object_type", None)
    if target is None:
        return None
    return f"{target.app_label}.{target.model}"
