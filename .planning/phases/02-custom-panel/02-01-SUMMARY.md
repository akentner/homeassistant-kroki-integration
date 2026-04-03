---
phase: 02-custom-panel
plan: "01"
subsystem: panel-backend
tags: [panel, websocket, sidebar, static-files]
dependency_graph:
  requires: []
  provides: [panel-registration, ws-render, ws-get-entities]
  affects: [custom_components/kroki/__init__.py]
tech_stack:
  added: [panel_custom, websocket_api]
  patterns: [static-path-serving, websocket-command-handlers]
key_files:
  created:
    - custom_components/kroki/panel.py
    - custom_components/kroki/ws_api.py
    - custom_components/kroki/www/.gitkeep
  modified:
    - custom_components/kroki/__init__.py
    - tests/test_init.py
decisions:
  - "panel_custom not added to manifest.json dependencies — it's a built-in HA component, formal dependency declaration causes frontend/hass_frontend to be required in test env"
  - "ws_get_entities uses @callback (sync), ws_render uses @websocket_api.async_response (async) — matching HA WebSocket API contract"
metrics:
  duration: "3m 51s"
  completed: "2026-04-02"
  tasks_completed: 3
  files_modified: 5
---

# Phase 02 Plan 01: Panel Backend Registration Summary

**One-liner:** Kroki sidebar panel registered via `panel_custom` with `/kroki_static` static path, plus two WebSocket commands (`kroki/render` for live preview, `kroki/get_entities` for entity browser).

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | `panel.py` — Register sidebar panel with static path | `e62c7d1` |
| 2 | `ws_api.py` — WebSocket commands for render + entities | `a489148` |
| 3 | Wire panel + ws_api into `__init__.py` `async_setup` | `eba939f` |

## What Was Built

### panel.py
- `async_setup_panel(hass)` registers static path `/kroki_static → www/` directory
- Registers `kroki-panel` custom panel in HA sidebar: title "Kroki Diagrams", icon `mdi:chart-tree`
- `cache_headers=False` to avoid caching issues during development
- `www/.gitkeep` tracks the empty directory in git (JS file added by plan 02)

### ws_api.py
- `kroki/render` WebSocket command: async, validates diagram_type/output_format, picks first available Kroki server (or by `entry_id`), calls `client.render()`, returns base64 data URL
- `kroki/get_entities` WebSocket command: sync callback, returns sorted list of all HA entity IDs and names
- `async_setup_ws_api(hass)` registers both commands

### __init__.py
- `async_setup` now calls `await async_setup_panel(hass)` and `async_setup_ws_api(hass)` after reload service setup

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `panel_custom` removed from `manifest.json` dependencies**
- **Found during:** Task 1 verification (tests broke in Task 3 execution)
- **Issue:** Adding `panel_custom` to `manifest.json` `dependencies` causes HA to formally set it up, which pulls in `frontend` → `hass_frontend` module not installed in test env. All `test_init.py` tests failed.
- **Fix:** Removed `panel_custom` from manifest dependencies. It's a built-in HA component always available via `from homeassistant.components import panel_custom` — no formal dependency declaration needed. Added `mock_panel_setup` autouse fixture to `test_init.py` to mock `async_setup_panel` and `async_setup_ws_api` during unit tests.
- **Files modified:** `custom_components/kroki/manifest.json`, `tests/test_init.py`
- **Commit:** `eba939f`

## Verification Results

```
All imports OK
All ruff checks passed
104 tests passed (0 failures)
```

## Known Stubs

None — `panel.py` and `ws_api.py` are fully wired. The `www/` directory is intentionally empty; `kroki-panel.js` is created by plan 02.

## Self-Check: PASSED

- `custom_components/kroki/panel.py` ✓ exists
- `custom_components/kroki/ws_api.py` ✓ exists
- `custom_components/kroki/www/.gitkeep` ✓ exists
- Commits `e62c7d1`, `a489148`, `eba939f` ✓ exist
