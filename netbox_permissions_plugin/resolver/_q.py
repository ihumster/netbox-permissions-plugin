"""Helpers for applying NetBox-style constraints.

NetBox stores constraints in a JSONField:

- ``None`` or ``{}`` — no restrictions (always True);
- ``dict`` — all keys ANDed together;
- ``list[dict]`` — alternatives ORed together; an empty list means "never".

Each dict key is a Django ORM lookup (``field__sub__lookup``); the value is
passed to ``Q(...)`` as is.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Q


class NeverMatch(Exception):
    """Marker: constraints == [] — the filter must reject everything."""


def constraints_to_q(constraints: dict[str, Any] | list[dict[str, Any]] | None) -> Q:
    """Convert constraints to a Q object.

    Returns ``Q()`` (i.e. "anything matches") when no constraints are present.
    Raises ``NeverMatch`` when constraints is an empty list.
    """
    if constraints is None:
        return Q()
    if isinstance(constraints, dict):
        if not constraints:
            return Q()
        return Q(**constraints)
    if isinstance(constraints, list):
        if not constraints:
            raise NeverMatch
        q = Q()
        for chunk in constraints:
            if not isinstance(chunk, dict):
                # Structurally invalid — skip; do not make the rule overly permissive.
                continue
            q |= Q(**chunk) if chunk else Q()
        return q
    # Unknown type — treat as "no restrictions", but this is anomalous data.
    return Q()
