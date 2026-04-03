# Kroki Integration — GUI Management

## What This Is

A Home Assistant custom integration that renders Diagram-as-Code markup (GraphViz, Mermaid, PlantUML, 28+ types) via a Kroki server into images served as HA Image entities. Supports full GUI entity management via Config Subentries, Jinja2 template auto-updates, a custom sidebar panel with live preview, and parallel YAML configuration.

## Core Value

Kroki diagram entities are fully manageable via the Home Assistant GUI — no YAML editing required.

## Requirements

### Validated

- ✓ Kroki server connection via Config Flow (UI) — v1.x
- ✓ YAML-based diagram entities with Jinja2 templates — v1.x
- ✓ Automatic re-render on entity state changes — v1.x
- ✓ SHA256-based LRU disk cache for rendered images — v1.x
- ✓ SVG and PNG output — v1.x
- ✓ All 28+ Kroki diagram types supported — v1.x
- ✓ YAML reload without HA restart — v1.x
- ✓ Error placeholder SVG on render failure — v1.x
- ✓ Options Flow for default format and cache size — v1.x
- ✓ Multiple Kroki servers configurable — v1.x
- ✓ Diagram entities created, edited, deleted via HA GUI (Config Subentries) — v2.0
- ✓ Stable `unique_id = subentry_id` — entity_id survives renames — v2.0
- ✓ Jinja2 template support in GUI-created entities with auto-update — v2.0
- ✓ YAML and GUI entities coexist without conflict or migration — v2.0
- ✓ Custom sidebar panel with split-pane editor and live preview — v2.0
- ✓ Entity browser in panel for inserting entity refs into templates — v2.0
- ✓ `kroki.force_render` service for manual re-render with cache eviction — v2.0

### Active

*(No active requirements — planning next milestone)*

### Out of Scope

| Feature | Reason |
|---------|--------|
| Entity-Picker / Autocomplete in Config Flow | HA Config Flow UI does not support custom widgets |
| YAML-to-GUI migration | Coexistence is sufficient; no user request |
| Bidirectional YAML-GUI sync | Maintenance trap, conflicts unavoidable |
| Multiple diagrams per subentry | 1:1 granularity is the correct HA pattern |
| CodeMirror in panel | Vanilla textarea sufficient for MVP; deferred |
| Mobile panel optimization | Desktop-first; deferred to later milestone |

## Context

- **Shipped:** v2.0 — 3 phases, 10 plans, 121 passing tests
- **Codebase:** 1,296 LOC Python (integration) + 2,483 LOC Python (tests)
- **Tech stack:** Python 3.13, Home Assistant Config Subentries, LitElement (vanilla), WebSocket API
- **Distribution:** HACS custom integration
- **Known tech debt:**
  - Phases 1 and 3 have no VERIFICATION.md — implementation is clearly present but not formally verified
  - `hass.data.get("entity_components")` in force_render uses HA-internal dict key — may break on future HA versions
  - Phase 2 tests mock KrokiClient — real client-to-ws-api integration not covered by unit tests

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GUI diagrams as Config Subentries | HA standard for UI-configured entities, auto-persisted | ✓ Good — clean HA pattern, subentry_id provides stable unique_id |
| `unique_id = subentry_id` (never name-derived) | Prevents entity registry collisions, survives renames | ✓ Good — critical correctness property, validated by tests |
| YAML and GUI coexist (dual path in image.py) | Don't break existing YAML users | ✓ Good — zero regressions, 104 → 121 tests all green |
| Panel uses LitElement + textarea (no CodeMirror) | No build tooling in repo, HA LitElement available | ✓ Good — MVP shipped without build step |
| LitElement from CDN (jsdelivr/lit@3) | HA bundled lit not reliably globally exported | ✓ Good — no import issues |
| `@async_response` for ws_render handler | HA WebSocket API contract for async handlers | ✓ Good — required for correct async behavior |
| force_render as closure in async_setup | Idiomatic HA pattern, no class needed | ✓ Good — simple, maintainable |
| Service dispatches via `async_create_task` | Fire-and-forget prevents blocking service handler | ✓ Good — follows D-07 pattern |

## Constraints

- **HA API:** Config Flow UI limited to standard form elements (no code editor widget natively)
- **Compatibility:** YAML mode must continue working unchanged
- **HA Version:** Minimum 2024.7.0 (HACS declaration)
- **Distribution:** HACS — no PyPI packaging required

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-03 after v2.0 milestone — GUI entity management shipped*
