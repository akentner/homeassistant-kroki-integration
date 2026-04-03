---
phase: 01-subentry-crud
plan: "02"
subsystem: config-flow
tags: [config-flow, subentry, diagram-crud, template-validation, strings]
dependency_graph:
  requires: [01-01-SUMMARY.md]
  provides: [DiagramSubentryFlowHandler, async_get_supported_subentry_types, subentry-strings]
  affects: [config_flow.py, strings.json]
tech_stack:
  added: [ConfigSubentryFlow, SubentryFlowResult, TemplateSelector, SelectSelector, TextSelector]
  patterns: [subentry-flow-handler, template-validation, parent-entry-options-inheritance]
key_files:
  modified:
    - custom_components/kroki/config_flow.py
    - custom_components/kroki/strings.json
decisions:
  - "Template validation uses Template(source, hass).ensure_valid() — rejects syntax errors, accepts entity-reference templates (D-01, D-03)"
  - "Output format 'Server Default' stores 'server_default' string (not None) in subentry data — entity resolves effective format in plan 01-03 (D-04, D-06)"
  - "Add case inherits parent entry's default output format from options (D-05)"
  - "Reconfigure passes title=user_input[CONF_NAME] to async_update_and_abort — updates subentry title on rename (D-07)"
metrics:
  duration: "2m 27s"
  completed: "2026-04-02T00:46:00Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 01 Plan 02: DiagramSubentryFlowHandler + Strings Summary

**One-liner:** DiagramSubentryFlowHandler with TemplateSelector, template syntax validation, and full subentry localization strings via strings.json.

## What Was Built

### Task 1: DiagramSubentryFlowHandler (config_flow.py)

Added to `custom_components/kroki/config_flow.py`:

- **New imports:** `ConfigSubentryFlow`, `SubentryFlowResult`, `CONF_NAME`, `SelectSelector`, `SelectSelectorConfig`, `TemplateSelector`, `TextSelector`, `TextSelectorConfig`, `TextSelectorType`, `Template`, `TemplateError`, plus new const imports (`CONF_DIAGRAM_SOURCE`, `CONF_DIAGRAM_TYPE`, `CONF_OUTPUT_FORMAT`, `SUPPORTED_DIAGRAM_TYPES`)
- **`KrokiConfigFlow.async_get_supported_subentry_types`**: classmethod returning `{"diagram": DiagramSubentryFlowHandler}`
- **`DiagramSubentryFlowHandler`** class with:
  - `async_step_user`: Add flow — validates template syntax, calls `async_create_entry(title=name, data={...})`
  - `async_step_reconfigure`: Edit flow — pre-populates from `subentry.data`, calls `async_update_and_abort(entry, subentry, title=..., data={...})`
  - `_build_schema`: Builds vol.Schema with TextSelector (name), SelectSelector (28 sorted diagram types), TemplateSelector (source), SelectSelector (output format: server_default/svg/png). Inherits parent entry's default output format for new diagrams.

**Template validation:** `Template(source, self.hass).ensure_valid()` — catches `TemplateError`, returns `errors[CONF_DIAGRAM_SOURCE] = "invalid_template"` with error detail in `description_placeholders`. Valid templates referencing non-existent entities pass through.

### Task 2: Subentry Strings (strings.json)

Added `"subentries"` top-level key with complete `"diagram"` subentry flow strings:

- `flow_title`: "Diagram"
- `step.user`: Add Diagram — title, description, data labels, data_description for all 4 fields
- `step.reconfigure`: Edit Diagram — same structure
- `error.invalid_template`: "Invalid Jinja2 template syntax: {reason}" (with `{reason}` placeholder)
- `abort.reconfigure_successful`: "Diagram updated successfully."
- `selector.output_format.options`: server_default/svg/png option labels

All existing `config`, `options`, and `services` keys preserved.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| Task 1: DiagramSubentryFlowHandler | `fd1494b` | custom_components/kroki/config_flow.py |
| Task 2: Subentry strings | `6e6c76e` | custom_components/kroki/strings.json |

## Verification Passed

```
ruff check custom_components/kroki/config_flow.py → All checks passed!
python -c "from custom_components.kroki.config_flow import DiagramSubentryFlowHandler, KrokiConfigFlow; ..." → ok
python3 -m json.tool custom_components/kroki/strings.json → valid JSON
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. The `async_create_entry` and `async_update_and_abort` calls are functional. The `CONF_OUTPUT_FORMAT` value `"server_default"` is a known string sentinel (not None) that plan 01-03 resolves to the effective format. This is intentional per D-04/D-06, not a stub.

## Self-Check: PASSED

- `custom_components/kroki/config_flow.py` contains `DiagramSubentryFlowHandler` ✓
- `custom_components/kroki/strings.json` contains `subentries.diagram` ✓
- Commits `fd1494b` and `6e6c76e` exist ✓
