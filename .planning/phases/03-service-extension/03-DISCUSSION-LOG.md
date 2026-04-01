# Phase 3: Service Extension - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 03-service-extension
**Areas discussed:** Service target & scope, Cache bypass depth, Service registration location, Feedback & observability

---

## Service Target & Scope

| Option | Description | Selected |
|--------|-------------|----------|
| entity_id field (targeted) | Service takes entity_id as required field — only that entity re-renders. Works on both YAML and GUI diagrams. Standard HA service pattern. | |
| Broadcast all kroki entities | No target field — calling the service re-renders ALL currently loaded kroki diagram entities at once. | |
| Full HA ServiceTarget selector | HA ServiceTarget (targets.entity_id, targets.device_id, targets.area_id) — standard HA v2 service schema with entity picker widget in DevTools. | ✓ |

**User's choice:** Full HA ServiceTarget selector

**Notes:** Works on both YAML and GUI diagram entities (both are KrokiImageEntity instances — no distinction needed).

---

## Cache Bypass Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Reset in-memory hash only | Only reset _current_hash to None — next render still checks disk cache. Fastest path. | |
| Reset hash + evict disk cache | Reset _current_hash AND delete the disk cache entry for that diagram's current hash. Forces an API call. | |
| Full wipe (hash + disk + in-memory image) | Reset _current_hash, delete disk cache entry, AND clear _current_image so entity shows loading state while re-rendering. | ✓ |

**User's choice:** Full wipe (hash + disk + in-memory image)

**Notes:** Forces a completely fresh render including hitting the Kroki API server. Loading state shown during re-render.

---

## Service Registration Location

| Option | Description | Selected |
|--------|-------------|----------|
| async_setup in __init__.py | Register alongside async_setup_reload_service — service exists even with no config entries loaded. | ✓ |
| async_setup_entry (per entry) | Register per config entry — tricky if multiple entries exist (duplicate registration). | |
| image.py (platform level) | Register from image.py async_setup_entry or async_setup_platform. | |

**User's choice:** async_setup in __init__.py

**Notes:** Consistent with existing reload service location. Service available immediately when integration loads.

---

## Feedback & Observability

| Option | Description | Selected |
|--------|-------------|----------|
| Fire-and-forget + log | Service logs DEBUG when called, schedules re-render task, returns immediately. Silent skip (WARNING log) if entity not found. | ✓ |
| Await render + raise on error | Service awaits render completion. Raises ServiceValidationError on failure. | |
| State attribute + fire-and-forget | Updates force_render_requested_at state attribute plus fire-and-forget render. | |

**User's choice:** Fire-and-forget + log

**Notes:** Matches HA service convention. Errors surfaced via entity _error state attribute (existing behavior).

---

## the Agent's Discretion

- Whether to use EntityPlatform.async_call_action_from_service or manual entity lookup
- services.yaml description wording
- Whether `_async_force_render` is a new method or inline logic in the handler
- Minor version bump decisions

## Deferred Ideas

None.
