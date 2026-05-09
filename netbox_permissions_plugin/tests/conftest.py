"""Shared fixtures for resolver tests.

These tests run against a live NetBox environment (DJANGO_SETTINGS_MODULE=netbox.settings),
so they really create User, Group, ObjectPermission, dcim.Site, etc.
Run via ``pytest`` from a directory where NetBox is importable.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def db_setup(db):
    """Marker for "needs DB". Just re-exports the pytest-django ``db`` fixture."""
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
    # NetBox 4.x ships a custom Group model in `users.models`; the M2M on its
    # User points there, not at django.contrib.auth.models.Group.
    from users.models import Group

    return Group.objects.create(name="dc-engineers")


@pytest.fixture
def group_b(db):
    from users.models import Group

    return Group.objects.create(name="noc-readonly")


@pytest.fixture
def site_ct(db):
    from django.contrib.contenttypes.models import ContentType

    return ContentType.objects.get(app_label="dcim", model="site")


@pytest.fixture
def make_objectperm(db, site_ct):
    from users.models import ObjectPermission

    def _make(
        name, *, actions, constraints=None, users=(), groups=(), enabled=True, content_types=()
    ):
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
