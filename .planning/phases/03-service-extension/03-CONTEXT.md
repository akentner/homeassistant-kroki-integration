# Phase 3: Service Extension - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers `kroki.force_render` — a HA service action that triggers an immediate
re-render of any Kroki diagram entity, bypassing the hash-based dedup cache and disk cache.
Works on both YAML-configured and GUI-configured (subentry) diagram entities.

**In scope:** Service registration in `async_setup` (`__init__.py`), HA ServiceTarget schema
(entity/device/area selector), entity method for full cache wipe + re-render trigger,
`services.yaml` / `strings.json` service description, tests.

**Out of scope:** Cache invalidation across multiple entities in bulk (beyond ServiceTarget
targeting), migration of YAML entities, any new entity fields or config flow changes.

</domain>

<decisions>
## Implementation Decisions

### Service Target

- **D-01:** `kroki.force_render` uses the full HA ServiceTarget selector (entity_id,
  device_id, area_id). This aligns with the HA v2 service schema — the DevTools "Services"
  tab shows an entity picker widget automatically. Schema registered with
  `vol.Schema({vol.Optional("entity_id"): cv.entity_ids, ...})` or the HA
  `cv.make_entity_service_schema({})` pattern for entity services.
- **D-02:** The service works on both YAML-configured and GUI-configured (subentry) diagram
  entities. Both paths produce `KrokiImageEntity` instances — no distinction needed in the
  handler.

### Cache Bypass Depth

- **D-03:** `force_render` performs a **full wipe** before re-rendering:
  1. `self._current_hash = None` — clears in-memory hash dedup
  2. `self._cache.evict(hash)` (or equivalent) — removes the disk cache entry for the
     entity's current hash (if any)
  3. `self._current_image = None` — clears in-memory image bytes so entity shows no image
     while re-rendering
  4. Then calls `self._unsub_track.async_refresh()` to trigger a fresh template evaluation
     and re-render cycle.
- **D-04:** The disk cache eviction should only run if `self._current_hash` is not None
  (i.e., there is a known cache key to evict). Silent no-op if the entity has never rendered.

### Service Registration

- **D-05:** The service is registered in `async_setup` in `__init__.py`, alongside the
  existing `async_setup_reload_service` call. This ensures the service exists as soon as the
  integration loads, regardless of whether any config entries are set up.
- **D-06:** The handler resolves target entities via
  `hass.data[DOMAIN]` or the HA entity platform helpers (e.g., `entity_component` or
  `async_get_platforms`). Use `hass.services.async_register` with a `vol.Schema` for the
  service definition, or use the entity-service pattern via `EntityPlatform.async_call_action_from_service`.

### Feedback & Observability

- **D-07:** Fire-and-forget: the service handler schedules the re-render as an
  `hass.async_create_task(entity._async_force_render())` and returns immediately.
- **D-08:** On call, log at DEBUG level: `"force_render called for %s", entity.entity_id`.
- **D-09:** If a targeted entity_id does not exist or is not a `KrokiImageEntity`, log a
  WARNING and skip silently — do not raise `ServiceValidationError`. This matches HA
  convention where service calls on non-matching entities are no-ops.
- **D-10:** Render errors after force_render follow the existing error path: error SVG is
  shown and `_error` extra state attribute is set on the entity.

### the Agent's Discretion

- Whether to implement via `EntityPlatform.async_call_action_from_service` (HA's built-in
  entity service routing) or manual entity lookup — researcher/planner should determine
  which pattern is idiomatic for HA 2024.7+.
- `services.yaml` description wording and example automation YAML.
- Whether `_async_force_render` is a new method on `KrokiImageEntity` or inline logic in the
  service handler.
- Minor version bump for `config_flow.py` (if needed) — follow HA conventions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing integration code (modify)
- `custom_components/kroki/__init__.py` — Add `kroki.force_render` service registration in `async_setup`
- `custom_components/kroki/image.py` — Add force-render method to `KrokiImageEntity` (full cache wipe + re-render trigger)
- `custom_components/kroki/cache.py` — Check if `KrokiCache` exposes an evict/delete method; add one if not
- `custom_components/kroki/const.py` — Add `SERVICE_FORCE_RENDER` constant

### New files
- `custom_components/kroki/services.yaml` — HA service description (required for DevTools display)
- Optionally: `custom_components/kroki/strings.json` service section (if not already present)

### Requirements
- `.planning/REQUIREMENTS.md` — SVC-01: `kroki.force_render` triggers re-render of a named entity

### Codebase maps
- `.planning/codebase/ARCHITECTURE.md` — Data flow and render path (§ Data Flow)
- `.planning/codebase/CONVENTIONS.md` — Service registration patterns, HA-specific patterns

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `KrokiImageEntity._async_update_image(rendered_source)` — core render method; force_render
  must bypass the `content_hash == self._current_hash` guard at line 306 of `image.py`
- `KrokiImageEntity._unsub_track.async_refresh()` — triggers a fresh template evaluation;
  this is the correct way to re-initiate a render cycle (used in `async_added_to_hass`)
- `KrokiCache` — disk cache; check whether it has an evict/remove-by-key method (not visible
  in ARCHITECTURE.md — read `cache.py` directly before planning)
- `async_setup_reload_service` — already imported and called in `async_setup`; force_render
  service follows the same registration pattern

### Established Patterns
- Service registration: `async_setup_reload_service(hass, DOMAIN, PLATFORMS)` in `async_setup`
- Entity method naming: `_async_*` prefix for private async entity methods
- Error logging: `_LOGGER.error(...)` for failures, `_LOGGER.debug(...)` for cache hits
- Task scheduling: `self.hass.async_create_task(self._async_update_image(str(result)))` in
  template callback — same pattern applies for force_render dispatch

### Integration Points
- `__init__.py:async_setup` → add `hass.services.async_register(DOMAIN, SERVICE_FORCE_RENDER, handler, schema)` (or entity service equivalent)
- `image.py:KrokiImageEntity` → add `async_force_render()` (or `_async_force_render()`) method
- `cache.py:KrokiCache` → may need `evict(key: str)` method if not already present

</code_context>

<specifics>
## Specific Ideas

- The ServiceTarget selector approach means the service schema includes both `entity_id` and
  target fields, giving users the entity picker widget in Developer Tools > Services.
- "Full wipe" sequence: reset `_current_hash`, evict disk cache key, clear `_current_image`,
  then call `_unsub_track.async_refresh()` to kick off the normal render pipeline.
- Both YAML and GUI entities are valid targets — no entity_id prefix or attribute filter
  needed in the handler.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-service-extension*
*Context gathered: 2026-04-02*
