---
phase: 01-subentry-crud
plan: 01
subsystem: core-integration
tags: [platform-forwarding, config-entry, hass-data, init, tests]
dependency_graph:
  requires: []
  provides: [platform-forwarding, shared-client-cache-per-entry]
  affects: [image-platform-setup, yaml-entity-coexistence]
tech_stack:
  added: []
  patterns: [async_forward_entry_setups, hass.data per entry_id, conditional unload pop]
key_files:
  created: []
  modified:
    - custom_components/kroki/__init__.py
    - custom_components/kroki/config_flow.py
    - tests/test_init.py
decisions:
  - "Patch ConfigEntries.async_forward_entry_setups at class level in tests (not integration level) to avoid AttributeError from missing image.async_setup_entry stub"
  - "async_unload_platforms must also be patched in unload test since it calls the real platform unload path"
metrics:
  duration_seconds: 208
  completed_date: "2026-04-01T22:48:21Z"
  tasks_completed: 2
  files_modified: 3
---

# Phase 01 Plan 01: Platform Forwarding + Shared Client/Cache Storage Summary

**One-liner:** Added `async_forward_entry_setups` + shared `{client, cache}` per config entry to enable GUI-managed image entities via HA's standard platform forwarding pattern.

## What Was Built

- **`__init__.py`** — Rewrote `async_setup_entry` to create a `KrokiClient` + `KrokiCache` per config entry and call `async_forward_entry_setups(entry, PLATFORMS)`. Rewrote `async_unload_entry` to use `async_unload_platforms` with conditional `hass.data` pop only on success.
- **`config_flow.py`** — Bumped `MINOR_VERSION` from 1 to 2 (structural config entry change per HA convention).
- **`tests/test_init.py`** — Updated assertions from value equality (`== {CONF_SERVER_URL: ...}`) to key presence (`"client" in entry_data`, `"cache" in entry_data`). Added `patch(ConfigEntries.async_forward_entry_setups)` and `patch(ConfigEntries.async_unload_platforms)` to isolate `__init__.py` logic from image platform.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| Task 1: Platform forwarding + shared client/cache | `33f72f1` | `__init__.py`, `config_flow.py` |
| Task 2: Update test_init.py | `5e6b30f` | `tests/test_init.py` |

## Verification

All 94 tests pass (`pytest tests/ -v`):
- `tests/test_init.py` — 4 tests pass
- `tests/test_image.py` — all YAML path tests pass (no regression)
- `tests/test_config_flow.py`, `tests/test_cache.py`, `tests/test_kroki_client.py` — all pass

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Patching strategy mismatch for async_forward_entry_setups**
- **Found during:** Task 2
- **Issue:** Plan suggested patching at integration level (`custom_components.kroki.async_forward_entry_setups`) but that module attribute doesn't exist — it's accessed via `hass.config_entries`. Also, `async_unload_platforms` needed to be patched in the unload test as well (plan only mentioned `async_forward_entry_setups`).
- **Fix:** Patched `homeassistant.config_entries.ConfigEntries.async_forward_entry_setups` and `homeassistant.config_entries.ConfigEntries.async_unload_platforms` at the class level. This cleanly isolates `__init__.py` tests from the image platform.
- **Files modified:** `tests/test_init.py`
- **Commit:** `5e6b30f`

## Known Stubs

None. The changes are functional. Note: `image.py` does not yet have `async_setup_entry` — this is intentional and will be addressed in a later plan. The tests correctly patch around this gap.

## Self-Check: PASSED
