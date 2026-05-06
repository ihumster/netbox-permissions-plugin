"""``compute_effective(user)`` — the main audit entry point.

Algorithm:

1. If ``user.is_active`` is False, return an empty set with the inactive flag.
   Django's permission backend would also return False, but the audit page
   wants to show the user and the rules they "would have" if reactivated.
2. If ``user.is_superuser`` is True, return a synthetic ResolvedRule marked
   SUPERUSER. In reality a superuser bypasses the permission backend entirely.
3. Otherwise, fetch every enabled ObjectPermission attached to the user
   directly or via any of their groups (single SQL query with distinct).
4. Expand each ObjectPermission across its object_types and assignment paths.
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
    """Compute effective permissions for the given user.

    Accepts an instance of ``get_user_model()``.
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
    """Effective permissions of the group itself, ignoring its members."""
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
    """Lazily import ObjectPermission so this module loads without NetBox."""
    from users.models import ObjectPermission

    return ObjectPermission


def _resolve_for_user(user, memberships: tuple[GroupMembership, ...]) -> Iterable[ResolvedRule]:
    """Fetch every ObjectPermission relevant to the user and expand them."""
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
        # The same ObjectPermission can be both directly assigned and granted
        # via a group; emit separate rows so all sources are visible.
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


def _make_rule(
    perm,
    content_type,
    source: RuleSource,
    via_group: GroupMembership | None,
) -> ResolvedRule:
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
