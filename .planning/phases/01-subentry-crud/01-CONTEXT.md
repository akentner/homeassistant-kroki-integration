# Phase 1: Subentry CRUD - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers Config Subentry CRUD for diagram entities: users can add, edit, and delete
Kroki diagram entities via the Home Assistant GUI (Settings > Devices & Services), using
HA's Config Subentry mechanism (introduced in HA 2025.7). The YAML platform path remains
completely unchanged alongside the new GUI path.

**In scope:** `DiagramSubentryFlowHandler` (add + reconfigure steps), `async_setup_entry`
in `image.py`, platform forwarding in `__init__.py`, KrokiImageEntity factory for subentries,
shared cache, template validation, strings/translations.

**Out of scope:** Custom panel (Phase 2), force re-render service (Phase 3), YAML migration,
live render preview during config flow save.

</domain>

<decisions>
## Implementation Decisions

### Template Validation

- **D-01:** `async_step_user` and `async_step_reconfigure` validate Jinja2 template syntax
  before saving. Use `homeassistant.helpers.template.Template(source)` to compile; catch
  `TemplateError` and return `errors["diagram_source"] = "invalid_template"` with the
  exception message as the error description.
- **D-02:** Error detail is shown as the Jinja2 exception message (not a generic string).
  The `strings.json` key `invalid_template` should include a `{reason}` placeholder so the
  full error is surfaced inline.
- **D-03:** Templates that reference non-existent entity states are syntactically valid and
  MUST be accepted — they will fail on first render and show an error SVG (existing behavior).
  Only pure syntax errors (unparseable) are rejected in the form.

### Output Format Field

- **D-04:** The subentry form always shows an output format field (3-option SelectSelector):
  - Option 1: "Server Default" → stores `None` or omits the key in `subentry.data`
  - Option 2: "SVG" → stores `"svg"`
  - Option 3: "PNG" → stores `"png"`
- **D-05:** Default pre-selection when opening the add form = `config_entry.options.get(CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT)` — inherits from the parent server Config Entry options.
- **D-06:** The entity's effective output format is resolved at setup time: `subentry.data.get(CONF_OUTPUT_FORMAT) or entry.options.get(CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT)`.

### Entity Naming

- **D-07:** `subentry.title` is used as the entity name (`_attr_name = subentry.title`). The
  form field is labelled **"Name"** with description "Display name for this diagram entity"
  and a placeholder like "Network Overview".
- **D-08:** `unique_id = subentry.subentry_id` (stable ULID, set once at creation, never
  re-derived). If the user renames the diagram, `entity_id` does NOT change (HA entity
  registry preserves it). This is accepted behavior — entity name updates visually, entity_id
  stays stable.
- **D-09:** YAML entities keep their existing unique_id scheme: `unique_id or f"kroki_{cv.slugify(name)}"`. The two namespaces (YAML: name-derived, GUI: subentry_id) never collide.

### Cache Sharing

- **D-10:** One `KrokiCache` instance per server Config Entry (`entry_id`), created in
  `async_setup_entry` in `__init__.py`. Stored in `hass.data[DOMAIN][entry_id]` as a dict
  with two keys: `"client"` (`KrokiClient`) and `"cache"` (`KrokiCache`).
- **D-11:** `async_setup_platform` (YAML path) retrieves the shared cache and client from
  `hass.data[DOMAIN][config_entries[0].entry_id]` instead of creating new instances. This
  ensures YAML and GUI entities for the same server share one cache.
- **D-12:** `async_setup_entry` in `__init__.py` must be updated to store `{"client": ..., "cache": ...}` instead of `entry.data` directly. `async_unload_entry` pops the same key.

### KrokiImageEntity Construction

- **D-13:** Add a `from_subentry` classmethod to `KrokiImageEntity`:
  ```python
  @classmethod
  def from_subentry(
      cls,
      hass: HomeAssistant,
      client: KrokiClient,
      cache: KrokiCache,
      subentry: ConfigSubentry,
      effective_output_format: str,
  ) -> KrokiImageEntity:
  ```
  This classmethod creates the entity from subentry data, sets `unique_id = subentry.subentry_id`,
  and wraps `subentry.data[CONF_DIAGRAM_SOURCE]` in a `Template` object.
- **D-14:** The existing `__init__` signature is NOT changed (YAML path stays intact). The
  classmethod is an additional factory, not a replacement.

