"""Утилиты для применения NetBox-style constraints.

NetBox хранит constraints в JSONField:
- None или {} — без ограничений (всегда True);
- dict — все ключи AND;
- list[dict] — список вариантов OR; пустой список означает «никогда».

Каждый ключ dict — это lookup в Django ORM (`field__sub__lookup`),
значение — то, что туда передаётся в Q(...).
"""

from __future__ import annotations

from typing import Any

from django.db.models import Q


class NeverMatch(Exception):
    """Маркер: constraints = [] — фильтр никогда не должен пропускать ничего."""


def constraints_to_q(constraints: dict[str, Any] | list[dict[str, Any]] | None) -> Q:
    """Преобразовать constraints в Q-объект.

    Возвращает Q() (т.е. «всё подходит»), если ограничений нет.
    Бросает NeverMatch, если constraints — пустой список.
    """
    if constraints is None:
        return Q()
    if isinstance(constraints, dict):
        if not constraints:
            return Q()
        return Q(**constraints)
    if isinstance(constraints, list):
        if not constraints:
            raise NeverMatch
        q = Q()
        for chunk in constraints:
            if not isinstance(chunk, dict):
                # Структурно невалидно — пропускаем; не делаем правило слишком permissive.
                continue
            q |= Q(**chunk) if chunk else Q()
        return q
    # Неизвестный тип — считаем «без ограничений», но это аномалия.
    return Q()
