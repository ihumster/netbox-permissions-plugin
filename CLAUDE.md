# CLAUDE.md

Project conventions and tooling. Read this before making changes.

## Toolchain

- **Python**: 3.12+ (see `pyproject.toml` `requires-python`).
- **NetBox**: 4.4+ (see `PluginConfig.min_version` in `netbox_permissions_plugin/__init__.py`).
- **Package manager / runner**: [`uv`](https://github.com/astral-sh/uv). No `pip`, `python -m venv`, `python -m build`, `twine upload` directly. Use `uv pip install`, `uv venv`, `uv build`, `uv publish` instead.
- **Build backend**: `hatchling` (configured in `pyproject.toml`).
- **Linter / formatter**: `ruff` (config in `pyproject.toml` `[tool.ruff]`).
- **Tests**: `pytest` + `pytest-django`. Resolver-only tests (`test_q_builder.py`) run without NetBox; everything else needs a live NetBox install.

## CI / release

- CI runs on every PR and push to `main` / `develop` (`.github/workflows/ci.yml`):
  matrix `Python {3.12, 3.13} × NetBox {v4.4.0}`. Adding new versions is safe —
  jobs are independent and the `CI summary` job is what's required by branch protection.
- Releases trigger on `git tag v*.*.*` (`.github/workflows/release.yml`):
  `uv build` produces sdist + wheel, attaches to GitHub Release. PyPI publish
  via `uv publish` is gated behind `vars.PUBLISH_TO_PYPI=true` and PyPI Trusted
  Publishing (OIDC), no long-lived tokens.
- The pinned `UV_VERSION` lives in workflow `env:` blocks. Bump together.

## Code style rules

### Everything is English

All comments AND all user-facing UI text in this project MUST be in English. No multi-language support is planned. This applies to:

- Inline `#` comments in Python.
- YAML comments in `.github/workflows/*.yml`.
- TOML comments in `pyproject.toml`.
- Module-, class-, and function-level docstrings in Python.
- Comments in HTML templates (`<!-- ... -->`).
- All template-rendered strings: page headers, form labels, `help_text`, button text, table headers, tooltips, badge labels, error messages.
- Form field `label=` and `help_text=` in `forms.py`.

If you find Russian text anywhere in templates, forms, or code, translate it.

### Other

- Type hints required on all public functions and dataclasses.
- Prefer `from __future__ import annotations` at the top of every module
  (already applied across the codebase).
- Resolver layer (`netbox_permissions_plugin/resolver/`) must not import from
  views, forms, or templates — keep the dependency direction one-way.
- Lazy imports for `users.models.ObjectPermission` and friends inside functions,
  so the package can be loaded for AST/type checking without a NetBox install.

## Architecture quick reference

```
netbox_permissions_plugin/
├── __init__.py             # PluginConfig
├── settings.py             # PLUGINS_CONFIG accessor with defaults
├── urls.py
├── navigation.py
├── forms.py
├── template_content.py     # PluginTemplateExtension entries
├── resolver/               # core audit logic; no HTTP, no UI
│   ├── types.py            # DTOs (frozen dataclasses)
│   ├── _q.py               # constraints (JSON) -> Django Q
│   ├── membership.py       # MembershipProvider abstraction (SSO hook)
│   ├── effective.py
│   ├── reverse.py
│   └── tester.py
├── views/                  # function/CBV views, thin
├── templates/              # extends NetBox `base/layout.html`
└── tests/
```

When adding features for stage 2 (CRUD ObjectPermission, constraint builder),
resolver and UI layers must remain decoupled.
