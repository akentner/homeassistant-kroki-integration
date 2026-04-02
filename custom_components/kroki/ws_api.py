"""WebSocket API for Kroki live preview and entity browser."""

from __future__ import annotations

import base64

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, SUPPORTED_DIAGRAM_TYPES
from .kroki_client import KrokiConnectionError, KrokiRenderError


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kroki/render",
        vol.Required("diagram_type"): vol.In(SUPPORTED_DIAGRAM_TYPES),
        vol.Required("source"): str,
        vol.Optional("output_format", default="svg"): vol.In(["svg", "png"]),
        vol.Optional("entry_id"): str,
    }
)
@websocket_api.async_response
async def ws_render(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Render a diagram and return it as a data URL."""
    entry_id = msg.get("entry_id")
    domain_data = hass.data.get(DOMAIN, {})
    if entry_id:
        entry_data = domain_data.get(entry_id)
    else:
        entry_data = next(iter(domain_data.values()), None) if domain_data else None

    if entry_data is None:
        connection.send_error(msg["id"], "no_server", "No Kroki server configured")
        return

    client = entry_data["client"]
    try:
        rendered = await client.async_render_diagram(msg["diagram_type"], msg["source"], msg["output_format"])
    except KrokiConnectionError as err:
        connection.send_error(msg["id"], "connection_error", str(err))
        return
    except KrokiRenderError as err:
        connection.send_error(msg["id"], "render_error", str(err))
        return

    data_url = f"data:image/{msg['output_format']};base64,{base64.b64encode(rendered).decode()}"
    connection.send_result(msg["id"], {"data_url": data_url, "output_format": msg["output_format"]})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kroki/get_entities",
    }
)
@callback
def ws_get_entities(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Return all HA entity IDs and names for the entity browser."""
    states = hass.states.async_all()
    entities = [{"entity_id": s.entity_id, "name": s.name} for s in sorted(states, key=lambda s: s.entity_id)]
    connection.send_result(msg["id"], {"entities": entities})


def async_setup_ws_api(hass: HomeAssistant) -> None:
    """Register WebSocket API commands for Kroki."""
    websocket_api.async_register_command(hass, ws_render)
    websocket_api.async_register_command(hass, ws_get_entities)
