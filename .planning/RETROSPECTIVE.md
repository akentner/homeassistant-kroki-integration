# Retrospective

Living retrospective — one section per milestone.

---

## Milestone: v2.0 — GUI Entity Management

**Shipped:** 2026-04-03
**Phases:** 3 | **Plans:** 10 | **Tests:** 121 passing

### What Was Built

- Config Subentries for diagram entity CRUD (create, edit, delete) via HA GUI
- Dual-path image platform: `async_setup_entry` (GUI) + `async_setup_platform` (YAML) coexist
- Custom sidebar panel: LitElement webcomponent with split-pane editor and live WebSocket preview
- `kroki.force_render` service with cache eviction

### What Worked

- **Subentry pattern was the right HA abstraction** — stable `subentry_id` as `unique_id` cleanly solved entity registry collisions from day one
- **LitElement without build tooling** — vanilla textarea + CDN LitElement delivered a working MVP panel without adding webpack/rollup complexity
- **Phased execution kept scope tight** — Panel stayed clearly in Phase 2, service in Phase 3; no feature creep between phases
- **Tests caught real bugs** — TemplateSelector schema-level validation behavior, `@async_response` call pattern, `hass.http = None` in tests — all caught before merging

### What Was Inefficient

- **ws_api.py bug not caught by Phase 2 tests** — mocking `KrokiClient` in `test_panel.py` masked the wrong method name (`client.render` → `client.async_render_diagram`) and arg order. Required a post-phase audit to surface.
- **Phases 1 and 3 have no VERIFICATION.md** — formal verification step was skipped; implementation is clearly present but the process gap means no formal audit trail
- **gsd-tools `summary-extract` failed** — SUMMARY.md files didn't match expected `one_liner` field format; MILESTONES.md required manual accomplishment entry

### Patterns Established

- `async_add_entities` is a sync callback (`AddConfigEntryEntitiesCallback` returns `None`) — test mocks must be `def`, not `async def`
- `@websocket_api.async_response` wraps async handler as sync `@callback` — tests: call sync + `await hass.async_block_till_done()`
- `hass.http is None` in unit tests — use `patch.object(hass, "http", mock_http)` not `patch.object(hass.http, ...)`
- `panel_custom` must NOT be in `manifest.json` dependencies — built-in HA component, formal dep causes test failures

### Key Lessons

- **Mock at the boundary, not inside it** — mocking `KrokiClient` in WebSocket API tests hides API contract bugs. At minimum one integration-level test without mocking the client boundary is worth it.
- **VERIFICATION.md has real value** — even if implementation is "obviously correct", formal verification catches subtle integration issues (PANEL-04 is the proof).

---

## Cross-Milestone Trends

| Metric | v2.0 |
|--------|------|
| Phases | 3 |
| Plans | 10 |
| Tests added | +27 (94 → 121) |
| Timeline | 6 days |
| Critical bugs found in audit | 1 (PANEL-04) |
