"""Config flow for the Kroki integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CACHE_MAX_SIZE,
    CONF_DEFAULT_OUTPUT_FORMAT,
    CONF_SERVER_URL,
    DEFAULT_CACHE_MAX_SIZE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SERVER_URL,
    DOMAIN,
)
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> KrokiOptionsFlow:
        """Get the options flow for this handler."""
        return KrokiOptionsFlow()

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

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the server URL."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            server_url = user_input[CONF_SERVER_URL].rstrip("/")
            user_input[CONF_SERVER_URL] = server_url

            # Validate the server connection
            session = async_get_clientsession(self.hass)
            client = KrokiClient(session, server_url)

            if await client.async_health_check():
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    title=server_url,
                    data_updates=user_input,
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVER_URL,
                        default=reconfigure_entry.data.get(
                            CONF_SERVER_URL, DEFAULT_SERVER_URL
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )


class KrokiOptionsFlow(OptionsFlow):
    """Handle options for the Kroki integration."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEFAULT_OUTPUT_FORMAT,
                        default=self.config_entry.options.get(
                            CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT
                        ),
                    ): vol.In({"svg": "SVG", "png": "PNG"}),
                    vol.Optional(
                        CONF_CACHE_MAX_SIZE,
                        default=self.config_entry.options.get(
                            CONF_CACHE_MAX_SIZE, DEFAULT_CACHE_MAX_SIZE
                        ),
                    ): vol.All(int, vol.Range(min=1, max=500)),
                }
            ),
        )
