"""Sources of group membership for a user.

NetBox can load users from the local DB, LDAP, or SAML/OIDC. At runtime they
all look the same (User + Group), but we want the UI to show the **source** of
the membership so it is clear who actually owns the data.

Architecturally this is a provider pattern. The default provider —
``DjangoMembershipProvider`` — knows nothing about external sources and marks
every membership as ``LOCAL``. If your prod has SSO with group claims, plug in
a provider that reads them (for example, for python-social-auth — read
``UserSocialAuth.extra_data``) by adding its dotted path to ``PLUGINS_CONFIG``.
"""

from __future__ import annotations

from typing import Iterable, Protocol, TYPE_CHECKING

from django.utils.module_loading import import_string

from .. import settings as plugin_settings
from .types import GroupMembership, MembershipSource

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth.models import Group, User


class MembershipProvider(Protocol):
    """Provider contract.

    An implementation must yield a ``GroupMembership`` for each group the user
    belongs to **from this provider's perspective**. Groups not relevant to the
    source (or when the source is unavailable) are simply skipped. The final
    list is built by combining all registered providers.
    """

    def memberships(self, user: "User") -> Iterable[GroupMembership]:  # pragma: no cover
        ...


class DjangoMembershipProvider:
    """Default provider — uses ``user.groups`` as is, marking everything LOCAL."""

    def memberships(self, user: "User") -> Iterable[GroupMembership]:
        for group in user.groups.all():
            yield GroupMembership(
                group_id=group.pk,
                group_name=group.name,
                source=MembershipSource.LOCAL,
            )


def collect_memberships(user: "User") -> tuple[GroupMembership, ...]:
    """Combine memberships from every registered provider.

    If the same ``group_id`` is reported by multiple providers, a non-LOCAL
    source wins (LOCAL is treated as the fallback).
    """
    providers = _load_providers()
    by_id: dict[int, GroupMembership] = {}
    for provider in providers:
        for m in provider.memberships(user):
            existing = by_id.get(m.group_id)
            if existing is None:
                by_id[m.group_id] = m
                continue
            # Already present — keep whichever has a more meaningful source.
            if existing.source == MembershipSource.LOCAL and m.source != MembershipSource.LOCAL:
                by_id[m.group_id] = m
    return tuple(sorted(by_id.values(), key=lambda gm: gm.group_name))


def _load_providers() -> list[MembershipProvider]:
    out: list[MembershipProvider] = []
    for path in plugin_settings.membership_provider_paths():
        cls = import_string(path)
        out.append(cls())
    return out
