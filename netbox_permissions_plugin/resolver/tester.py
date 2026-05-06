"""explain(user, ct, object_id, action) — единичная проверка allow/deny.

Возвращает ExplainResult: allowed True/False, причина, какие правила сработали.

Используем тот же подход, что и NetBox в рантайме: смотрим Django-permission
+ ObjectPermission, но дополнительно сохраняем трассу, чтобы пользователь
видел, какое именно правило допустило/не допустило действие.
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
    """Объяснить, может ли user выполнить action над объектом."""
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
            deny_detail="Пользователь деактивирован.",
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

    # Все правила пользователя на этот CT с этим action.
    eff = compute_effective(user)
    relevant = tuple(
        r for r in eff.rules
        if r.object_type_app_label == content_type.app_label
        and r.object_type_model == content_type.model
        and action in r.actions
        and r.enabled
    )
    if not relevant:
        return ExplainResult(
            allowed=False,
            user_id=user.pk,
            user_label=user.username,
            object_type_label=label_ct,
            object_id=object_id,
            action=action,
            deny_reason=DenyReason.NO_OBJECT_PERM,
            deny_detail=(
                f"У пользователя нет ни одного ObjectPermission на "
                f"{label_ct} с action={action!r}."
            ),
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
            deny_detail=f"ContentType {label_ct} не привязан к модели.",
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
            f"Найдено {len(relevant)} правил с нужным action, но ни одно "
            f"constraints не совпало с объектом id={object_id}."
        ),
        matched_rules=relevant,  # показываем кандидатов как «не сработали»
    )
