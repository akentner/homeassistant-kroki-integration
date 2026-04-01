"""Config flow for the Kroki integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.template import Template, TemplateError

from .const import (
    CONF_CACHE_MAX_SIZE,
    CONF_DEFAULT_OUTPUT_FORMAT,
    CONF_DIAGRAM_SOURCE,
    CONF_DIAGRAM_TYPE,
    CONF_OUTPUT_FORMAT,
    CONF_SERVER_URL,
    DEFAULT_CACHE_MAX_SIZE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SERVER_URL,
    DOMAIN,
    SUPPORTED_DIAGRAM_TYPES,
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
    MINOR_VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> KrokiOptionsFlow:
        """Get the options flow for this handler."""
        return KrokiOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry) -> dict[str, type[ConfigSubentryFlow]]:
        """Return supported subentry types."""
        return {"diagram": DiagramSubentryFlowHandler}

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
                        default=reconfigure_entry.data.get(CONF_SERVER_URL, DEFAULT_SERVER_URL),
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
                        default=self.config_entry.options.get(CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT),
                    ): vol.In({"svg": "SVG", "png": "PNG"}),
                    vol.Optional(
                        CONF_CACHE_MAX_SIZE,
                        default=self.config_entry.options.get(CONF_CACHE_MAX_SIZE, DEFAULT_CACHE_MAX_SIZE),
                    ): vol.All(int, vol.Range(min=1, max=500)),
                }
            ),
        )


class DiagramSubentryFlowHandler(ConfigSubentryFlow):
    """Handle add/reconfigure flows for diagram subentries."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Handle the add-diagram step."""
        parent_entry = self._get_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate template syntax (D-01)
            source = user_input[CONF_DIAGRAM_SOURCE]
            try:
                Template(source, self.hass).ensure_valid()
            except TemplateError as err:
                errors[CONF_DIAGRAM_SOURCE] = "invalid_template"
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._build_schema(parent_entry),
                    errors=errors,
                    description_placeholders={"reason": str(err)},
                )

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_DIAGRAM_TYPE: user_input[CONF_DIAGRAM_TYPE],
                    CONF_DIAGRAM_SOURCE: user_input[CONF_DIAGRAM_SOURCE],
                    CONF_OUTPUT_FORMAT: user_input.get(CONF_OUTPUT_FORMAT),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(parent_entry),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Handle reconfigure of an existing diagram subentry."""
        parent_entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}

        if user_input is not None:
            source = user_input[CONF_DIAGRAM_SOURCE]
            try:
                Template(source, self.hass).ensure_valid()
            except TemplateError as err:
                errors[CONF_DIAGRAM_SOURCE] = "invalid_template"
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=self._build_schema(parent_entry, subentry.data),
                    errors=errors,
                    description_placeholders={"reason": str(err)},
                )

            return self.async_update_and_abort(
                parent_entry,
                subentry,
                title=user_input[CONF_NAME],
                data={
                    CONF_DIAGRAM_TYPE: user_input[CONF_DIAGRAM_TYPE],
                    CONF_DIAGRAM_SOURCE: user_input[CONF_DIAGRAM_SOURCE],
                    CONF_OUTPUT_FORMAT: user_input.get(CONF_OUTPUT_FORMAT),
                },
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(parent_entry, subentry.data),
            errors=errors,
        )

    def _build_schema(
        self,
        parent_entry: ConfigEntry,
        current: dict | None = None,
    ) -> vol.Schema:
        """Build the form schema for add or reconfigure."""
        if current is None:
            current = {}
        # Add case (current is empty): inherit parent server's default output format (D-05).
        # Map the effective format to a selector option string ("svg", "png", or "server_default").
        if not current:
            effective = parent_entry.options.get(CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT)
            default_format = effective if effective in ("svg", "png") else "server_default"
        else:
            default_format = current.get(CONF_OUTPUT_FORMAT, "server_default")
        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=current.get(CONF_NAME, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(
                    CONF_DIAGRAM_TYPE,
                    default=current.get(CONF_DIAGRAM_TYPE, SUPPORTED_DIAGRAM_TYPES[0]),
                ): SelectSelector(SelectSelectorConfig(options=SUPPORTED_DIAGRAM_TYPES, sort=True)),
                vol.Required(
                    CONF_DIAGRAM_SOURCE,
                    default=current.get(CONF_DIAGRAM_SOURCE, ""),
                ): TemplateSelector(),
                vol.Optional(
                    CONF_OUTPUT_FORMAT,
                    default=default_format,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=["server_default", "svg", "png"],
                    )
                ),
            }
        )
