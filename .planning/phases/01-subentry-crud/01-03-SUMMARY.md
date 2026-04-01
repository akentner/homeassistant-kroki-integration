---
phase: 01-subentry-crud
plan: 03
subsystem: image-platform
tags: [async-setup-entry, from-subentry, subentry-crud, image-platform, dual-path]
dependency_graph:
  requires: [platform-forwarding, shared-client-cache-per-entry]
  provides: [gui-entity-setup, from-subentry-factory, dual-path-image-platform]
  affects: [entity-registry, template-tracking, yaml-entity-coexistence]
tech_stack:
  added: []
  patterns: [async_setup_entry-subentry-iteration, from_subentry-classmethod, config_subentry_id-linkage, hass.data-cache-reuse]
key_files:
  created: []
  modified:
    - custom_components/kroki/image.py
decisions:
  - "async_add_entities called per-entity with config_subentry_id=subentry.subentry_id to link entities to their subentry in the HA entity registry"
  - "from_subentry uses unique_id=subentry.subentry_id (stable ULID) — never derived from name, preventing entity registry collisions with YAML entities"
  - "async_setup_platform updated to reuse hass.data client/cache when available, falling back to creating new instances if not set"
metrics:
  duration_seconds: 169
  completed_date: "2026-04-02T00:53:42Z"
  tasks_completed: 1
  files_modified: 1
---

# Phase 01 Plan 03: async_setup_entry + from_subentry Summary

**One-liner:** Wired GUI subentry diagrams to HA image platform via `async_setup_entry` + `KrokiImageEntity.from_subentry` with stable ULID unique_ids and shared cache reuse.

## What Was Built

- **`custom_components/kroki/image.py`** — Three targeted additions:
  1. **`async_setup_entry`** at module level: iterates `config_entry.subentries.values()`, filters by `subentry_type == "diagram"`, resolves effective output format (subentry-specific or parent entry default), creates `KrokiImageEntity` via `from_subentry`, and calls `async_add_entities([entity], config_subentry_id=subentry.subentry_id)` to link each entity to its subentry in HA's entity registry.
  2. **`KrokiImageEntity.from_subentry`** classmethod: creates entity from subentry data with `unique_id=subentry.subentry_id` (stable ULID per D-08/Pitfall 1), wraps raw diagram source string in a `Template` object matching the YAML path behavior.
  3. **`async_setup_platform` update**: reuses shared `client`/`cache` from `hass.data[DOMAIN][entry_id]` when available (D-11), falls back to creating new instances if not yet initialized.
  - Added `ConfigSubentry` and `AddConfigEntryEntitiesCallback` imports.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| Task 1: async_setup_entry + from_subentry + shared cache reuse | `903c72c` | `custom_components/kroki/image.py` |

## Verification

All 94 tests pass (`pytest tests/ -v`):
- `tests/test_image.py` — all 48 tests pass (YAML path unchanged, all existing behaviors preserved)
- `tests/test_init.py` — 4 tests pass (no regression)
- `tests/test_config_flow.py`, `tests/test_cache.py`, `tests/test_kroki_client.py` — all pass
- `ruff check custom_components/kroki/image.py` — all checks passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Quoted return type annotation in from_subentry**
- **Found during:** Task 1 verification (ruff check)
- **Issue:** `-> "KrokiImageEntity":` triggered ruff UP037 (remove quotes from type annotation). With `from __future__ import annotations` in the file, the forward reference quotes are unnecessary.
- **Fix:** Removed quotes: `-> KrokiImageEntity:`
- **Files modified:** `custom_components/kroki/image.py`
- **Commit:** `903c72c` (fixed inline before commit)

### Implementation Notes

- `AddConfigEntryEntitiesCallback` confirmed to accept `config_subentry_id` keyword argument (verified against installed HA `entity_platform.py`). Used per-entity call pattern (`async_add_entities([entity], config_subentry_id=subentry.subentry_id)`) as verified in HA source.
- Plan noted uncertainty about whether `config_subentry_id` param exists — confirmed it does.

## Known Stubs

None. The implementation is fully functional. GUI subentry entities will appear as `image.*` entities in HA when subentries exist in the config entry. Template tracking is active via the unchanged `async_added_to_hass` path.

## Self-Check: PASSED
