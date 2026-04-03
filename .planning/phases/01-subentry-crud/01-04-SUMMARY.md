---
phase: 01-subentry-crud
plan: "04"
subsystem: tests
tags: [tests, config-flow, subentry, image-platform, coexistence]
dependency_graph:
  requires: [01-01, 01-02, 01-03]
  provides: [test-coverage-subentry-crud, test-coverage-async-setup-entry]
  affects: []
tech_stack:
  added: []
  patterns:
    - hass.config_entries.subentries.async_init((entry_id, subentry_type), context) for add flow
    - MockConfigEntry(subentries_data=(ConfigSubentryDataWithId(...),)) for test setup
    - ConfigSubentry as real fixture object (not MagicMock) for from_subentry tests
    - pytest.raises(InvalidData) pattern for TemplateSelector schema-level validation errors
key_files:
  created: []
  modified:
    - tests/test_config_flow.py
    - tests/test_image.py
    - tests/conftest.py
decisions:
  - TemplateSelector validates template syntax at schema level via cv.template/ensure_valid — duplicate ensure_valid() in async_step_user handler is dead code; test captures schema-level InvalidData with schema_errors["diagram_source"]
  - mock_config_subentry uses real ConfigSubentry (not MagicMock) to exercise actual subentry attribute access
  - async_add_entities is a sync callback (AddConfigEntryEntitiesCallback returns None); test mock must be regular def, not async def
  - MockConfigEntry.subentries_data accepts ConfigSubentryDataWithId tuples for stable subentry_id in tests
metrics:
  duration: "7m 39s"
  completed: "2026-04-01"
  tasks_completed: 3
  files_modified: 3
---

# Phase 01 Plan 04: Subentry CRUD Tests Summary

Finalized Phase 01 by adding comprehensive test coverage for all subentry flows and
async_setup_entry entity creation, proving that GUI and YAML entities coexist with
non-colliding unique_ids and that the full test suite passes (104 tests, 0 failures).

## What Was Built

### Task 1: Subentry flow tests in test_config_flow.py (+4 tests)

- `test_subentry_add_flow_success` — verifies subentry created with correct title/data via `hass.config_entries.subentries.async_init((entry_id, "diagram"), context=SOURCE_USER)`
- `test_subentry_add_flow_invalid_template` — verifies `TemplateSelector` schema-level validation raises `InvalidData` with `schema_errors["diagram_source"]` for invalid Jinja2
- `test_subentry_add_flow_valid_template_nonexistent_entity` — verifies syntactically valid templates with non-existent entity refs are accepted (D-03)
- `test_subentry_reconfigure_flow` — verifies reconfigure updates title/data and subentry_id remains unchanged (D-08, Pitfall 5)

Helper added: `_create_server_entry()` reduces boilerplate across subentry tests.

### Task 2: async_setup_entry and from_subentry tests (+6 tests, +1 fixture)

**conftest.py**: Added `mock_config_subentry` fixture returning a real `ConfigSubentry` with a stable ULID subentry_id.

**TestAsyncSetupEntry** (3 tests):
- `test_async_setup_entry_creates_entities_for_subentries` — one entity per diagram subentry, correct unique_id/name/type
- `test_async_setup_entry_skips_non_diagram_subentries` — non-diagram subentry types skipped
- `test_async_setup_entry_no_subentries_creates_no_entities` — empty entry creates no entities

**TestFromSubentry** (3 tests):
- `test_from_subentry_unique_id_is_subentry_id` — unique_id = subentry_id, not name-derived (Pitfall 1)
- `test_from_subentry_and_yaml_unique_ids_do_not_collide` — "Network" GUI entity → ULID; "Network" YAML entity → "kroki_network"
- `test_from_subentry_server_default_format_resolved` — effective_output_format parameter used correctly

### Task 3: Full suite verification

104 tests, 0 failures. ruff check and ruff format --check both pass. All symbols importable. strings.json valid.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TemplateSelector validates at schema level, not handler level**

- **Found during:** Task 1
- **Issue:** `test_subentry_add_flow_invalid_template` expected `result["type"] is FlowResultType.FORM` with `result["errors"]["diagram_source"] == "invalid_template"`. But `TemplateSelector()` calls `cv.template` which calls `Template.ensure_valid()` at schema validation time. HA raises `InvalidData` (not a form result) before `async_step_user` is even called. The `ensure_valid()` check in the handler is dead code.
- **Fix:** Updated test to use `pytest.raises(InvalidData)` and verify `exc_info.value.schema_errors["diagram_source"]`. Test now accurately reflects actual integration behavior.
- **Files modified:** `tests/test_config_flow.py`
- **Commit:** 96d992a

**2. [Rule 1 - Bug] async_add_entities is sync, not async**

- **Found during:** Task 2
- **Issue:** `async_setup_entry` calls `async_add_entities([entity], config_subentry_id=...)` synchronously (no await). Test mock defined as `async def mock_add_entities(...)` caused "coroutine was never awaited" warning and empty `entities_added` list.
- **Fix:** Changed mock to `def mock_add_entities(entities, **kwargs)` (regular function, matching `AddConfigEntryEntitiesCallback` signature returning `None`).
- **Files modified:** `tests/test_image.py`
- **Commit:** e829dc3

**3. [Rule 2 - Missing] `entry.start_subentry_reconfigure_flow` not available on plain ConfigEntry**

- **Found during:** Task 1
- **Issue:** `start_subentry_reconfigure_flow` is a method on `MockConfigEntry`, not on the `ConfigEntry` object returned by `hass.config_entries.flow.async_configure`. Tests using `_create_server_entry()` get a plain `ConfigEntry`.
- **Fix:** Used `hass.config_entries.subentries.async_init((entry_id, "diagram"), context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id})` directly, which is what `start_subentry_reconfigure_flow` calls internally.
- **Files modified:** `tests/test_config_flow.py`
- **Commit:** 96d992a

## Test Coverage Summary

| File | New Tests | Previous Tests | Total |
|------|-----------|----------------|-------|
| test_config_flow.py | 4 | 9 | 13 |
| test_image.py | 6 | 48 | 54 |
| conftest.py | 1 fixture | 3 fixtures | 4 fixtures |
| All test files | 10 | 94 | 104 |

## Known Stubs

None — all new tests exercise real implementations with minimal mocking.

## Self-Check: PASSED
