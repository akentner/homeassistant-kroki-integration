---
phase: 02-custom-panel
verified: 2026-04-02T00:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 2: Custom Panel — Verification Report

**Phase Goal:** Users have a sidebar panel with a code editor and live preview for authoring diagrams
**Verified:** 2026-04-02
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                          | Status     | Evidence                                                                                   |
|----|-----------------------------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------|
| 1  | A Kroki entry appears in the HA sidebar (panel registered)                                     | ✓ VERIFIED | `panel.py:async_setup_panel` calls `panel_custom.async_register_panel` with `frontend_url_path="kroki"`, `sidebar_title="Kroki Diagrams"` |
| 2  | Calling `kroki/render` WebSocket command returns a rendered diagram as a data URL              | ✓ VERIFIED | `ws_api.py:ws_render` fetches from `KrokiClient.render()`, base64-encodes result, returns `data:image/{format};base64,...` |
| 3  | Calling `kroki/get_entities` WebSocket command returns a list of HA entity IDs                 | ✓ VERIFIED | `ws_api.py:ws_get_entities` calls `hass.states.async_all()` and returns sorted `{entity_id, name}` list |
| 4  | `kroki-panel.js` defines a LitElement custom element `<kroki-panel>`                          | ✓ VERIFIED | File ends with `customElements.define("kroki-panel", KrokiPanel)` |
| 5  | The element renders a split-pane layout: editor (textarea) on left, preview (img) on right    | ✓ VERIFIED | CSS classes `.editor-pane`, `.preview-pane`, `.main` (flex layout) present; `<textarea>` in editor pane, `<img>` in preview pane |
| 6  | A diagram-type dropdown populates from the 28 supported types                                  | ✓ VERIFIED | `DIAGRAM_TYPES` array contains exactly 28 entries matching `const.py`; rendered via `DIAGRAM_TYPES.map(t => html\`<option ...>\`)` |
| 7  | The entity browser shows a filterable list; clicking one inserts it into the textarea          | ✓ VERIFIED | `.entity-browser` with filter `<input>`, `_insertEntity(entityId)` inserts `{{ states('...') }}` at cursor |
| 8  | `async_setup_panel` is called during integration setup                                         | ✓ VERIFIED | `__init__.py:async_setup` calls `await async_setup_panel(hass)` at line 32 |
| 9  | The JS file is a valid ES module (no build step required)                                      | ✓ VERIFIED | File starts with `import { LitElement, html, css } from "https://cdn.jsdelivr.net/..."` |
| 10 | All 8 tests in `test_panel.py` pass; full suite green                                          | ✓ VERIFIED | `pytest tests/test_panel.py`: 8 passed; full `pytest tests/`: 112 passed, 0 failures      |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact                                        | Expected                                          | Status     | Details                                                                                    |
|-------------------------------------------------|---------------------------------------------------|------------|--------------------------------------------------------------------------------------------|
| `custom_components/kroki/panel.py`              | Panel registration + static path serving          | ✓ VERIFIED | 29 lines; exports `async_setup_panel`; registers `/kroki_static` static path + panel      |
| `custom_components/kroki/ws_api.py`             | WebSocket API handlers for render + entity browser | ✓ VERIFIED | 68 lines; exports `async_setup_ws_api`, `ws_render`, `ws_get_entities`; full logic         |
| `custom_components/kroki/__init__.py`           | Wires panel + ws_api into `async_setup`           | ✓ VERIFIED | Lines 18-19 import both modules; lines 32-33 call them in `async_setup`                   |
| `custom_components/kroki/www/kroki-panel.js`    | Kroki panel LitElement webcomponent               | ✓ VERIFIED | 265 lines; complete LitElement component with all required features                        |
| `custom_components/kroki/www/.gitkeep`          | Tracks `www/` directory in git                    | ✓ VERIFIED | Directory exists; `kroki-panel.js` present                                                |
| `tests/test_panel.py`                           | Tests for panel registration and WebSocket API    | ✓ VERIFIED | 172 lines; 8 tests — all pass                                                             |

---

### Key Link Verification

