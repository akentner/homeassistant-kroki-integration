"""Kroki sidebar panel registration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

PANEL_DIR = Path(__file__).parent / "www"
URL_BASE = "/kroki_static"


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register the Kroki custom panel and its static files."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(url_path=URL_BASE, path=str(PANEL_DIR), cache_headers=False)]
    )
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path="kroki",
        webcomponent_name="kroki-panel",
        sidebar_title="Kroki Diagrams",
        sidebar_icon="mdi:chart-tree",
        module_url=f"{URL_BASE}/kroki-panel.js",
        embed_iframe=False,
        require_admin=False,
    )
