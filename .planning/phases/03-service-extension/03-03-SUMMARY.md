# 03-03 Summary: Tests — KrokiCache.evict(), async_force_render(), Service Dispatch

## Status: COMPLETE

## What was done

### Task 1: KrokiCache.evict() tests (test_cache.py)
Added 3 new test functions after `TestCacheClear`:

- `test_evict_removes_entry`: puts an entry, evicts it, asserts `get()` returns None and disk file is gone
- `test_evict_unknown_key_is_noop`: evicting an unknown hash does not raise, leaves existing entry intact
- `test_evict_missing_file_still_removes_metadata`: manually deletes disk file, then evicts — should not raise, metadata removed

### Task 2: KrokiImageEntity.async_force_render() tests (test_image.py)
Added 3 new async test functions at end of file (using `mock_kroki_client` from conftest.py):

- `test_force_render_clears_state_and_triggers_refresh`: simulates rendered state with seeded cache, verifies hash/image cleared, cache evicted, refresh called
- `test_force_render_noop_evict_when_no_hash`: entity never rendered (_current_hash=None), verifies no eviction but refresh still triggered (D-04)
- `test_force_render_does_nothing_if_no_tracker`: entity not added to hass (_unsub_track=None), verifies no exception raised

### Task 3: kroki.force_render service tests (test_init.py)
Added 3 new async test functions at end of file:

- `test_force_render_service_registered`: verifies `hass.services.has_service(DOMAIN, "force_render")` after integration loads
- `test_force_render_service_calls_entity_method`: injects mock KrokiImageEntity via `entity_components`, calls service, asserts `async_force_render()` was called once
- `test_force_render_service_unknown_entity_logs_warning`: mock component returns None for entity lookup, verifies WARNING log contains "force_render" and entity_id (D-09)

## Verification

- `make test`: 121 passed (9 new tests, no regressions)
- `make lint`: all checks passed

## SVC-01 Coverage

All acceptance criteria verified:
- Service registered: `test_force_render_service_registered`
- Dispatches to entity: `test_force_render_service_calls_entity_method`
- Skips unknown entities: `test_force_render_service_unknown_entity_logs_warning`
- Cache eviction: `test_evict_removes_entry`, `test_evict_missing_file_still_removes_metadata`
- Entity wipe cycle: `test_force_render_clears_state_and_triggers_refresh`
- D-04 no-op: `test_force_render_noop_evict_when_no_hash`
- Safe without tracker: `test_force_render_does_nothing_if_no_tracker`
