"""Tests for the Kroki integration setup (__init__.py)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kroki.const import (
    CONF_SERVER_URL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def mock_panel_setup():
    """Mock panel and WebSocket API setup to avoid frontend dependency in tests."""
    with (
        patch("custom_components.kroki.async_setup_panel", new=AsyncMock(return_value=None)),
        patch("custom_components.kroki.async_setup_ws_api", new=MagicMock(return_value=None)),
    ):
        yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="https://kroki.example.com",
        data={CONF_SERVER_URL: "https://kroki.example.com"},
        unique_id="https://kroki.example.com",
    )


async def test_async_setup_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test setting up a config entry stores client and cache in hass.data."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert "client" in entry_data
    assert "cache" in entry_data


async def test_async_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test unloading a config entry removes data from hass.data."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        new=AsyncMock(return_value=True),
    ):
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_async_setup_multiple_entries(hass: HomeAssistant) -> None:
    """Test setting up multiple config entries stores data for each."""
    entry1 = MockConfigEntry(
        domain=DOMAIN,
        title="https://server1.example.com",
        data={CONF_SERVER_URL: "https://server1.example.com"},
        unique_id="https://server1.example.com",
    )
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        title="https://server2.example.com",
        data={CONF_SERVER_URL: "https://server2.example.com"},
        unique_id="https://server2.example.com",
    )
    entry1.add_to_hass(hass)
    entry2.add_to_hass(hass)

    # Setting up one entry triggers HA to set up all entries for the domain
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        await hass.config_entries.async_setup(entry1.entry_id)
        await hass.async_block_till_done()

    assert entry1.state is ConfigEntryState.LOADED
    assert entry2.state is ConfigEntryState.LOADED
    assert entry1.entry_id in hass.data[DOMAIN]
    assert entry2.entry_id in hass.data[DOMAIN]


async def test_async_setup_registers_reload_service(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that async_setup registers the reload service."""
    mock_config_entry.add_to_hass(hass)

    # Trigger async_setup by loading the integration
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # The reload service should be registered
    assert hass.services.has_service(DOMAIN, "reload")


# ---------------------------------------------------------------------------
# kroki.force_render service
# ---------------------------------------------------------------------------


async def test_force_render_service_registered(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that force_render service is registered after async_setup."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, "force_render")


async def test_force_render_service_calls_entity_method(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that calling force_render dispatches to the entity's async_force_render."""
    from unittest.mock import AsyncMock as AM
    from unittest.mock import MagicMock

    from custom_components.kroki.image import KrokiImageEntity

    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Build a mock KrokiImageEntity
    mock_entity = MagicMock(spec=KrokiImageEntity)
    mock_entity.entity_id = "image.test_diagram"
    mock_entity.async_force_render = AM(return_value=None)

    # Inject mock entity via entity_components
    mock_component = MagicMock()
    mock_component.get_entity.return_value = mock_entity
    hass.data.setdefault("entity_components", {})["image"] = mock_component

    await hass.services.async_call(
        DOMAIN,
        "force_render",
        {"entity_id": ["image.test_diagram"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_entity.async_force_render.assert_called_once()


async def test_force_render_service_unknown_entity_logs_warning(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, caplog
) -> None:
    """Test that force_render logs WARNING for unknown entity_id without raising (D-09)."""
    import logging

    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(return_value=None),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    mock_component = MagicMock()
    mock_component.get_entity.return_value = None  # entity not found
    hass.data.setdefault("entity_components", {})["image"] = mock_component

    with caplog.at_level(logging.WARNING, logger="custom_components.kroki"):
        await hass.services.async_call(
            DOMAIN,
            "force_render",
            {"entity_id": ["image.nonexistent"]},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert any("force_render" in r.message and "nonexistent" in r.message for r in caplog.records)
