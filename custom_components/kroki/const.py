"""Constants for the Kroki integration."""

from homeassistant.const import Platform

DOMAIN = "kroki"

PLATFORMS = [Platform.IMAGE]

# Config keys (config entry data)
CONF_SERVER_URL = "server_url"
CONF_DIAGRAM_TYPE = "diagram_type"
CONF_DIAGRAM_SOURCE = "diagram_source"
CONF_OUTPUT_FORMAT = "output_format"
CONF_DIAGRAMS = "diagrams"
CONF_UNIQUE_ID = "unique_id"
CONF_DEFAULT_ENTITY_ID = "default_entity_id"

# Options keys (config entry options)
CONF_CACHE_MAX_SIZE = "cache_max_size"
CONF_DEFAULT_OUTPUT_FORMAT = "default_output_format"
CONF_ENABLE_PANEL = "enable_panel"

# Defaults
DEFAULT_SERVER_URL = "https://kroki.io"
DEFAULT_OUTPUT_FORMAT = "svg"
DEFAULT_CACHE_MAX_SIZE = 50
DEFAULT_ENABLE_PANEL = False

# Content types
CONTENT_TYPE_MAP = {
    "svg": "image/svg+xml",
    "png": "image/png",
}

# Service names
SERVICE_FORCE_RENDER = "force_render"

# Supported diagram types (all Kroki-supported types)
SUPPORTED_DIAGRAM_TYPES = [
    "actdiag",
    "blockdiag",
    "bpmn",
    "bytefield",
    "c4plantuml",
    "d2",
    "dbml",
    "ditaa",
    "erd",
    "excalidraw",
    "graphviz",
    "mermaid",
    "nomnoml",
    "nwdiag",
    "packetdiag",
    "pikchr",
    "plantuml",
    "rackdiag",
    "seqdiag",
    "structurizr",
    "svgbob",
    "symbolator",
    "tikz",
    "umlet",
    "vega",
    "vegalite",
    "wavedrom",
    "wireviz",
]
