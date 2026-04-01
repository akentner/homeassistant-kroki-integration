# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-01)

**Core value:** Kroki diagram entities fully manageable via HA GUI — no YAML editing required
**Current focus:** Phase 1 — Subentry CRUD

## Current Position

Phase: 1 of 3 (Subentry CRUD)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-04-01 — Roadmap created for milestone v2.0

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: none yet
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Pre-roadmap: unique_id for GUI entities = subentry_id (never derived from name — prevents entity registry collisions, Pitfall 1+5)
- Pre-roadmap: async_forward_entry_setups must be added to __init__.py; async_unload_platforms must mirror it
- Pre-roadmap: YAML path (async_setup_platform) stays untouched; dual-path coexistence in image.py
- Pre-roadmap: Panel uses LitElement + textarea (no CodeMirror for MVP); cache_headers=False

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 1: Adding async_forward_entry_setups to __init__.py is a structural change — existing YAML entity tests must pass after this change before proceeding.
- Phase 2: Panel requires custom JS. No build tooling in repo. Vanilla LitElement (already in HA bundle) is the planned approach — confirm before Phase 2 planning.

## Session Continuity

Last session: 2026-04-01
Stopped at: Roadmap created, STATE.md initialized — ready to plan Phase 1
Resume file: None
