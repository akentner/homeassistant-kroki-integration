# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Custom Home Assistant integration that generates diagram images via [Kroki](https://kroki.io) servers. Uses a **hybrid configuration** approach: server connections via Config Flow (UI), diagram entities via YAML platform config. Distributed through HACS as a custom integration.

## Commands

```bash
make install          # Create .venv and install deps (pytest-homeassistant-custom-component, ruff, pre-commit)
make test             # Run pytest
make test-verbose     # Run pytest -v
make lint             # ruff check
make format           # ruff format + check --fix
make check            # CI-style: format --check + lint (no changes)
make validate         # hassfest + HACS validation (requires Docker)
make release                        # Interactive release script (bump, commit, push, GitHub release)
make release VERSION=2.0.0-alpha.6  # Non-interactive: pass version directly
```

Run a single test: `.venv/bin/pytest tests/test_image.py::test_function_name -v`

## Architecture

All code lives in `custom_components/kroki/`. The integration registers the `image` platform only.

- **`__init__.py`** -- Sets up reload service, stores config entry data in `hass.data[DOMAIN]`. Does NOT forward to platforms (YAML-driven).
- **`config_flow.py`** -- UI config flow for server URL + options flow (default output format, cache max size). Validates server via health check.
- **`image.py`** -- Core logic. `KrokiImageEntity` extends `ImageEntity`. Uses `async_track_template_result` to watch Jinja2 template dependencies and auto-re-render on entity state changes. Hash-based dedup prevents unnecessary API calls.
- **`kroki_client.py`** -- Async HTTP client. POST `/{diagram_type}/{output_format}` with plain text body. Custom exceptions: `KrokiConnectionError`, `KrokiRenderError`.
- **`cache.py`** -- `KrokiCache`: LRU file cache in `.storage/kroki/`, metadata in `cache_meta.json`. Keyed by SHA256 of `"{output_format}:{rendered_content}"`.
- **`const.py`** -- All constants, config keys, defaults, supported diagram types list.

## Key Design Decisions

- Templates are tracked via HA's `async_track_template_result`, not polled. The integration automatically detects referenced entities.
- On render error, the entity shows a red SVG error placeholder (not blank/unavailable).
- Cache hash includes output format, so SVG and PNG of the same diagram are cached separately.
- The first config entry's server URL is used for all YAML-defined entities.

## Linting & Style

- Ruff with Python 3.13 target, 120 char line length
- Rules: bugbear (B), pycodestyle (E/W), pyflakes (F), isort (I), pyupgrade (UP)
- Pre-commit hooks: trailing whitespace, EOF fixer, YAML/JSON check, ruff
