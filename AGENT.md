# AGENT.md – Kroki Integration for Home Assistant

## Project Overview

A Home Assistant custom integration that generates dynamic diagram images via [Kroki](https://kroki.io). Jinja2 templates containing HA entity references are rendered into diagram source code, sent to a Kroki server, and the resulting image (SVG or PNG) is provided as an HA Image entity.

## Architecture

```
Config Flow (UI)                 YAML Platform Config
    │                                   │
    ▼                                   ▼
┌─────────────────┐         ┌──────────────────────┐
│ Config Entry    │         │ Image Entities       │
│ (Server URL,    │◄────────│ (Template, Diagram   │
│  Validierung)   │         │  Type, Output Format)│
└─────────────────┘         └──────────────────────┘
                                   │
                          Template Rendering
                          (Jinja2 + Entity Tracking)
                                   │
                              Hash Check
                                   │
                      ┌────────────┴────────────┐
                      │ Cache Hit               │ Cache Miss
                      │ → Image from .storage   │ → POST to Kroki API
                      └─────────────────────────┘
                                                    │
                                              Save image
                                              + Update cache
```

### Hybrid Configuration Pattern

- **Config Flow (UI):** Manages Kroki server connections. Each Config Entry = one server. Multiple entries are allowed (e.g., one local, one remote).
- **YAML Platform Config:** Defines the individual Image entities. Templates are complex and better suited for YAML than UI forms.
- The Image platform reads the first available Config Entry to determine the server URL, falling back to `https://kroki.io`.

### Template Rendering Flow

1. Entity is created with a Jinja2 template string
2. `async_track_template_result` registers listeners on all entities referenced in the template
3. When a referenced entity changes, the template is re-rendered
4. SHA256 hash of the rendered string is computed
5. Cache lookup:
   - **Hit:** Load image from `.storage/kroki/` → done
   - **Miss:** POST to Kroki API → save image → update cache
6. `self.async_write_ha_state()` is called → Image entity updates in frontend

### Kroki API Usage

The integration uses the **POST API** (no encoding needed):

```
POST /{diagram_type}/{output_format}
Content-Type: text/plain
Body: <diagram source>
```

Health checks use `GET /health`.

## File Structure

```
custom_components/kroki/
├── __init__.py           # async_setup (reload service), async_setup_entry/async_unload_entry
├── manifest.json         # Integration metadata, config_flow: true, integration_type: service
├── const.py              # DOMAIN, config keys, defaults, content type map, 28 diagram types
├── config_flow.py        # Server URL input + health check validation
├── image.py              # PLATFORM_SCHEMA, KrokiImageEntity (template tracking, rendering, caching)
├── kroki_client.py       # KrokiClient (async_health_check, async_render_diagram)
├── cache.py              # KrokiCache (LRU file cache with JSON metadata)
├── strings.json          # UI texts for config flow + reload service
└── services.yaml         # kroki.reload service definition
```

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Entity platform | Image (not Camera) | Lighter weight, modern HA platform (since 2023.7) |
| Template system | HA native Jinja2 | Consistent with rest of HA, supports `states()`, `is_state()`, etc. |
| Update trigger | Automatic entity tracking | `async_track_template_result` detects referenced entities and re-renders on change |
| Config approach | Hybrid (UI + YAML) | UI for server connection, YAML for templates (too complex for UI) |
| Cache location | `.storage/kroki/` | Persistent across restarts |
| Cache strategy | LRU with limit (default: 50) | Prevents unbounded disk usage |
| API method | POST (plain text) | No encoding/compression needed unlike GET |
| Output formats | SVG and PNG (per entity) | Configurable, SVG default |
| Error handling | Error placeholder SVG | Always shows something, error details in entity attribute |
| Server default | `https://kroki.io` | Official public instance, overridable with self-hosted |
| Reload | `kroki.reload` service | Developer Tools → YAML → "Kroki image entities", no restart needed |
| Multiple servers | Multiple Config Entries | Each entry = one server, platform uses the first one |

## Coding Conventions

- All async methods prefixed with `async_`
- HA-style logging: `_LOGGER = logging.getLogger(__name__)` with lazy formatting
- Type hints on all public methods
- Use `async_get_clientsession(hass)` for HTTP (shared aiohttp session)
- Constants in `const.py`, never hardcoded
- Entity unique IDs: `kroki_{slugified_name}` by default, overridable via `unique_id` in YAML
- Entity ID: overridable via `default_entity_id` in YAML (sets `image.{slugified_value}`)

## Dependencies

- No external pip requirements (uses HA's built-in `aiohttp`, `voluptuous`, `jinja2`)
- Minimum HA version: 2024.7.0 (for Image platform stability)
- Dev dependencies: `pytest-homeassistant-custom-component`, `ruff`, `pre-commit`

## Build

The project uses a `Makefile` for all development tasks. Run `make help` for available targets.

## Testing

Tests live in `tests/` and use `pytest-homeassistant-custom-component`.

```bash
make test            # Run all tests
make test-verbose    # Run with verbose output
make lint            # Run ruff linter
make format          # Auto-format and fix lint issues
make check           # CI-style check (no changes)
make validate        # Hassfest + HACS validation (Docker)
```

### Test structure

```
tests/
├── __init__.py
├── conftest.py            # Shared fixtures (hass_config_dir, cache clearing, mock clients)
├── test_config_flow.py    # Config flow, reconfigure, options flow (9 tests)
├── test_init.py           # Setup/unload entry, reload service (4 tests)
├── test_kroki_client.py   # Health check, render diagram, error handling (15 tests)
├── test_cache.py          # LRU cache init, put/get, eviction, clear (18 tests)
└── test_image.py          # Entity init, unique_id, template tracking, rendering, platform setup (46 tests)
```

### Test infrastructure notes

- `conftest.py` provides a `hass_config_dir` fixture pointing to the project root so HA discovers `custom_components/kroki/`
- An autouse `clear_custom_components_cache` fixture clears `DATA_CUSTOM_COMPONENTS` before each test (the test helper caches an empty dict during bootstrap)
- Tests calling `_async_update_image` directly must mock `async_write_ha_state` (entity is not fully registered with HA)
- Config flow tests use `mock_setup_entry` to skip real `async_setup_entry`, so `hass.data[DOMAIN]` is not initialized during those tests
