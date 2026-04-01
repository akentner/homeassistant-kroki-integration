---
phase: 02-custom-panel
plan: "03"
subsystem: testing
tags: [tests, websocket, panel, tdd]
dependency_graph:
  requires: [02-01]
  provides: [test coverage for ws_api.py, test coverage for panel.py]
  affects: [tests/test_panel.py]
tech_stack:
  added: []
  patterns: [async_response decorator requires sync call + async_block_till_done, patch.object(hass, "http") for None HTTP component in tests]
key_files:
  created: [tests/test_panel.py]
  modified: []
decisions:
  - "@websocket_api.async_response wraps handler as sync @callback — tests must call sync + await hass.async_block_till_done()"
  - "hass.http is None in unit tests — use patch.object(hass, 'http', mock_http) not patch.object(hass.http, ...)"
metrics:
  duration: 208s
  completed: "2026-04-01T23:31:39Z"
  tasks_completed: 2
  files_modified: 1
---

# Phase 02 Plan 03: WebSocket API and Panel Tests Summary

**One-liner:** Tests for `ws_render` (success, no-server, errors, PNG) and `ws_get_entities` (full/empty) plus panel registration — all 8 tests passing with sync+drain pattern for `@async_response` handlers.

## What Was Built

`tests/test_panel.py` with 8 tests covering:

| Test | Coverage |
|------|----------|
| `test_ws_render_success` | Happy path: SVG data URL with correct base64 content |
| `test_ws_render_no_server` | Error path: `no_server` when `hass.data[DOMAIN]` is empty |
| `test_ws_render_connection_error` | Error path: `connection_error` from `KrokiConnectionError` |
| `test_ws_render_render_error` | Error path: `render_error` from `KrokiRenderError` |
| `test_ws_render_png_format` | PNG output_format reflected in data URL prefix |
| `test_ws_get_entities_returns_all_states` | Returns list with all entity_ids from hass.states |
| `test_ws_get_entities_empty` | Returns `[]` when no states set |
| `test_async_setup_panel_registers` | Panel registered with `frontend_url_path="kroki"` and `webcomponent_name="kroki-panel"` |

## Decisions Made

1. **`@async_response` call pattern**: The `@websocket_api.async_response` decorator transforms the async handler into a sync `@callback` that schedules a background task. Tests must call it without `await` and then `await hass.async_block_till_done()` to flush the task. Plan example used `await ws_render(...)` which was incorrect.

2. **`hass.http` patching**: In unit tests, `hass.http` is `None` (HTTP component not loaded). `patch.object(hass.http, ...)` raises `AttributeError`. Solution: `patch.object(hass, "http", mock_http)` replaces the entire attribute.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ws_render test call pattern incorrect**
- **Found during:** Task 1 (RED phase)
- **Issue:** Plan template used `await ws_render(hass, connection, msg)` but `@async_response` makes `ws_render` a sync `@callback` returning `None`, not a coroutine
- **Fix:** Changed to sync call `ws_render(hass, connection, msg)` + `await hass.async_block_till_done()` pattern
- **Files modified:** `tests/test_panel.py`
- **Commit:** 5263d2f

**2. [Rule 1 - Bug] hass.http is None in tests**
- **Found during:** Task 1 (RED phase)
- **Issue:** `patch.object(hass.http, "async_register_static_paths", ...)` raises `AttributeError: None does not have attribute 'async_register_static_paths'`
- **Fix:** Used `patch.object(hass, "http", mock_http)` where `mock_http` is a `MagicMock` with `async_register_static_paths = AsyncMock()`
- **Files modified:** `tests/test_panel.py`
- **Commit:** 5263d2f

## Full Test Suite Results

- **Before:** 104 passed (pre-plan baseline from 02-01/02-02)
- **After:** 112 passed (8 new tests added)
- **Ruff:** Clean — no lint errors

## Self-Check: PASSED

- ✅ `tests/test_panel.py` — exists
- ✅ Commit `5263d2f` — verified in git log
