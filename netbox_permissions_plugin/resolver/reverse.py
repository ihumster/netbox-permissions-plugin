"""``reverse_lookup(content_type, object_id, action=None)``.

Algorithm:

1. Pull enabled ObjectPermission rows whose ``object_types`` includes the CT
   (and, when ``action`` is provided, whose ``actions`` contains it).
2. For each rule, apply its constraints as a Q on the model queryset and check
   whether the requested object passes the filter. This is a single SQL per
   rule of the form
   ``Model.objects.filter(pk=object_id).filter(<constraints>).exists()``.
3. Return a list of MatchingRule with attached users/groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib.contenttypes.models import ContentType

from ._q import NeverMatch, constraints_to_q
from .types import ResolvedRule, RuleSource


@dataclass(frozen=True)
class GranteePrincipal:
    kind: str  # "user" | "group"
    id: int
    label: str


@dataclass(frozen=True)
class MatchingRule:
    rule: ResolvedRule
    grantees: tuple[GranteePrincipal, ...]


def reverse_lookup(
    content_type: ContentType,
    object_id: Any,
    action: str | None = None,
) -> tuple[MatchingRule, ...]:
    """Who has access to the given object, and via which rule."""
    from users.models import ObjectPermission

    qs = ObjectPermission.objects.filter(
        object_types=content_type,
        enabled=True,
    )
    if action:
        # ``actions`` is a JSON list of strings; check membership via Postgres ``?``.
        qs = qs.filter(actions__contains=[action])

    qs = qs.prefetch_related("object_types", "users", "groups").distinct()

    model = content_type.model_class()
    if model is None:
        return ()

    matching: list[MatchingRule] = []

    for perm in qs:
        try:
            q = constraints_to_q(perm.constraints)
        except NeverMatch:
            continue
        # One query per rule -- fine at 5-25 perms per CT.
        if not model._default_manager.filter(pk=object_id).filter(q).exists():
            continue

        rule = ResolvedRule(
            permission_id=perm.pk,
            permission_name=perm.name,
            enabled=perm.enabled,
            actions=tuple(perm.actions or ()),
            constraints=perm.constraints,
            object_type_app_label=content_type.app_label,
            object_type_model=content_type.model,
            source=RuleSource.DIRECT,  # less meaningful for reverse-lookup output
        )
        grantees = tuple(_grantees_for(perm))
        matching.append(MatchingRule(rule=rule, grantees=grantees))

    # Superusers should also appear in reverse-lookup so the on-call sees the
    # full access list at a glance.
    matching.extend(_superuser_matches(content_type, object_id))
    return tuple(matching)


def _grantees_for(perm) -> list[GranteePrincipal]:
    out: list[GranteePrincipal] = []
    for u in perm.users.all():
        out.append(GranteePrincipal(kind="user", id=u.pk, label=u.username))
    for g in perm.groups.all():
        out.append(GranteePrincipal(kind="group", id=g.pk, label=g.name))
    return out


def _superuser_matches(content_type: ContentType, object_id: Any) -> list[MatchingRule]:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    superusers = User.objects.filter(is_superuser=True, is_active=True)
    if not superusers.exists():
        return []

    rule = ResolvedRule(
        permission_id=None,
        permission_name="<superuser>",
        enabled=True,
        actions=("view", "add", "change", "delete"),
        constraints=None,
        object_type_app_label=content_type.app_label,
        object_type_model=content_type.model,
        source=RuleSource.SUPERUSER,
    )
    grantees = tuple(
        GranteePrincipal(kind="user", id=u.pk, label=u.username) for u in superusers
    )
    return [MatchingRule(rule=rule, grantees=grantees)]