| From                                         | To                                    | Via                                                          | Status     | Details                                                                         |
|----------------------------------------------|---------------------------------------|--------------------------------------------------------------|------------|---------------------------------------------------------------------------------|
| `custom_components/kroki/__init__.py`        | `custom_components/kroki/panel.py`    | `await async_setup_panel(hass)` in `async_setup`            | ✓ WIRED    | Line 32: `await async_setup_panel(hass)`                                       |
| `custom_components/kroki/__init__.py`        | `custom_components/kroki/ws_api.py`   | `async_setup_ws_api(hass)` in `async_setup`                 | ✓ WIRED    | Line 33: `async_setup_ws_api(hass)`                                            |
| `custom_components/kroki/ws_api.py`          | `hass.data[DOMAIN]`                   | `kroki client per entry_id lookup`                          | ✓ WIRED    | Line 28: `domain_data = hass.data.get(DOMAIN, {})`; client retrieved from dict |
| `kroki-panel.js`                             | `/api/websocket`                      | `hass.connection.sendMessagePromise({type: 'kroki/render'})` | ✓ WIRED    | Line 222-227 in JS; calls `kroki/render` with `diagram_type`, `source`, `output_format` |
| `kroki-panel.js`                             | `/api/websocket`                      | `hass.connection.sendMessagePromise({type: 'kroki/get_entities'})` | ✓ WIRED | Line 240 in JS; populates `_entities` from response                       |
| `tests/test_panel.py`                        | `custom_components/kroki/ws_api.py`   | Direct function calls with mock hass + connection           | ✓ WIRED    | Lines 10, 45, 66, 83, 99, 121, 135, 148 call `ws_render`/`ws_get_entities`    |

---

### Data-Flow Trace (Level 4)

| Artifact             | Data Variable    | Source                        | Produces Real Data | Status      |
|----------------------|-----------------|-------------------------------|---------------------|-------------|
| `kroki-panel.js`     | `_previewUrl`   | `ws_render` → `KrokiClient.render()` → Kroki HTTP API | Yes — actual HTTP POST to Kroki server | ✓ FLOWING |
| `kroki-panel.js`     | `_entities`     | `ws_get_entities` → `hass.states.async_all()` | Yes — real HA state machine | ✓ FLOWING |
| `kroki-panel.js`     | `_diagramType`  | `DIAGRAM_TYPES` array (hardcoded, 28 entries) | Yes — immutable constant, not a stub | ✓ FLOWING |

---

### Behavioral Spot-Checks

| Behavior                                    | Command                                                                                    | Result              | Status  |
|---------------------------------------------|--------------------------------------------------------------------------------------------|---------------------|---------|
| All imports resolve without error            | `.venv/bin/python -c "from custom_components.kroki.panel import async_setup_panel; ..."` | All imports OK       | ✓ PASS  |
| 8 `test_panel.py` tests pass                 | `.venv/bin/pytest tests/test_panel.py -v`                                                 | 8 passed in 0.73s   | ✓ PASS  |
| Full suite: 112 tests, 0 failures            | `.venv/bin/pytest tests/ -q`                                                              | 112 passed in 5.17s | ✓ PASS  |
| Ruff linting clean                           | `.venv/bin/ruff check panel.py ws_api.py __init__.py`                                    | All checks passed   | ✓ PASS  |
| 28 DIAGRAM_TYPES in kroki-panel.js           | `python3 -c "count DIAGRAM_TYPES"`                                                        | 28 types confirmed  | ✓ PASS  |
| `customElements.define("kroki-panel", ...)` present | `grep customElements.define kroki-panel.js`                                       | Found at line 265   | ✓ PASS  |
| `kroki/render` and `kroki/get_entities` in JS | `grep "kroki/render\|kroki/get_entities" kroki-panel.js`                               | Both found (ll 223, 240) | ✓ PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description                                                                           | Status        | Evidence                                                                          |
|-------------|-------------|---------------------------------------------------------------------------------------|---------------|-----------------------------------------------------------------------------------|
| PANEL-01    | 02-01, 02-03 | Kroki-Sidebar-Panel ist in HA registriert und über die Seitenleiste erreichbar        | ✓ SATISFIED  | `panel.py` registers panel with `frontend_url_path="kroki"`, `sidebar_title="Kroki Diagrams"`; test `test_async_setup_panel_registers` passes |
| PANEL-02    | 02-02       | Panel zeigt Editor (textarea, Monospace) und Live-Vorschau nebeneinander (Split-Pane) | ✓ SATISFIED  | `.editor-pane textarea` (monospace, dark theme) + `.preview-pane img`; split via `.main { display: flex }` |
| PANEL-03    | 02-02       | User kann Diagrammtyp im Panel per Dropdown wählen                                    | ✓ SATISFIED  | `<select>` dropdown bound to `_diagramType`, populated from `DIAGRAM_TYPES` (28 entries) |
| PANEL-04    | 02-01, 02-03 | Panel rendert bei Änderungen eine Live-Vorschau via Kroki-Server (WebSocket-Backend)  | ✓ SATISFIED  | `ws_render` handler in `ws_api.py` calls `KrokiClient.render()` and returns data URL; 5 render tests pass |
| PANEL-05    | 02-02, 02-03 | User kann Entity-IDs aus einem Entity-Browser in die Template-Source einfügen         | ✓ SATISFIED  | `_insertEntity()` inserts `{{ states('entity_id') }}` at cursor; entity list loaded via `kroki/get_entities`; `test_ws_get_entities_*` passes |

