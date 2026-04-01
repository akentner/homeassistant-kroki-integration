"""The Kroki integration."""

from __future__ import annotations

import logging
from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType

from .cache import KrokiCache
from .const import (
    CONF_CACHE_MAX_SIZE,
    CONF_SERVER_URL,
    DEFAULT_CACHE_MAX_SIZE,
    DEFAULT_SERVER_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_FORCE_RENDER,
)
from .image import KrokiImageEntity
from .kroki_client import KrokiClient
from .panel import async_setup_panel
from .ws_api import async_setup_ws_api

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

type KrokiConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Kroki integration from YAML."""
    # Register the reload service so it appears in Developer Tools
    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    await async_setup_panel(hass)
    async_setup_ws_api(hass)

    async def _async_handle_force_render(call: ServiceCall) -> None:
        """Handle the kroki.force_render service call."""
        entity_ids: list[str] = call.data.get(ATTR_ENTITY_ID, [])
        # Resolve the image entity component to look up live entities
        component = hass.data.get("entity_components", {}).get(Platform.IMAGE)
        for entity_id in entity_ids:
            if component is None:
                _LOGGER.warning("force_render: image entity component not available, skipping %s", entity_id)
                continue
            entity = component.get_entity(entity_id)
            if entity is None or not isinstance(entity, KrokiImageEntity):
                _LOGGER.warning(
                    "force_render: entity %s not found or not a KrokiImageEntity, skipping",
                    entity_id,
                )
                continue
            _LOGGER.debug("force_render dispatching to %s", entity_id)
            hass.async_create_task(entity.async_force_render())

    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_RENDER,
        _async_handle_force_render,
        schema=vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids}),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: KrokiConfigEntry) -> bool:
    """Set up Kroki from a config entry.

    Creates a shared KrokiClient and KrokiCache for the config entry and
    forwards setup to the image platform so that GUI-managed diagram entities
    are registered as HA image entities.
    """
    hass.data.setdefault(DOMAIN, {})

    server_url = entry.data.get(CONF_SERVER_URL, DEFAULT_SERVER_URL)
    cache_max_size = entry.options.get(CONF_CACHE_MAX_SIZE, DEFAULT_CACHE_MAX_SIZE)
    session = async_get_clientsession(hass)
    client = KrokiClient(session, server_url)
    cache_dir = Path(hass.config.path(".storage")) / DOMAIN
    cache = KrokiCache(cache_dir, max_size=cache_max_size)

    hass.data[DOMAIN][entry.entry_id] = {"client": client, "cache": cache}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KrokiConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
