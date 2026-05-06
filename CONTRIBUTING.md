# Contributing

Проект использует [`uv`](https://github.com/astral-sh/uv) для управления Python-окружениями, зависимостями, сборкой и публикацией. Никакой `pip`/`venv`/`build`/`twine` напрямую вызывать не надо.

Минимальные версии: **Python 3.12+**, **NetBox 4.4+**.

## Установка uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# либо через pipx / brew / scoop / winget — uv доступен почти везде
```

## Локальная разработка

NetBox-плагины тестируются поверх живого NetBox: его нужно поднять рядом и связать с плагином через editable-install в общем venv.

1. Склонировать NetBox 4.4+ рядом с проектом:

   ```bash
   git clone --depth 1 --branch v4.4.0 https://github.com/netbox-community/netbox.git ~/netbox
   ```

2. Создать venv с Python 3.12, общий для NetBox и плагина:

   ```bash
   cd ~/netbox
   uv venv --python 3.12 .venv
   . .venv/bin/activate     # или `. .venv/Scripts/activate` на Windows
   ```

3. Поставить зависимости NetBox и плагин в editable-режиме:

   ```bash
   uv pip install -r requirements.txt
   uv pip install -e '/path/to/netbox-permissions-plugin[dev]'
   ```

4. Поднять Postgres и Redis (например, через `docker compose up -d postgres redis`).

5. Сконфигурировать NetBox (`~/netbox/netbox/netbox/configuration.py`) — минимально:

   ```python
   PLUGINS = ["netbox_permissions_plugin"]
   PLUGINS_CONFIG = {"netbox_permissions_plugin": {}}
   # ... плюс DATABASE / REDIS / SECRET_KEY как обычно
   ```

6. Прогнать миграции и тесты:

   ```bash
   cd ~/netbox/netbox
   python manage.py migrate
   pytest /path/to/netbox-permissions-plugin/netbox_permissions_plugin/tests/
   ```

### Чисто Python-тесты без NetBox

Один файл — `test_q_builder.py` — не требует Django. Запустить из директории плагина:

```bash
cd /path/to/netbox-permissions-plugin
uv run --with pytest --with pytest-mock \
  pytest netbox_permissions_plugin/tests/test_q_builder.py
```

`uv run --with ...` создаёт временный venv с указанными пакетами, устанавливает плагин из текущего pyproject и запускает команду. Полезно для быстрой обратной связи в чистой логике резолвера.

## Lockfile (опционально)

Если нужна воспроизводимость — сгенерировать `uv.lock` и закоммитить:

```bash
uv lock
git add uv.lock
```

Локфайл фиксирует точные версии всех dev-зависимостей. CI его пока не использует (матрица версий важнее), но локально это удобно — `uv sync` восстановит окружение бит-в-бит.

## Pre-commit

```bash
uv tool install pre-commit
pre-commit install
```

Хуки прогоняют ruff (lint + format), trailing whitespace, проверку YAML/TOML.

## Что проверяет CI

`.github/workflows/ci.yml`:

- **lint** — `ruff check` и `ruff format --check`, поднятый через `uv tool run`.
- **pure-tests** — `test_q_builder.py` без поднятия NetBox (быстрый сигнал).
- **netbox-tests** — матрица Python 3.12/3.13 × NetBox v4.4.0:
  поднимает Postgres 16 + Redis 7 как services, ставит зависимости через `uv pip install`,
  гоняет `python manage.py migrate` и pytest по всем тестам плагина.

Расширить матрицу до нескольких версий NetBox: добавить элементы в
`matrix.netbox-ref` (например, `["v4.4.0", "v4.5.0", "develop"]`).

## Релиз

1. Бампнуть версию в `pyproject.toml` (`project.version` и `netbox_permissions_plugin.__version__`).
2. Закоммитить и запушить в `main`.
3. Создать annotated tag и запушить:

   ```bash
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin v0.1.0
   ```

4. `release.yml` сам:
   - проверит, что tag совпадает с версией в pyproject (`uv run python -c "import tomllib..."`);
   - соберёт sdist + wheel через `uv build`;
   - проверит метаданные через `twine check`;
   - прикрепит к GitHub Release;
   - опубликует на PyPI через `uv publish`, если в репозитории установлен `vars.PUBLISH_TO_PYPI=true`,
     создан environment `pypi`, и на pypi.org для проекта настроен Trusted Publisher (OIDC).

PyPI Trusted Publishing настраивается на pypi.org → Settings проекта → Publishing → Add a new publisher → GitHub. Указать owner, repo, workflow `release.yml`, environment `pypi`. После этого long-lived токены не нужны.

## Архитектура коротко

Слои изолированы — это упрощает тесты и постепенный rollout.

- `resolver/` — без HTTP, только Python и Django ORM. Содержит `compute_effective`,
  `reverse_lookup`, `explain` плюс DTO-типы. Если хочется добавить REST API — это
  делается тонким слоем поверх resolver-а.
- `views/`, `forms.py`, `templates/` — UI слой; ходит в Django ORM только через resolver.
- `template_content.py` — точка интеграции в детальные страницы NetBox.

При добавлении новой фичи в этап 2 (constraint builder и т.п.) старайтесь не пробивать слои — резолвер и UI должны оставаться раздельными.
