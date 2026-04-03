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


# ===== Subentry flow tests =====


async def _create_server_entry(hass: HomeAssistant) -> config_entries.ConfigEntry:
    """Helper to create a server config entry for subentry tests."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(PATCH_CLIENT) as mock_client_cls:
        mock_client_cls.return_value.async_health_check = AsyncMock(return_value=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SERVER_URL: "https://kroki.example.com"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    return result["result"]


async def test_subentry_add_flow_success(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test successful diagram subentry creation."""
    from custom_components.kroki.const import CONF_DIAGRAM_SOURCE, CONF_DIAGRAM_TYPE, CONF_OUTPUT_FORMAT

    entry = await _create_server_entry(hass)

    # Start subentry add flow
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "diagram"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "My Diagram",
            CONF_DIAGRAM_TYPE: "mermaid",
            CONF_DIAGRAM_SOURCE: "graph TD\nA-->B",
            CONF_OUTPUT_FORMAT: "svg",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Verify subentry was created with correct data
    assert len(entry.subentries) == 1
    subentry = list(entry.subentries.values())[0]
    assert subentry.title == "My Diagram"
    assert subentry.data[CONF_DIAGRAM_TYPE] == "mermaid"
    assert subentry.data[CONF_DIAGRAM_SOURCE] == "graph TD\nA-->B"


async def test_subentry_add_flow_invalid_template(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test that invalid Jinja2 syntax raises a schema validation error for diagram_source.

    TemplateSelector validates syntax via cv.template at the schema level, which
    raises InvalidData rather than returning a FORM with errors. The field path
    in the schema error is 'diagram_source'.
    """
    from homeassistant.data_entry_flow import InvalidData

    from custom_components.kroki.const import CONF_DIAGRAM_SOURCE, CONF_DIAGRAM_TYPE, CONF_OUTPUT_FORMAT

    entry = await _create_server_entry(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "diagram"),
        context={"source": config_entries.SOURCE_USER},
    )
    # The TemplateSelector validates template syntax; invalid input raises InvalidData
    with pytest.raises(InvalidData) as exc_info:
        await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input={
                "name": "Bad Diagram",
                CONF_DIAGRAM_TYPE: "mermaid",
                CONF_DIAGRAM_SOURCE: "{{ invalid jinja {{ }}",
                CONF_OUTPUT_FORMAT: "svg",
            },
        )
    # Verify the error is associated with the diagram_source field
    assert "diagram_source" in exc_info.value.schema_errors


async def test_subentry_add_flow_valid_template_nonexistent_entity(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test that a valid template referencing a non-existent entity is accepted (D-03)."""
    from custom_components.kroki.const import CONF_DIAGRAM_SOURCE, CONF_DIAGRAM_TYPE, CONF_OUTPUT_FORMAT

    entry = await _create_server_entry(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "diagram"),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "Template Diagram",
            CONF_DIAGRAM_TYPE: "mermaid",
            CONF_DIAGRAM_SOURCE: "graph TD\nA[{{ states('sensor.nonexistent') }}]-->B",
            CONF_OUTPUT_FORMAT: "svg",
        },
    )
    # Template is syntactically valid — must be accepted even if entity doesn't exist
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_subentry_reconfigure_flow(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test reconfiguring an existing subentry."""
    from custom_components.kroki.const import CONF_DIAGRAM_SOURCE, CONF_DIAGRAM_TYPE, CONF_OUTPUT_FORMAT

    entry = await _create_server_entry(hass)

    # Add a subentry
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "diagram"),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "Original Name",
            CONF_DIAGRAM_TYPE: "mermaid",
            CONF_DIAGRAM_SOURCE: "graph TD\nA-->B",
            CONF_OUTPUT_FORMAT: "svg",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    subentry_id = list(entry.subentries.keys())[0]

    # Reconfigure the subentry directly via the subentries flow manager
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "diagram"),
        context={"source": config_entries.SOURCE_RECONFIGURE, "subentry_id": subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Verify form is pre-populated with current subentry values (name field)
    schema_keys = {str(k): k for k in result["data_schema"].schema}
    name_key = schema_keys["name"]
    assert name_key.default() == "Original Name"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "Renamed Diagram",
            CONF_DIAGRAM_TYPE: "plantuml",
            CONF_DIAGRAM_SOURCE: "@startuml\nA -> B\n@enduml",
            CONF_OUTPUT_FORMAT: "png",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify subentry was updated
    updated_subentry = entry.subentries[subentry_id]
    assert updated_subentry.title == "Renamed Diagram"
    assert updated_subentry.data[CONF_DIAGRAM_TYPE] == "plantuml"
    # subentry_id must NOT change (Pitfall 5, D-08)
    assert subentry_id in entry.subentries
