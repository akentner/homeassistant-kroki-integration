# Kroki Integration for Home Assistant

Generate dynamic diagram images from [Kroki](https://kroki.io) using Home Assistant templates.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/akentner/homeassistant-kroki-integration/actions/workflows/validate.yml/badge.svg)](https://github.com/akentner/homeassistant-kroki-integration/actions/workflows/validate.yml)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=akentner&repository=homeassistant-kroki-integration&category=integration)

## Features

- **Template-based diagrams** -- Use Jinja2 templates with entity states to generate dynamic diagrams
- **All Kroki diagram types** -- GraphViz, PlantUML, Mermaid, D2, BlockDiag, and 20+ more
- **SVG and PNG output** -- Configurable per diagram
- **Automatic updates** -- Images re-render automatically when referenced entities change
- **Hash-based caching** -- Identical diagrams are served from cache (LRU, configurable size)
- **Multiple servers** -- Use the public kroki.io or your own self-hosted instance
- **YAML reload** -- Update diagrams without restarting Home Assistant

## Installation

### HACS (Recommended)

1. Click the button above or:
   1. Open HACS in your Home Assistant instance
   2. Click the three dots in the top right corner and select **Custom repositories**
   3. Add `https://github.com/akentner/homeassistant-kroki-integration` with category **Integration**
2. Search for "Kroki" and install it
3. Restart Home Assistant

### Manual

1. Copy `custom_components/kroki/` to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Step 1: Add the Kroki server

Go to **Settings > Devices & Services > Add Integration > Kroki**

Enter the server URL (default: `https://kroki.io`). You can add multiple servers.

### Step 2: Define image entities in YAML

Add to your `configuration.yaml`:

```yaml
image:
  - platform: kroki
    diagrams:
      - name: "Network Overview"
        diagram_type: graphviz
        output_format: svg
        diagram_source: >
          digraph G {
            Internet -> Router
            Router -> "{{ states('sensor.switch_count') }} Switches"
            {% if is_state('binary_sensor.nas', 'on') %}
            Router -> NAS [color=green]
            {% else %}
            Router -> NAS [color=red, style=dashed]
            {% endif %}
          }

      - name: "System Status"
        diagram_type: mermaid
        output_format: png
        diagram_source: >
          flowchart LR
            A[CPU: {{ states('sensor.cpu_usage') }}%] --> B{Load}
            B -->|High| C[Alert]
            B -->|Normal| D[OK]
```

### Step 3: Reload

After editing YAML, go to **Developer Tools > YAML > Reload Kroki image entities** -- no restart needed.

## Configuration Options

### Diagram options

| Key | Required | Default | Description |
|---|---|---|---|
| `name` | Yes | -- | Name of the image entity |
| `diagram_type` | Yes | -- | Kroki diagram type (see below) |
| `diagram_source` | Yes | -- | Jinja2 template for the diagram source |
| `output_format` | No | `svg` | Output format: `svg` or `png` |

### Supported diagram types

`actdiag`, `blockdiag`, `bpmn`, `bytefield`, `c4plantuml`, `d2`, `dbml`, `ditaa`, `erd`, `excalidraw`, `graphviz`, `mermaid`, `nomnoml`, `nwdiag`, `packetdiag`, `pikchr`, `plantuml`, `rackdiag`, `seqdiag`, `structurizr`, `svgbob`, `symbolator`, `tikz`, `umlet`, `vega`, `vegalite`, `wavedrom`, `wireviz`

## Entity Attributes

Each Kroki image entity exposes these extra attributes:

| Attribute | Description |
|---|---|
| `diagram_type` | The diagram type (e.g., `graphviz`) |
| `output_format` | The output format (`svg` or `png`) |
| `last_rendered` | ISO timestamp of the last successful render |
| `template_hash` | SHA256 hash of the currently rendered template |
| `error` | Error message if rendering failed, otherwise `null` |
| `server_url` | The Kroki server URL used for rendering |

## Architecture

This integration uses a **hybrid configuration** approach:

- **Config Flow (UI):** Manages Kroki server connections. Go to Settings > Integrations to add one or more Kroki servers. Each config entry represents one server -- you can have a local instance and the public `kroki.io` side by side.
- **YAML Platform Config:** Defines the individual Image entities with their Jinja2 templates. Templates are complex and better suited for YAML than UI forms.

### How it works

```
  Template with entity references
          │
          ▼
  Jinja2 rendering (automatic on entity change)
          │
          ▼
  SHA256 hash of rendered output
          │
    ┌─────┴─────┐
    │ Cache hit │ Cache miss
    │ → from    │ → POST to Kroki API
    │   disk    │ → save to cache
    └───────────┘
          │
          ▼
  Image entity updated in frontend
```

The integration uses `async_track_template_result` to automatically detect which entities are referenced in a template. When any of those entities change state, the template is re-rendered and -- only if the rendered output actually changed (different hash) -- a new image is generated.

### Kroki API

The integration uses the Kroki POST API, sending diagram source as plain text:

```
POST /{diagram_type}/{output_format}
Content-Type: text/plain

<diagram source>
```

No encoding or compression is needed. The server returns the rendered image directly.

## Caching

Rendered images are cached in `.storage/kroki/` using a SHA256 hash of the rendered template output. The cache uses an LRU (Least Recently Used) strategy with a default limit of 50 entries. When the cache is full, the least recently accessed images are evicted.

This means:
- If an entity toggles between two known states, both images are cached and served instantly
- Restarts don't lose the cache (persistent on disk)
- The cache metadata is stored in `.storage/kroki/cache_meta.json`

## Error Handling

When a rendering error occurs (server unreachable, invalid diagram syntax, template error), the entity displays a red error placeholder SVG with the error message. The `error` attribute on the entity contains the details.

Error types:
- **Template error:** Invalid Jinja2 syntax or missing entities
- **Connection error:** Kroki server unreachable or timeout
- **Render error:** Kroki returns an error (e.g., invalid diagram syntax)

## Self-hosted Kroki

You can run your own Kroki server instead of using the public `kroki.io`:

```bash
docker run -d -p 8000:8000 yuzutech/kroki
```

Then add `http://your-host:8000` as the server URL in the integration config flow. See the [Kroki documentation](https://docs.kroki.io/kroki/setup/install/) for more deployment options.

## License

MIT
