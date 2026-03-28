"""Config flow for the Kroki integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_SERVER_URL, DEFAULT_SERVER_URL, DOMAIN
from .kroki_client import KrokiClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERVER_URL, default=DEFAULT_SERVER_URL): str,
    }
)


class KrokiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kroki."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            server_url = user_input[CONF_SERVER_URL].rstrip("/")
            user_input[CONF_SERVER_URL] = server_url

            # Prevent duplicate entries for the same server
            self._async_abort_entries_match({CONF_SERVER_URL: server_url})

            # Validate the server connection
            session = async_get_clientsession(self.hass)
            client = KrokiClient(session, server_url)

            if await client.async_health_check():
                return self.async_create_entry(
                    title=server_url,
                    data=user_input,
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
