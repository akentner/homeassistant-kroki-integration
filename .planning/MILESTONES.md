# Milestones

## v2.0 GUI Entity Management (Shipped: 2026-04-03)

**Phases completed:** 3 phases, 10 plans, 14 tasks

**Key accomplishments:**

- Diagram entities fully manageable via HA GUI — no YAML editing required (Config Subentries)
- Stable `unique_id = subentry_id` prevents entity registry collisions with YAML entities
- Jinja2 templates auto-re-render on entity state changes in GUI-created diagrams
- YAML and GUI entities coexist without conflict or migration required
- Custom sidebar panel with split-pane code editor and live WebSocket preview
- `kroki.force_render` service for manual re-render with cache eviction
- 121 passing tests across all phases

---
