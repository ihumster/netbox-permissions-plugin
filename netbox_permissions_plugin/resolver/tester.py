"""``explain(user, ct, object_id, action)`` -- single allow/deny check.

Returns an ``ExplainResult``: ``allowed`` True/False, the reason, and the rules
that matched.

We follow the same approach as NetBox at runtime -- Django permission +
ObjectPermission -- but additionally record a trace so the user can see which
rule allowed (or failed to allow) the action.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from ._q import NeverMatch, constraints_to_q
from .effective import compute_effective
from .types import DenyReason, ExplainResult, ResolvedRule


def explain(
    user,
    content_type: ContentType,
    object_id: Any,
    action: str,
) -> ExplainResult:
    """Explain whether ``user`` may perform ``action`` on the given object."""
    User = get_user_model()
    if not isinstance(user, User):
        raise TypeError(f"Expected user instance, got {type(user)!r}")

    label_ct = f"{content_type.app_label}.{content_type.model}"

    if not user.is_active:
        return ExplainResult(
            allowed=False,
            user_id=user.pk,
            user_label=user.username,
            object_type_label=label_ct,
            object_id=object_id,
            action=action,
            deny_reason=DenyReason.INACTIVE,
            deny_detail="User is deactivated.",
        )

    if user.is_superuser:
        eff = compute_effective(user)
        return ExplainResult(
            allowed=True,
            user_id=user.pk,
            user_label=user.username,
            object_type_label=label_ct,
            object_id=object_id,
            action=action,
            matched_rules=eff.rules,
        )

    # All of the user's rules for this CT and this action.
    eff = compute_effective(user)
    relevant_list: list[ResolvedRule] = []
    for r in eff.rules:
        if r.object_type_app_label != content_type.app_label:
            continue
        if r.object_type_model != content_type.model:
            continue
        if action not in r.actions:
            continue
        if not r.enabled:
            continue
        relevant_list.append(r)
    relevant = tuple(relevant_list)
    if not relevant:
        return ExplainResult(
            allowed=False,
            user_id=user.pk,
            user_label=user.username,
            object_type_label=label_ct,
            object_id=object_id,
            action=action,
            deny_reason=DenyReason.NO_OBJECT_PERM,
            deny_detail=(f"User has no ObjectPermission on {label_ct} with action={action!r}."),
        )

    model = content_type.model_class()
    if model is None:
        return ExplainResult(
            allowed=False,
            user_id=user.pk,
            user_label=user.username,
            object_type_label=label_ct,
            object_id=object_id,
            action=action,
            deny_reason=DenyReason.UNKNOWN_ACTION,
            deny_detail=f"ContentType {label_ct} is not bound to a model.",
        )

    matched: list[ResolvedRule] = []
    for r in relevant:
        try:
            q = constraints_to_q(r.constraints)
        except NeverMatch:
            continue
        if model._default_manager.filter(pk=object_id).filter(q).exists():
            matched.append(r)

    if matched:
        return ExplainResult(
            allowed=True,
            user_id=user.pk,
            user_label=user.username,
            object_type_label=label_ct,
            object_id=object_id,
            action=action,
            matched_rules=tuple(matched),
        )

    return ExplainResult(
        allowed=False,
        user_id=user.pk,
        user_label=user.username,
        object_type_label=label_ct,
        object_id=object_id,
        action=action,
        deny_reason=DenyReason.CONSTRAINTS_NOT_MATCHED,
        deny_detail=(
            f"Found {len(relevant)} rule(s) with the requested action, but "
            f"no constraint matched object id={object_id}."
        ),
        matched_rules=relevant,  # show the candidates as "did not fire"
    )