**No orphaned requirements.** All 5 Phase 2 requirement IDs (PANEL-01 through PANEL-05) appear in plan frontmatter and are verified as satisfied.

---

### Anti-Patterns Found

| File                                             | Line     | Pattern                          | Severity | Impact                                                 |
|--------------------------------------------------|----------|----------------------------------|----------|--------------------------------------------------------|
| `custom_components/kroki/www/kroki-panel.js`     | 175, 189 | HTML `placeholder` attribute     | ℹ️ Info  | UI input hints — not code stubs. Expected behaviour.   |

No blockers. No warnings. The two `placeholder` occurrences are standard HTML attributes on `<textarea>` and `<input>` elements, not implementation stubs.

**Note on `manifest.json`:** `panel_custom` was deliberately NOT added to `dependencies` (see Plan 02-01 deviation). This is correct — `panel_custom` is a HA built-in that doesn't need formal dependency declaration. Adding it would pull `hass_frontend` into the test environment and break CI. This is a documented, intentional design decision.

---

### Human Verification Required

#### 1. Sidebar Entry Visual Appearance

**Test:** Start a real HA instance with the integration loaded, open the sidebar
**Expected:** "Kroki Diagrams" appears in the left sidebar with the `mdi:chart-tree` icon
**Why human:** Visual rendering in a running HA instance cannot be verified programmatically

#### 2. Live Preview End-to-End Flow

**Test:** In the panel, enter a mermaid diagram source and click "Render"
**Expected:** The preview pane shows the rendered SVG diagram within 2-3 seconds
**Why human:** Requires a real HA + Kroki server connection; WebSocket round-trip cannot be tested without a running stack

#### 3. Entity Browser Population

**Test:** Open the panel in a running HA instance with entities defined
**Expected:** The entity browser on the right shows a filterable list of entity IDs; typing in the filter box narrows the list; clicking an entity inserts `{{ states('entity_id') }}` at the cursor position in the textarea
**Why human:** Requires a running HA instance with real entity state; DOM interaction and cursor placement cannot be verified statically

#### 4. Split-Pane Responsive Layout

**Test:** Resize the browser window to a narrow viewport
**Expected:** Toolbar wraps gracefully; editor and preview remain usable (desktop-first; mobile not required for v2.0)
**Why human:** CSS layout behavior requires visual inspection

---

### Gaps Summary

**No gaps found.** All automated checks passed:

- Backend (`panel.py`, `ws_api.py`) fully implemented and wired into `async_setup`
- Frontend (`kroki-panel.js`) is a complete LitElement webcomponent with all required features
- All 5 PANEL requirements satisfied with direct codebase evidence
- 8/8 `test_panel.py` tests pass; full suite 112/112 green
- Ruff linting clean on all modified files
- Commits `e62c7d1`, `a489148`, `eba939f`, `65dfd0b`, `5263d2f` all verified in git log

The 4 human-verification items are for visual/interactive behavior in a running HA instance — they do not block the phase goal determination.

---

_Verified: 2026-04-02_
_Verifier: the agent (gsd-verifier)_
