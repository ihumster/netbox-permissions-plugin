"""Общие фикстуры для тестов resolver-а.

Тесты идут поверх живого NetBox-окружения (через DJANGO_SETTINGS_MODULE=netbox.settings),
поэтому реально создают User, Group, ObjectPermission, dcim.Site и т.п.
Запускать через `pytest` из директории, где доступен NetBox.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def db_setup(db):
    """Маркер «нужна БД». Просто прокидывает pytest-django db fixture."""
    return db


@pytest.fixture
def User(db):
    from django.contrib.auth import get_user_model

    return get_user_model()


@pytest.fixture
def regular_user(User):
    return User.objects.create_user(username="alice", password="x", is_active=True)


@pytest.fixture
def superuser(User):
    return User.objects.create_user(
        username="root", password="x", is_active=True, is_superuser=True
    )


@pytest.fixture
def inactive_user(User):
    return User.objects.create_user(username="ghost", password="x", is_active=False)


@pytest.fixture
def group_a(db):
    from django.contrib.auth.models import Group

    return Group.objects.create(name="dc-engineers")


@pytest.fixture
def group_b(db):
    from django.contrib.auth.models import Group

    return Group.objects.create(name="noc-readonly")


@pytest.fixture
def site_ct(db):
    from django.contrib.contenttypes.models import ContentType

    return ContentType.objects.get(app_label="dcim", model="site")


@pytest.fixture
def make_objectperm(db, site_ct):
    from users.models import ObjectPermission

    def _make(name, *, actions, constraints=None, users=(), groups=(), enabled=True, content_types=()):
        cts = list(content_types) or [site_ct]
        perm = ObjectPermission.objects.create(
            name=name,
            enabled=enabled,
            actions=list(actions),
            constraints=constraints,
        )
        perm.object_types.set(cts)
        if users:
            perm.users.set(users)
        if groups:
            perm.groups.set(groups)
        return perm

    return _make


@pytest.fixture
def site_dc1(db):
    from dcim.models import Site

    return Site.objects.create(name="DC1", slug="dc1")


@pytest.fixture
def site_dc2(db):
    from dcim.models import Site

    return Site.objects.create(name="DC2", slug="dc2")
