# NetBox Permissions Plugin

[![CI](https://github.com/OWNER/netbox-permissions-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/netbox-permissions-plugin/actions/workflows/ci.yml)

Аудит и (в будущем) визуальный конструктор `users.ObjectPermission` для NetBox 4.4+.

Целевые версии: **NetBox ≥ 4.4**, **Python ≥ 3.12**.
Сборка и dev-окружение — через [`uv`](https://github.com/astral-sh/uv).

> Замените `OWNER` в URL бейджа на свой GitHub-аккаунт/организацию после создания репозитория.

## Что есть в этом MVP (этап 1)

Плагин **только читает** существующие права. Запись через UI и constraint-builder появятся в этапе 2.

Три страницы под `/plugins/permissions/`:

* **Effective permissions for user** — что реально может пользователь, с разворачиванием по группам и источникам.
* **Reverse lookup** — кто имеет доступ к указанному объекту и через какое правило.
* **Permission tester** — единичная проверка allow/deny с трассой по сработавшим/не сработавшим constraints.

Плюс вкладка **Permissions** на детальной странице ключевых моделей (Device, Site, Rack, Prefix, IP, Tenant, VM, Circuit, Script).

## Установка

В venv NetBox (используем uv):

```bash
uv pip install -e /path/to/netbox-permissions-plugin
```

В `configuration.py`:

```python
PLUGINS = [
    "netbox_permissions_plugin",
]

PLUGINS_CONFIG = {
    "netbox_permissions_plugin": {
        # Группы, которые синхронизируются из IdP — отображаются с пометкой,
        # запись в них в этапе 2 будет заблокирована.
        "external_groups": ["sso-admins", "sso-noc"],
        # Сколько объектов показывать в превью (для этапа 2).
        "preview_sample_size": 25,
        # Точка кастомизации для SAML/OIDC group claims —
        # подключите свой провайдер по dotted-path.
        "membership_providers": [
            "netbox_permissions_plugin.resolver.membership.DjangoMembershipProvider",
        ],
    },
}
```

Затем — стандартное:

```bash
python manage.py collectstatic --no-input
systemctl restart netbox netbox-rq
```

Доступ к UI плагина гейтится Django-permission `users.view_objectpermission`.

## Запуск тестов

Полный test suite требует поднятого NetBox с БД — см. [CONTRIBUTING.md](CONTRIBUTING.md).

Чисто Python-тесты (без NetBox-стека) — одной командой:

```bash
uv run --with pytest --with pytest-mock \
  pytest netbox_permissions_plugin/tests/test_q_builder.py
```

## Архитектура

```
netbox_permissions_plugin/
├── __init__.py             # PluginConfig
├── settings.py             # обёртка над PLUGINS_CONFIG
├── urls.py                 # маршруты /plugins/permissions/*
├── navigation.py           # пункт меню «Permissions Audit»
├── forms.py                # 3 формы для аудит-страниц
├── template_content.py     # вкладка «Permissions» на объектах
├── resolver/               # ядро аудита, без HTTP/UI
│   ├── types.py            # DTO: ResolvedRule, EffectivePermissions, ExplainResult
│   ├── _q.py               # constraints (JSON) → django.db.models.Q
│   ├── membership.py       # MembershipProvider — точка кастомизации SSO
│   ├── effective.py        # compute_effective(user)
│   ├── reverse.py          # reverse_lookup(ct, id, action=None)
│   └── tester.py           # explain(user, ct, id, action)
├── views/                  # 3 view-класса для аудит-страниц
├── templates/              # HTML-шаблоны на base/layout.html NetBox
└── tests/                  # pytest-django
```

Resolver намеренно изолирован от Django-views и шаблонов — это упрощает юнит-тесты и подготавливает почву для REST API (этап 3).

## Roadmap

* **Этап 2** — CRUD `users.ObjectPermission` через UI плагина: wizard, constraint builder с автокомплитом полей и custom fields, dry-run preview, `ConstraintSnippet`, `PermissionAuditEvent`.
* **Этап 3** — REST API (`/api/plugins/permissions/...`) под автоматизацию через pyinfra/ansible, management-команды.
* **Этап 4** — кэш эффективных прав (по сигналам), 4-eyes approval, GitOps (опционально).
