---
phase: 02-custom-panel
plan: "02"
subsystem: frontend
tags: [lit, webcomponent, panel, frontend, javascript]
dependency_graph:
  requires: [02-01]
  provides: [kroki-panel-js]
  affects: [panel-registration]
tech_stack:
  added: [LitElement CDN, ES modules]
  patterns: [Shadow DOM, LitElement reactive properties, WebSocket messaging]
key_files:
  created:
    - custom_components/kroki/www/kroki-panel.js
  modified: []
decisions:
  - "Import LitElement from CDN (jsdelivr/lit@3) rather than HA bundle — HA's bundled lit not reliably exported globally"
  - "Vanilla ES module with no build step — textarea for code editing (not CodeMirror per MVP decision)"
  - "Hardcoded DIAGRAM_TYPES array in JS (not fetched from backend) — simpler, const.py is source of truth"
metrics:
  duration: "2m"
  completed: "2026-04-02"
  tasks: 1
  files: 1
---

# Phase 02 Plan 02: Kroki Panel LitElement Webcomponent Summary

## One-liner

Vanilla LitElement ES module defining `<kroki-panel>` with split-pane editor/preview, 28-type dropdown, and entity browser that calls `kroki/render` and `kroki/get_entities` WebSocket commands.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | kroki-panel.js — LitElement panel with split pane, editor, preview, entity browser | 65dfd0b | custom_components/kroki/www/kroki-panel.js |

## What Was Built

**`custom_components/kroki/www/kroki-panel.js`** — A complete LitElement webcomponent for the HA Kroki panel:

- **Split-pane layout**: Editor (textarea, monospace, dark theme) on left, diagram preview (`<img>` with data URL) on right, entity browser on far right
- **Diagram type selector**: `<select>` dropdown populated from 28 hardcoded `DIAGRAM_TYPES` matching `const.py`
- **Output format selector**: SVG / PNG toggle
- **Render button**: Calls `kroki/render` WebSocket command, displays result or error message
- **Entity browser**: Filterable list of HA entities loaded via `kroki/get_entities`; clicking an entity inserts `{{ states('entity_id') }}` template at cursor position
- **Reactive LitElement**: All state tracked as `static properties` with `{state: true}`, renders efficiently via shadow DOM

## Verification Results

All 13 checks passed:
- ✅ ES module (starts with import)
- ✅ customElements.define("kroki-panel")
- ✅ kroki/render WebSocket call
- ✅ kroki/get_entities WebSocket call
- ✅ DIAGRAM_TYPES array (28 types)
- ✅ Split-pane layout (.main)
- ✅ Entity browser (.entity-browser)
- ✅ _insertEntity method (cursor-aware template insertion)
- ✅ _renderPreview method (async, loading state, error handling)
- ✅ _loadEntities method (async, fails gracefully)
- ✅ KrokiPanel extends LitElement
- ✅ static properties declaration
- ✅ static styles (CSS custom properties for HA theming)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — the webcomponent is fully functional. It relies on the `kroki/render` and `kroki/get_entities` WebSocket handlers from Plan 02-01 being registered.

## Self-Check: PASSED
