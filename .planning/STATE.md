# State

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-01 — Milestone v2.0 started

## Accumulated Context

- Research abgeschlossen: FEATURES.md, ARCHITECTURE.md, PITFALLS.md vorhanden
- Config Subentries (HA 2025.7) sind der richtige Mechanismus für GUI CRUD
- unique_id muss subentry_id sein — niemals vom Namen ableiten (Pitfall 1 + 5)
- async_forward_entry_setups muss in __init__.py ergänzt werden (Pitfall 2)
- Panel: LitElement + textarea (kein CodeMirror für MVP), cache_headers=False (Pitfall 9)
- YAML-Pfad (async_setup_platform) bleibt unverändert
