"""Resolver — ядро аудита.

Этот пакет ничего не знает про HTTP, формы и шаблоны: только Python и Django ORM.
Это нужно, чтобы юнит-тесты гонялись быстро и без поднятия view'ов.
"""

from .effective import compute_effective
from .reverse import reverse_lookup
from .tester import explain
from .types import (
    DenyReason,
    EffectivePermissions,
    ExplainResult,
    GroupMembership,
    MembershipSource,
    ResolvedRule,
    RuleSource,
)

__all__ = [
    "DenyReason",
    "EffectivePermissions",
    "ExplainResult",
    "GroupMembership",
    "MembershipSource",
    "ResolvedRule",
    "RuleSource",
    "compute_effective",
    "explain",
    "reverse_lookup",
]
