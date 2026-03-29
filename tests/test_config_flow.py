"""Tests for the Kroki config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.kroki.const import (
    CONF_CACHE_MAX_SIZE,
    CONF_DEFAULT_OUTPUT_FORMAT,
    CONF_SERVER_URL,
    DEFAULT_SERVER_URL,
    DOMAIN,
)

PATCH_CLIENT = "custom_components.kroki.config_flow.KrokiClient"


@pytest.fixture
def mock_setup_entry():
    """Mock async_setup_entry."""
    with patch(
        "custom_components.kroki.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


async def test_user_flow_success(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://kroki.example.com"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "https://kroki.example.com"
    assert result["data"] == {CONF_SERVER_URL: "https://kroki.example.com"}


async def test_user_flow_strips_trailing_slash(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test that trailing slashes are stripped from the URL."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://kroki.example.com/"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SERVER_URL] == "https://kroki.example.com"


async def test_user_flow_connection_error(hass: HomeAssistant) -> None:
    """Test user flow when server is unreachable."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=False)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://bad-server.example.com"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_recover_after_error(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test that the user can retry after a connection error."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    # First attempt fails
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=False)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://bad-server.example.com"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Second attempt succeeds
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://good-server.example.com"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_duplicate_entry(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test that duplicate server URLs are prevented."""
    # Create an existing entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://kroki.example.com"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Try to add the same server again
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://kroki.example.com"},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_flow_success(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test successful reconfiguration of server URL."""
    # Create initial entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://old-server.example.com"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]

    # Start reconfiguration via config_entries flow API
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://new-server.example.com"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_SERVER_URL] == "https://new-server.example.com"


async def test_reconfigure_flow_connection_error(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test reconfiguration when new server is unreachable."""
    # Create initial entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://server.example.com"},
        )
    entry = result["result"]

    # Start reconfiguration - new server is unreachable
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=False)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://unreachable.example.com"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test options flow for default_output_format and cache_max_size."""
    # Create initial entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: DEFAULT_SERVER_URL},
        )
    entry = result["result"]

    # Open options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Submit options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEFAULT_OUTPUT_FORMAT: "png",
            CONF_CACHE_MAX_SIZE: 100,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_DEFAULT_OUTPUT_FORMAT] == "png"
    assert entry.options[CONF_CACHE_MAX_SIZE] == 100


async def test_options_flow_shows_current_values(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test that options flow shows current option values."""
    # Create initial entry with options
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: DEFAULT_SERVER_URL},
        )
    entry = result["result"]

    # Set initial options
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEFAULT_OUTPUT_FORMAT: "png",
            CONF_CACHE_MAX_SIZE: 200,
        },
    )

    # Re-open options flow - should show previously saved values
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
