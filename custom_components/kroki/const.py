"""Constants for the Kroki integration."""

from homeassistant.const import Platform

DOMAIN = "kroki"

PLATFORMS = [Platform.IMAGE]

# Config keys
CONF_SERVER_URL = "server_url"
CONF_DIAGRAM_TYPE = "diagram_type"
CONF_DIAGRAM_SOURCE = "diagram_source"
CONF_OUTPUT_FORMAT = "output_format"
CONF_DIAGRAMS = "diagrams"

# Defaults
DEFAULT_SERVER_URL = "https://kroki.io"
DEFAULT_OUTPUT_FORMAT = "svg"
DEFAULT_CACHE_MAX_SIZE = 50

# Content types
CONTENT_TYPE_MAP = {
    "svg": "image/svg+xml",
    "png": "image/png",
}

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
