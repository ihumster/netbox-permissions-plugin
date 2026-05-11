"""django-filter filtersets for the plugin's models.

Two different bases:

* ``ConstraintSnippet`` extends ``NetBoxModel``, so we use
  ``NetBoxModelFilterSet`` to pick up the standard ``q`` search, tags
  filter, and ``created/last_updated`` lookups for free.
* ``PermissionAuditEvent`` is a plain ``models.Model`` (no NetBoxModel
  bases) by design -- it has no tags, no journal, no ``created``/
  ``last_updated``, only ``timestamp``. ``NetBoxModelFilterSet`` tries to
  auto-generate filters for the missing fields and crashes at import time
  with ``ValueError: Invalid field name/lookup on created: created``, so
  we drop down to plain ``django_filters.FilterSet`` here.
"""

from __future__ import annotations

import django_filters
from netbox.filtersets import NetBoxModelFilterSet

from .models import ConstraintSnippet, PermissionAuditEvent


class ConstraintSnippetFilterSet(NetBoxModelFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ConstraintSnippet
        fields = ("id", "name", "description", "object_types")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(name__icontains=value) | queryset.filter(
            description__icontains=value
        )


class PermissionAuditEventFilterSet(django_filters.FilterSet):
    """Filter for the audit list view.

    No ``q`` search (audit entries have no human-name field worth indexing).
    Action is a choice filter; user and target_type are exact-match;
    timestamp supports ``gte``/``lte`` for time-range queries.
    """

    action = django_filters.ChoiceFilter(
        choices=PermissionAuditEvent._meta.get_field("action").choices,
    )
    timestamp = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = PermissionAuditEvent
        fields = ("id", "user", "action", "target_type", "timestamp")
