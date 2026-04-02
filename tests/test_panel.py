"""Tests for Kroki panel and WebSocket API."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.kroki.const import DOMAIN
from custom_components.kroki.kroki_client import KrokiConnectionError, KrokiRenderError
from custom_components.kroki.ws_api import ws_get_entities, ws_render


def _make_connection():
    """Create a mock WebSocket connection."""
    conn = MagicMock()
    conn.send_result = MagicMock()
    conn.send_error = MagicMock()
    return conn


def _make_hass_with_client(hass, client, entry_id="test_entry"):
    """Populate hass.data[DOMAIN] with a mock client."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry_id] = {"client": client, "cache": MagicMock()}
    return hass


@pytest.mark.asyncio
async def test_ws_render_success(hass):
    """Successful render returns a data URL."""
    mock_client = AsyncMock()
    mock_client.async_render_diagram.return_value = b"<svg>test</svg>"
    _make_hass_with_client(hass, mock_client)

    connection = _make_connection()
    msg = {
        "id": 1,
        "type": "kroki/render",
        "diagram_type": "mermaid",
        "source": "graph TD\n  A-->B",
        "output_format": "svg",
    }
    # ws_render is wrapped with @async_response — it schedules a background task.
    # We must call it synchronously and then drain the event loop.
    ws_render(hass, connection, msg)
    await hass.async_block_till_done()

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert result["data_url"].startswith("data:image/svg")
    assert base64.b64decode(result["data_url"].split(",", 1)[1]) == b"<svg>test</svg>"


@pytest.mark.asyncio
async def test_ws_render_no_server(hass):
    """Render with no configured server returns no_server error."""
    hass.data.setdefault(DOMAIN, {})
    connection = _make_connection()
    msg = {
        "id": 2,
        "type": "kroki/render",
        "diagram_type": "mermaid",
        "source": "graph TD\n  A-->B",
        "output_format": "svg",
    }
    ws_render(hass, connection, msg)
    await hass.async_block_till_done()

    connection.send_error.assert_called_once()
    assert connection.send_error.call_args[0][1] == "no_server"
    connection.send_result.assert_not_called()


@pytest.mark.asyncio
async def test_ws_render_connection_error(hass):
    """KrokiConnectionError maps to connection_error."""
    mock_client = AsyncMock()
    mock_client.async_render_diagram.side_effect = KrokiConnectionError("timeout")
    _make_hass_with_client(hass, mock_client)

    connection = _make_connection()
    msg = {"id": 3, "type": "kroki/render", "diagram_type": "graphviz", "source": "digraph {}", "output_format": "svg"}
    ws_render(hass, connection, msg)
    await hass.async_block_till_done()

    connection.send_error.assert_called_once()
    assert connection.send_error.call_args[0][1] == "connection_error"


@pytest.mark.asyncio
async def test_ws_render_render_error(hass):
    """KrokiRenderError maps to render_error."""
    mock_client = AsyncMock()
    mock_client.async_render_diagram.side_effect = KrokiRenderError("syntax error")
    _make_hass_with_client(hass, mock_client)

    connection = _make_connection()
    msg = {"id": 4, "type": "kroki/render", "diagram_type": "plantuml", "source": "bad source", "output_format": "svg"}
    ws_render(hass, connection, msg)
    await hass.async_block_till_done()

    connection.send_error.assert_called_once()
    assert connection.send_error.call_args[0][1] == "render_error"


@pytest.mark.asyncio
async def test_ws_render_png_format(hass):
    """PNG output format reflected in data URL."""
    mock_client = AsyncMock()
    mock_client.async_render_diagram.return_value = b"\x89PNG..."
    _make_hass_with_client(hass, mock_client)

    connection = _make_connection()
    msg = {
        "id": 5,
        "type": "kroki/render",
        "diagram_type": "mermaid",
        "source": "graph TD\n A-->B",
        "output_format": "png",
    }
    ws_render(hass, connection, msg)
    await hass.async_block_till_done()

    result = connection.send_result.call_args[0][1]
    assert result["data_url"].startswith("data:image/png")


def test_ws_get_entities_returns_all_states(hass):
    """get_entities returns one entry per state."""
    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("sensor.temp", "21")

    connection = _make_connection()
    msg = {"id": 6, "type": "kroki/get_entities"}
    ws_get_entities(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    entity_ids = [e["entity_id"] for e in result["entities"]]
    assert "light.kitchen" in entity_ids
    assert "sensor.temp" in entity_ids


def test_ws_get_entities_empty(hass):
    """get_entities returns empty list when no states."""
    connection = _make_connection()
    msg = {"id": 7, "type": "kroki/get_entities"}
    ws_get_entities(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert isinstance(result["entities"], list)


@pytest.mark.asyncio
async def test_async_setup_panel_registers(hass):
    """async_setup_panel registers the panel with correct url_path."""
    from custom_components.kroki.panel import async_setup_panel

    mock_http = MagicMock()
    mock_http.async_register_static_paths = AsyncMock()
    with (
        patch("custom_components.kroki.panel.panel_custom.async_register_panel") as mock_register,
        patch.object(hass, "http", mock_http),
    ):
        mock_register.return_value = None
        await async_setup_panel(hass)

    mock_register.assert_called_once()
    kwargs = mock_register.call_args.kwargs
    assert kwargs.get("frontend_url_path") == "kroki"
    assert kwargs.get("webcomponent_name") == "kroki-panel"
