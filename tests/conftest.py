"""Shared fixtures for Kroki integration tests."""

from __future__ import annotations

import pathlib
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS

from custom_components.kroki.const import (
    DEFAULT_SERVER_URL,
)

# Project root contains custom_components/kroki/
PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)


@pytest.fixture
def hass_config_dir() -> str:
    """Point HA config dir to project root so custom_components/kroki is found."""
    return PROJECT_ROOT


@pytest.fixture(autouse=True)
async def clear_custom_components_cache(hass: HomeAssistant) -> None:
    """Clear the custom components cache so our integration is discovered.

    The test helper bootstraps HA with a default config dir, which caches
    an empty custom_components dict. We need to clear that cache so the
    loader re-discovers our integration from the project root.
    """
    hass.data.pop(DATA_CUSTOM_COMPONENTS, None)


@pytest.fixture
def mock_kroki_client():
    """Return a mock KrokiClient."""
    client = MagicMock()
    client.server_url = DEFAULT_SERVER_URL
    client.async_health_check = AsyncMock(return_value=True)
    client.async_render_diagram = AsyncMock(return_value=b"<svg>test</svg>")
    return client


@pytest.fixture
def mock_kroki_client_unhealthy():
    """Return a mock KrokiClient that fails health checks."""
    client = MagicMock()
    client.server_url = DEFAULT_SERVER_URL
    client.async_health_check = AsyncMock(return_value=False)
    return client
