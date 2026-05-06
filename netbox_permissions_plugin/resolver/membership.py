"""Источники членства пользователя в группах.

NetBox позволяет грузить пользователей из локальной базы, LDAP, SAML/OIDC.
В рантайме все они выглядят одинаково (User + Group), но мы хотим показывать
в UI **источник** членства, чтобы было ясно, кто реально владелец данных.

Архитектурно это сделано через провайдеры. Дефолт — DjangoMembershipProvider:
он ничего не знает об источниках и просто помечает все членства как LOCAL.
Если у вас в проде SSO с group claims, нужно подключить отдельный провайдер
(например, для python-social-auth — читать UserSocialAuth.extra_data),
указав его dotted-path в PLUGINS_CONFIG.
"""

from __future__ import annotations

from typing import Iterable, Protocol, TYPE_CHECKING

from django.utils.module_loading import import_string

from .. import settings as plugin_settings
from .types import GroupMembership, MembershipSource

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth.models import Group, User


class MembershipProvider(Protocol):
    """Контракт провайдера.

    Реализация должна вернуть GroupMembership для каждой группы, в которой
    пользователь состоит **с точки зрения этого провайдера**. Группы, не
    относящиеся к источнику (или если источник недоступен), просто
    пропускаются. Финальный список собирается комбинированием всех
    зарегистрированных провайдеров.
    """

    def memberships(self, user: "User") -> Iterable[GroupMembership]:  # pragma: no cover
        ...


class DjangoMembershipProvider:
    """Дефолтный провайдер — берёт user.groups как есть, помечает LOCAL."""

    def memberships(self, user: "User") -> Iterable[GroupMembership]:
        for group in user.groups.all():
            yield GroupMembership(
                group_id=group.pk,
                group_name=group.name,
                source=MembershipSource.LOCAL,
            )


def collect_memberships(user: "User") -> tuple[GroupMembership, ...]:
    """Собрать все членства из всех зарегистрированных провайдеров.

    Если один и тот же group_id приходит от нескольких провайдеров —
    выигрывает не-LOCAL источник (LOCAL считается fallback'ом).
    """
    providers = _load_providers()
    by_id: dict[int, GroupMembership] = {}
    for provider in providers:
        for m in provider.memberships(user):
            existing = by_id.get(m.group_id)
            if existing is None:
                by_id[m.group_id] = m
                continue
            # Уже есть запись — оставляем ту, у которой источник содержательнее.
            if existing.source == MembershipSource.LOCAL and m.source != MembershipSource.LOCAL:
                by_id[m.group_id] = m
    return tuple(sorted(by_id.values(), key=lambda gm: gm.group_name))


def _load_providers() -> list[MembershipProvider]:
    out: list[MembershipProvider] = []
    for path in plugin_settings.membership_provider_paths():
        cls = import_string(path)
        out.append(cls())
    return out
