"""Tests for the Kroki integration setup (__init__.py)."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kroki.const import (
    CONF_SERVER_URL,
    DOMAIN,
)


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
    """Test setting up a config entry stores data in hass.data."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    assert hass.data[DOMAIN][mock_config_entry.entry_id] == {CONF_SERVER_URL: "https://kroki.example.com"}


async def test_async_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test unloading a config entry removes data from hass.data."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

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
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # The reload service should be registered
    assert hass.services.has_service(DOMAIN, "reload")