### Platform Forwarding

- **D-15:** `async_setup_entry` in `__init__.py` must call
  `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`.
- **D-16:** `async_unload_entry` must call
  `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` and only pop
  `hass.data[DOMAIN][entry.entry_id]` if unload succeeded.

### Claude's Discretion

- Config entry `MINOR_VERSION` bump (1.1 → 1.2) after adding platform forwarding — standard HA practice.
- Whether `strings.json` uses `selector` keys for the diagram type SelectSelector or plain labels — follow HA conventions.
- Test coverage strategy: unit tests for `DiagramSubentryFlowHandler` (add/reconfigure/delete), integration test for dual-path entity coexistence.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing integration code (modify)
- `custom_components/kroki/__init__.py` — Add platform forwarding + cache/client storage
- `custom_components/kroki/config_flow.py` — Add `async_get_supported_subentry_types` + `DiagramSubentryFlowHandler`
- `custom_components/kroki/image.py` — Add `async_setup_entry` + `KrokiImageEntity.from_subentry`
- `custom_components/kroki/const.py` — `PLATFORMS`, existing `CONF_*` constants (reuse, don't duplicate)

### Research (architecture patterns + pitfalls)
- `.planning/research/ARCHITECTURE.md` — Target architecture, dual-path coexistence, exact code patterns for platform forwarding + subentry flow
- `.planning/research/PITFALLS.md` — Critical pitfalls (unique_id collision, missing platform forwarding, subscription leaks, reload race condition)
- `.planning/research/FEATURES.md` — Table stakes, TemplateSelector pattern, strings.json requirements

### Planning inputs
- `.planning/REQUIREMENTS.md` — Phase 1 requirements: CRUD-01..05, CFG-01..04, TPL-01..02, YAML-01

No external specs — all architecture decisions are captured above and in research files.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `KrokiClient` — unchanged; shared between YAML and GUI entities via `hass.data`
- `KrokiCache` — unchanged; shared instance stored in `hass.data[DOMAIN][entry_id]["cache"]`
- `_generate_error_svg` — unchanged; reused by GUI entities on render failure
- `_compute_hash` — unchanged; same hash logic for both entity types
- `SUPPORTED_DIAGRAM_TYPES`, `CONTENT_TYPE_MAP`, `CONF_*` constants — reuse directly
- `KrokiConnectionError`, `KrokiRenderError` — unchanged exception hierarchy

### Established Patterns
- `_attr_has_entity_name = True` — stays; GUI entities also use this
- `async_track_template_result` / `async_will_remove_from_hass` — must be preserved in `from_subentry` path; not removable
- `async_update_reload_and_abort` (in `async_step_reconfigure` of server flow) — confirmed pattern
- `errors["base"] = "..."` — extend to `errors["diagram_source"] = "invalid_template"` for field-level errors

### Integration Points
- `__init__.py:async_setup_entry` → add `async_forward_entry_setups(entry, PLATFORMS)` and cache/client init
- `__init__.py:async_unload_entry` → add `async_unload_platforms(entry, PLATFORMS)`
- `config_flow.py:KrokiConfigFlow` → add `async_get_supported_subentry_types` classmethod
- `image.py` → add `async_setup_entry(hass, config_entry, async_add_entities)` at module level

### Breaking Change
- `hass.data[DOMAIN][entry_id]` changes from `entry.data` (a dict) to `{"client": KrokiClient, "cache": KrokiCache}`. Any code reading `hass.data[DOMAIN]` must be updated (currently only `async_setup_entry` stores it; no other code reads it — safe change).

</code_context>

<specifics>
## Specific Ideas

- The output format field in the subentry form shows 3 options: "Server Default", "SVG", "PNG". The "Server Default" option stores `None` / omits the key. Entity resolves effective format at setup time by checking subentry data first, then parent entry options.
- Form field for diagram source: `TemplateSelector()` — no configuration needed, provides full-screen editor button automatically (HA 2025.7+).
- Form field for diagram type: `SelectSelector(SelectSelectorConfig(options=SUPPORTED_DIAGRAM_TYPES, sort=True))`.
- Template validation: `from homeassistant.helpers.template import Template; Template(source, hass).ensure_valid()` — raises `TemplateError` with message that becomes the error description.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-subentry-crud*
*Context gathered: 2026-04-01*
