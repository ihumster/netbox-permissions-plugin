"""reverse_lookup(content_type, object_id, action=None).

Алгоритм:
1. Достаём enabled ObjectPermission, у которых в object_types этот CT
   и (если задан action) в actions есть запрошенный action.
2. Для каждого ObjectPermission применяем его constraints как Q к queryset
   модели и проверяем, попадает ли указанный объект под фильтр.
   Это делается одним SQL-запросом на правило вида
   `Model.objects.filter(pk=object_id).filter(<constraints>).exists()`.
3. Возвращаем список MatchingRule с привязанными users/groups.
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
    """Кто и через какое правило имеет доступ к указанному объекту."""
    from users.models import ObjectPermission

    qs = ObjectPermission.objects.filter(
        object_types=content_type,
        enabled=True,
    )
    if action:
        # actions хранится как список строк; проверяем contains через Postgres `?`.
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
        # Один запрос на правило — на 5–25 perms на CT это нормально.
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
            source=RuleSource.DIRECT,  # для reverse это поле менее значимо
        )
        grantees = tuple(_grantees_for(perm))
        matching.append(MatchingRule(rule=rule, grantees=grantees))

    # superuser-ы: их в reverse-lookup тоже стоит показывать,
    # потому что для дежурного важно увидеть полный список доступов.
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
