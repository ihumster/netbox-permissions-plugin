"""compute_effective(user) — основной метод аудита.

Алгоритм:

1. Если user.is_active=False — возвращаем пустой набор с пометкой;
   в Django backend всё равно вернёт False, но в аудите хочется видеть человека
   и его потенциальные права (то, что у него «было бы», но не работает).
2. Если user.is_superuser=True — возвращаем синтетическую ResolvedRule
   с маркером SUPERUSER. В реальности superuser обходит permission backend.
3. Иначе — выгружаем все enabled ObjectPermission, привязанные к user
   напрямую или через любую из его групп (один SQL-запрос с distinct).
4. Каждый ObjectPermission «разворачиваем» по object_types и источникам.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from django.contrib.auth import get_user_model
from django.db.models import Q

from .membership import collect_memberships
from .types import (
    EffectivePermissions,
    GroupMembership,
    MembershipSource,
    ResolvedRule,
    RuleSource,
)

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth.models import Group


def compute_effective(user) -> EffectivePermissions:
    """Вычислить эффективные права для пользователя.

    Принимает экземпляр User (из get_user_model()).
    """
    User = get_user_model()
    if not isinstance(user, User):
        raise TypeError(f"Expected user instance, got {type(user)!r}")

    memberships = collect_memberships(user)

    if not user.is_active:
        return EffectivePermissions(
            subject_kind="user",
            subject_id=user.pk,
            subject_label=user.username,
            is_superuser=user.is_superuser,
            is_active=False,
            memberships=memberships,
            rules=(),
        )

    if user.is_superuser:
        rules = (
            ResolvedRule(
                permission_id=None,
                permission_name="<superuser>",
                enabled=True,
                actions=("view", "add", "change", "delete"),
                constraints=None,
                object_type_app_label="*",
                object_type_model="*",
                source=RuleSource.SUPERUSER,
            ),
        )
        return EffectivePermissions(
            subject_kind="user",
            subject_id=user.pk,
            subject_label=user.username,
            is_superuser=True,
            is_active=True,
            memberships=memberships,
            rules=rules,
        )

    rules = tuple(_resolve_for_user(user, memberships))
    return EffectivePermissions(
        subject_kind="user",
        subject_id=user.pk,
        subject_label=user.username,
        is_superuser=False,
        is_active=True,
        memberships=memberships,
        rules=rules,
    )


def compute_effective_for_group(group) -> EffectivePermissions:
    """Эффективные права самой группы (без членов)."""
    rules = tuple(_resolve_for_group(group))
    return EffectivePermissions(
        subject_kind="group",
        subject_id=group.pk,
        subject_label=group.name,
        is_superuser=False,
        is_active=True,
        memberships=(),
        rules=rules,
    )


def _object_permission_model():
    """Лениво импортируем ObjectPermission, чтобы модуль грузился без NetBox."""
    from users.models import ObjectPermission

    return ObjectPermission


def _resolve_for_user(user, memberships: tuple[GroupMembership, ...]) -> Iterable[ResolvedRule]:
    """Достать все ObjectPermission, относящиеся к user, и развернуть."""
    ObjectPermission = _object_permission_model()
    group_ids = [m.group_id for m in memberships]

    qs = (
        ObjectPermission.objects.filter(
            Q(users=user) | Q(groups__in=group_ids),
            enabled=True,
        )
        .prefetch_related("object_types", "users", "groups")
        .distinct()
    )

    membership_by_id = {m.group_id: m for m in memberships}

    for perm in qs:
        # Один и тот же ObjectPermission может быть и прямым, и через группу —
        # эмитим записи отдельно, чтобы пользователь видел все источники.
        directly_assigned = perm.users.filter(pk=user.pk).exists()
        related_groups = list(perm.groups.filter(pk__in=group_ids))

        for ct in perm.object_types.all():
            if directly_assigned:
                yield _make_rule(perm, ct, RuleSource.DIRECT, None)
            for g in related_groups:
                yield _make_rule(
                    perm,
                    ct,
                    RuleSource.GROUP,
                    membership_by_id.get(g.pk),
                )


def _resolve_for_group(group) -> Iterable[ResolvedRule]:
    ObjectPermission = _object_permission_model()
    qs = (
        ObjectPermission.objects.filter(groups=group, enabled=True)
        .prefetch_related("object_types")
        .distinct()
    )
    fake_membership = GroupMembership(
        group_id=group.pk,
        group_name=group.name,
        source=MembershipSource.LOCAL,
    )
    for perm in qs:
        for ct in perm.object_types.all():
            yield _make_rule(perm, ct, RuleSource.GROUP, fake_membership)


def _make_rule(perm, content_type, source: RuleSource, via_group: GroupMembership | None) -> ResolvedRule:
    return ResolvedRule(
        permission_id=perm.pk,
        permission_name=perm.name,
        enabled=perm.enabled,
        actions=tuple(perm.actions or ()),
        constraints=perm.constraints,
        object_type_app_label=content_type.app_label,
        object_type_model=content_type.model,
        source=source,
        via_group=via_group,
    )
