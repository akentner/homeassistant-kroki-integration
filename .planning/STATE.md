---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: milestone
status: verifying
stopped_at: Completed 01-subentry-crud 01-04-PLAN.md — Phase 01 complete
last_updated: "2026-04-01T23:09:30.301Z"
last_activity: 2026-04-01
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 4
  completed_plans: 4
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-01)

**Core value:** Kroki diagram entities fully manageable via HA GUI — no YAML editing required
**Current focus:** Phase 01 — subentry-crud

## Current Position

Phase: 01 (subentry-crud) — EXECUTING
Plan: 4 of 4
Status: Phase complete — ready for verification
Last activity: 2026-04-01

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
| Phase 01-subentry-crud P02 | 2m 27s | 2 tasks | 2 files |
| Phase 01-subentry-crud P01 | 208 | 2 tasks | 3 files |
| Phase 01-subentry-crud P03 | 169 | 1 tasks | 1 files |
| Phase 01-subentry-crud P04 | 7m 39s | 3 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Pre-roadmap: unique_id for GUI entities = subentry_id (never derived from name — prevents entity registry collisions, Pitfall 1+5)
- Pre-roadmap: async_forward_entry_setups must be added to __init__.py; async_unload_platforms must mirror it
- Pre-roadmap: YAML path (async_setup_platform) stays untouched; dual-path coexistence in image.py
- Pre-roadmap: Panel uses LitElement + textarea (no CodeMirror for MVP); cache_headers=False
- [Phase 01-subentry-crud]: Template validation uses Template(source, hass).ensure_valid() — rejects syntax errors, accepts entity-reference templates
- [Phase 01-subentry-crud]: Output format 'Server Default' stores 'server_default' string in subentry data — entity resolves effective format at setup time
- [Phase 01-subentry-crud]: Patch ConfigEntries class-level methods in tests to isolate __init__.py from image platform (no async_setup_entry yet)
- [Phase 01-subentry-crud]: async_add_entities called per-entity with config_subentry_id=subentry.subentry_id to link entities to their subentry in HA entity registry
- [Phase 01-subentry-crud]: from_subentry uses unique_id=subentry.subentry_id (stable ULID) — never derived from name, preventing entity registry collisions with YAML entities (D-08, Pitfall 1)
- [Phase 01-subentry-crud]: TemplateSelector validates template syntax at schema level via cv.template/ensure_valid — duplicate ensure_valid() in async_step_user handler is dead code
- [Phase 01-subentry-crud]: mock_config_subentry uses real ConfigSubentry (not MagicMock) to exercise actual subentry attribute access
- [Phase 01-subentry-crud]: async_add_entities is a sync callback (AddConfigEntryEntitiesCallback returns None); test mock must be regular def, not async def

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 1: Adding async_forward_entry_setups to __init__.py is a structural change — existing YAML entity tests must pass after this change before proceeding.
- Phase 2: Panel requires custom JS. No build tooling in repo. Vanilla LitElement (already in HA bundle) is the planned approach — confirm before Phase 2 planning.

## Session Continuity

Last session: 2026-04-01T23:09:30.285Z
Stopped at: Completed 01-subentry-crud 01-04-PLAN.md — Phase 01 complete
Resume file: None
