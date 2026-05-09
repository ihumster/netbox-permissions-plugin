"""Resolver -- the audit core.

This package knows nothing about HTTP, forms, or templates: only Python and
the Django ORM. Keeping it pure lets unit tests run fast without touching the
view layer.
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
