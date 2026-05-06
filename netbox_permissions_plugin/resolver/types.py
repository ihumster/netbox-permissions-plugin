"""Data types returned by the resolver.

All DTOs are frozen dataclasses; views only read and render them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MembershipSource(str, Enum):
    """Where a user's group membership comes from."""

    LOCAL = "local"
    SAML = "saml"
    OIDC = "oidc"
    LDAP = "ldap"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GroupMembership:
    group_id: int
    group_name: str
    source: MembershipSource
    # Free-form provider details for display: claim path, DN, etc.
    detail: str | None = None


class RuleSource(str, Enum):
    """How an ObjectPermission reaches the user."""

    DIRECT = "direct"  # User.object_permissions
    GROUP = "group"  # via Group.object_permissions
    SUPERUSER = "superuser"  # synthetic, for is_superuser=True


@dataclass(frozen=True)
class ResolvedRule:
    """One row of effective permissions after resolution.

    A ResolvedRule always corresponds to a single ObjectPermission combined
    with a single ContentType. If the source ObjectPermission is linked to
    multiple CTs, it expands into multiple ResolvedRule rows during resolution.
    """

    permission_id: int | None  # None for synthetic superuser rules
    permission_name: str
    enabled: bool
    actions: tuple[str, ...]
    constraints: dict[str, Any] | list[dict[str, Any]] | None
    object_type_app_label: str
    object_type_model: str
    source: RuleSource
    via_group: GroupMembership | None = None  # populated when source=GROUP

    @property
    def object_type_label(self) -> str:
        return f"{self.object_type_app_label}.{self.object_type_model}"

    @property
    def is_unrestricted(self) -> bool:
        """``None`` or ``{}`` mean "no constraints"."""
        c = self.constraints
        if c is None:
            return True
        if isinstance(c, dict) and len(c) == 0:
            return True
        return False

    @property
    def is_never_match(self) -> bool:
        """Empty list ``[]`` means "never matches" (NetBox idiom)."""
        return isinstance(self.constraints, list) and len(self.constraints) == 0


@dataclass(frozen=True)
class EffectivePermissions:
    """Full set of effective permissions for a single subject (User or Group)."""

    subject_kind: str  # "user" | "group"
    subject_id: int
    subject_label: str
    is_superuser: bool
    is_active: bool
    memberships: tuple[GroupMembership, ...]
    rules: tuple[ResolvedRule, ...]

    def by_object_type(self) -> dict[str, list[ResolvedRule]]:
        out: dict[str, list[ResolvedRule]] = {}
        for r in self.rules:
            out.setdefault(r.object_type_label, []).append(r)
        return out


class DenyReason(str, Enum):
    INACTIVE = "user_inactive"
    NO_DJANGO_PERM = "no_django_permission"
    NO_OBJECT_PERM = "no_object_permission"
    CONSTRAINTS_NOT_MATCHED = "constraints_did_not_match"
    UNKNOWN_ACTION = "unknown_action"


@dataclass(frozen=True)
class ExplainResult:
    """Result of a single allow/deny check."""

    allowed: bool
    user_id: int
    user_label: str
    object_type_label: str
    object_id: Any
    action: str
    matched_rules: tuple[ResolvedRule, ...] = field(default_factory=tuple)
    deny_reason: DenyReason | None = None
    deny_detail: str | None = None
