# 03-01 Summary: Foundation — Constants, Cache.evict(), Entity Method

## Status: COMPLETE

## What was done

### Task 1: SERVICE_FORCE_RENDER constant (const.py)
Added `SERVICE_FORCE_RENDER = "force_render"` under a new `# Service names` block, after the `DEFAULT_*` constants.

### Task 2: KrokiCache.evict() (cache.py)
Added public `evict(content_hash: str) -> None` method placed between `put()` and the private `_evict()`. Implementation:
- Silent no-op if `content_hash` not in `_metadata`
- Resolves file path from metadata suffix, removes file via `os.remove()` if it exists
- `OSError` logged as WARNING (mirrors private `_evict` pattern), not propagated
- Removes hash from `_metadata` and calls `_save_metadata()`
- Logs DEBUG: `"Evicted cache entry by request: %s"`

### Task 3: KrokiImageEntity.async_force_render() (image.py)
Added public `async async_force_render()` method placed after `async_will_remove_from_hass()` and before `_async_update_image()`. Implementation (per D-03/D-04/D-08):
- Logs DEBUG: `"force_render called for %s"` with entity_id
- Captures `old_hash = self._current_hash`
- Clears `_current_hash = None` and `_current_image = None`
- Calls `self._cache.evict(old_hash)` only if `old_hash is not None` (D-04)
- Calls `self._unsub_track.async_refresh()` only if `_unsub_track is not None`

## Verification

- `make test`: 112 passed (no regressions)
- `make lint`: all checks passed
