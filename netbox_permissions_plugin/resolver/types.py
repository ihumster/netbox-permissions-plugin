"""Типы данных, возвращаемые resolver-ом.

Все DTO — frozen dataclass-ы; views только читают и рендерят.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MembershipSource(str, Enum):
    """Откуда у пользователя членство в группе."""

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
    # Произвольные детали от провайдера: claim path, DN, etc. — для отображения.
    detail: str | None = None


class RuleSource(str, Enum):
    """Каким путём ObjectPermission достался пользователю."""

    DIRECT = "direct"  # User.object_permissions
    GROUP = "group"  # через Group.object_permissions
    SUPERUSER = "superuser"  # синтетический, для is_superuser=True


@dataclass(frozen=True)
class ResolvedRule:
    """Одна строка эффективных прав после резолва.

    Каждая ResolvedRule всегда соответствует одному ObjectPermission
    в комбинации с одним ContentType. Если ObjectPermission связан с
    несколькими CT, при резолве он распадается на несколько ResolvedRule.
    """

    permission_id: int | None  # None для синтетических superuser-правил
    permission_name: str
    enabled: bool
    actions: tuple[str, ...]
    constraints: dict[str, Any] | list[dict[str, Any]] | None
    object_type_app_label: str
    object_type_model: str
    source: RuleSource
    via_group: GroupMembership | None = None  # заполнено для source=GROUP

    @property
    def object_type_label(self) -> str:
        return f"{self.object_type_app_label}.{self.object_type_model}"

    @property
    def is_unrestricted(self) -> bool:
        """`None` или `{}` означают «без ограничений»."""
        c = self.constraints
        if c is None:
            return True
        if isinstance(c, dict) and len(c) == 0:
            return True
        return False

    @property
    def is_never_match(self) -> bool:
        """Пустой список `[]` означает «никогда не матчится» (идиома NetBox)."""
        return isinstance(self.constraints, list) and len(self.constraints) == 0


@dataclass(frozen=True)
class EffectivePermissions:
    """Полный набор эффективных прав одного субъекта (User или Group)."""

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
    """Результат единичной проверки allow/deny."""

    allowed: bool
    user_id: int
    user_label: str
    object_type_label: str
    object_id: Any
    action: str
    matched_rules: tuple[ResolvedRule, ...] = field(default_factory=tuple)
    deny_reason: DenyReason | None = None
    deny_detail: str | None = None
