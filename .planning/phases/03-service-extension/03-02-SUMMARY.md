# 03-02 Summary: Wiring — Service Registration, services.yaml, strings.json

## Status: COMPLETE

## What was done

### Task 1: kroki.force_render service registration (__init__.py)
Added service registration to `async_setup`:
- New imports: `voluptuous as vol`, `ATTR_ENTITY_ID`, `Platform`, `ServiceCall`, `SERVICE_FORCE_RENDER`, `KrokiImageEntity`
- Defined `_async_handle_force_render` as a closure inside `async_setup` capturing `hass`
- Handler logic (per D-06/D-07/D-08/D-09):
  - Gets `entity_ids` from `call.data.get(ATTR_ENTITY_ID, [])`
  - Resolves image entity component via `hass.data.get("entity_components", {}).get(Platform.IMAGE)`
  - Logs WARNING and skips if component is None or entity not found/not a KrokiImageEntity (D-09)
  - Logs DEBUG on dispatch (D-08)
  - Uses `hass.async_create_task(entity.async_force_render())` (D-07, fire-and-forget)
- Registered via `hass.services.async_register(DOMAIN, SERVICE_FORCE_RENDER, ...)` with `vol.Optional(ATTR_ENTITY_ID): cv.entity_ids` schema

### Task 2: services.yaml
Added `force_render` service definition with:
- Entity selector (integration=kroki, domain=image, multiple=true)
- Name and description fields

### Task 3: strings.json
Added `"force_render"` entry under `"services"` with name, description, and entity_id field descriptions.

## Verification

- `make test`: 112 passed (no regressions)
- `make lint`: all checks passed
- `python3 -c "import yaml; yaml.safe_load(open('custom_components/kroki/services.yaml'))"`: valid YAML
