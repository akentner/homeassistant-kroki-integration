"""The Kroki integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

type KrokiConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Kroki integration from YAML."""
    # Register the reload service so it appears in Developer Tools
    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: KrokiConfigEntry) -> bool:
    """Set up Kroki from a config entry.

    The config entry stores the Kroki server connection.
    Image entities are set up via YAML platform configuration.
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # We don't forward to platforms here because image entities
    # are configured via YAML platform config, not config entries.
    # The config entry only stores the server connection details.
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KrokiConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
