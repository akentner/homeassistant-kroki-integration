# Roadmap: Kroki Integration — Milestone v2.0 GUI Entity Management

## Overview

Milestone v2.0 adds full GUI entity management to the existing Kroki integration. Phase 1
delivers the core: diagram entities can be created, edited, and deleted via Config Subentries
in the HA UI, with Jinja2 template support and YAML coexistence. Phase 2 adds a custom
sidebar panel with a split-pane editor and live preview. Phase 3 rounds out the service
surface with a force re-render service action.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Subentry CRUD** - Users can create, edit, and delete diagram entities via the HA GUI using Config Subentries (completed 2026-04-01)
- [x] **Phase 2: Custom Panel** - Sidebar panel with split-pane code editor and live diagram preview (completed 2026-04-01)
- [x] **Phase 3: Service Extension** - `kroki.force_render` service for manual re-render of any diagram entity (completed 2026-04-02)

## Phase Details

### Phase 1: Subentry CRUD
**Goal**: Users can fully manage diagram entities through the Home Assistant GUI — no YAML required
**Depends on**: Nothing (first phase)
**Requirements**: CRUD-01, CRUD-02, CRUD-03, CRUD-04, CRUD-05, CFG-01, CFG-02, CFG-03, CFG-04, TPL-01, TPL-02, YAML-01
**Success Criteria** (what must be TRUE):
  1. User can add a new diagram entity under a Kroki server entry in Settings > Devices & Services, choosing type from a dropdown of all 28+ supported types
  2. User can edit an existing diagram's name, type, source, and output format via a Reconfigure button; the entity_id remains stable across renames
  3. User can delete a diagram subentry and the associated image entity disappears from HA
  4. GUI-created diagrams with Jinja2 templates in the source field auto-update when referenced entity states change
  5. YAML-configured diagrams continue to function unchanged alongside GUI diagrams after a reload
**Plans**: 4 plans
Plans:
- [x] 01-01-PLAN.md — Platform forwarding + shared client/cache in __init__.py
- [x] 01-02-PLAN.md — DiagramSubentryFlowHandler + strings.json
- [x] 01-03-PLAN.md — image.py dual-path: async_setup_entry + from_subentry
- [x] 01-04-PLAN.md — Tests: subentry flows + coexistence + full suite green
**UI hint**: yes

### Phase 2: Custom Panel
**Goal**: Users have a sidebar panel with a code editor and live preview for authoring diagrams
**Depends on**: Phase 1
**Requirements**: PANEL-01, PANEL-02, PANEL-03, PANEL-04, PANEL-05
**Success Criteria** (what must be TRUE):
  1. A "Kroki Diagrams" entry appears in the HA sidebar and the panel loads without errors
  2. User sees a split-pane layout with a code editor (monospace textarea) on one side and a live diagram preview on the other
  3. User can select a diagram type from a dropdown and the preview updates accordingly
  4. User can browse available entity IDs and click to insert them into the editor source
**Plans**: 3 plans
Plans:
- [x] 02-01-PLAN.md — Backend: panel.py + ws_api.py + __init__.py wiring (PANEL-01, PANEL-04)
- [x] 02-02-PLAN.md — Frontend: kroki-panel.js LitElement webcomponent (PANEL-02, PANEL-03, PANEL-05)
- [x] 02-03-PLAN.md — Tests: WebSocket API + panel registration + full suite green
**UI hint**: yes

### Phase 3: Service Extension
**Goal**: Users can trigger a manual re-render of any Kroki diagram entity via a HA service call
**Depends on**: Phase 1
**Requirements**: SVC-01
**Success Criteria** (what must be TRUE):
  1. Calling `kroki.force_render` with a valid entity_id causes that entity to re-render immediately, bypassing the hash-based dedup cache
  2. The service is callable from Developer Tools > Services and from automations
**Plans**: 3 plans
Plans:
- [x] 03-01-PLAN.md — Cache evict method + SERVICE_FORCE_RENDER constant + KrokiImageEntity.async_force_render()
- [x] 03-02-PLAN.md — Register kroki.force_render service in async_setup + services.yaml + strings.json
- [x] 03-03-PLAN.md — Tests: cache evict + entity force_render + service dispatch + full suite green

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Subentry CRUD | 4/4 | Complete | 2026-04-01 |
| 2. Custom Panel | 3/3 | Complete | 2026-04-01 |
| 3. Service Extension | 3/3 | Complete | 2026-04-02 |
