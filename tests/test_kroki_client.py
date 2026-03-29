"""Tests for the Kroki API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.kroki.kroki_client import (
    KrokiClient,
    KrokiConnectionError,
    KrokiRenderError,
)


@pytest.fixture
def mock_session():
    """Return a mock aiohttp ClientSession."""
    return MagicMock(spec=aiohttp.ClientSession)


def _mock_response(status: int = 200, body: bytes = b"", text: str = ""):
    """Create a mock aiohttp response as async context manager."""
    response = AsyncMock()
    response.status = status
    response.read = AsyncMock(return_value=body)
    response.text = AsyncMock(return_value=text)

    context = AsyncMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


class TestKrokiClientInit:
    """Tests for KrokiClient initialization."""

    def test_server_url_property(self, mock_session):
        """Test server_url property returns the configured URL."""
        client = KrokiClient(mock_session, "https://kroki.example.com")
        assert client.server_url == "https://kroki.example.com"

    def test_server_url_strips_trailing_slash(self, mock_session):
        """Test that trailing slashes are stripped from server URL."""
        client = KrokiClient(mock_session, "https://kroki.example.com/")
        assert client.server_url == "https://kroki.example.com"


class TestHealthCheck:
    """Tests for the health check endpoint."""

    async def test_health_check_success(self, mock_session):
        """Test successful health check."""
        mock_session.get = MagicMock(return_value=_mock_response(status=200))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        result = await client.async_health_check()

        assert result is True
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "https://kroki.example.com/health"

    async def test_health_check_server_error(self, mock_session):
        """Test health check returns False for non-200 response."""
        mock_session.get = MagicMock(return_value=_mock_response(status=500))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        result = await client.async_health_check()

        assert result is False

    async def test_health_check_connection_error(self, mock_session):
        """Test health check returns False on connection error."""
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection refused"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        result = await client.async_health_check()

        assert result is False

    async def test_health_check_timeout(self, mock_session):
        """Test health check returns False on timeout."""
        mock_session.get = MagicMock(side_effect=TimeoutError())
        client = KrokiClient(mock_session, "https://kroki.example.com")

        result = await client.async_health_check()

        assert result is False


class TestRenderDiagram:
    """Tests for the diagram rendering endpoint."""

    async def test_render_svg_success(self, mock_session):
        """Test successful SVG rendering."""
        svg_data = b"<svg>diagram</svg>"
        mock_session.post = MagicMock(return_value=_mock_response(status=200, body=svg_data))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        result = await client.async_render_diagram("graphviz", "digraph { A -> B }", "svg")

        assert result == svg_data
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://kroki.example.com/graphviz/svg"

    async def test_render_png_success(self, mock_session):
        """Test successful PNG rendering."""
        png_data = b"\x89PNG\r\n\x1a\n..."
        mock_session.post = MagicMock(return_value=_mock_response(status=200, body=png_data))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        result = await client.async_render_diagram("plantuml", "@startuml\nA -> B\n@enduml", "png")

        assert result == png_data
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://kroki.example.com/plantuml/png"

    async def test_render_sends_correct_headers(self, mock_session):
        """Test that the correct headers are sent."""
        mock_session.post = MagicMock(return_value=_mock_response(status=200, body=b"data"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        await client.async_render_diagram("mermaid", "graph TD; A-->B", "svg")

        call_args = mock_session.post.call_args
        headers = call_args[1]["headers"]
        assert headers["Content-Type"] == "text/plain"
        assert headers["Accept"] == "image/svg+xml"

    async def test_render_sends_png_accept_header(self, mock_session):
        """Test that PNG accept header is sent for PNG format."""
        mock_session.post = MagicMock(return_value=_mock_response(status=200, body=b"data"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        await client.async_render_diagram("graphviz", "digraph { A -> B }", "png")

        call_args = mock_session.post.call_args
        headers = call_args[1]["headers"]
        assert headers["Accept"] == "image/png"

    async def test_render_sends_source_as_utf8_bytes(self, mock_session):
        """Test that diagram source is sent as UTF-8 encoded bytes."""
        mock_session.post = MagicMock(return_value=_mock_response(status=200, body=b"data"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        source = "digraph { A -> B }"
        await client.async_render_diagram("graphviz", source, "svg")

        call_args = mock_session.post.call_args
        assert call_args[1]["data"] == source.encode("utf-8")

    async def test_render_http_error_raises_render_error(self, mock_session):
        """Test that non-200 responses raise KrokiRenderError."""
        mock_session.post = MagicMock(return_value=_mock_response(status=400, text="Syntax Error in diagram"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        with pytest.raises(KrokiRenderError, match="HTTP 400"):
            await client.async_render_diagram("graphviz", "invalid source", "svg")

    async def test_render_500_error_raises_render_error(self, mock_session):
        """Test that server errors raise KrokiRenderError."""
        mock_session.post = MagicMock(return_value=_mock_response(status=500, text="Internal Server Error"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        with pytest.raises(KrokiRenderError, match="HTTP 500"):
            await client.async_render_diagram("graphviz", "digraph { A -> B }", "svg")

    async def test_render_connection_error(self, mock_session):
        """Test that connection errors raise KrokiConnectionError."""
        mock_session.post = MagicMock(side_effect=aiohttp.ClientError("Connection refused"))
        client = KrokiClient(mock_session, "https://kroki.example.com")

        with pytest.raises(KrokiConnectionError, match="Cannot connect"):
            await client.async_render_diagram("graphviz", "digraph { A -> B }", "svg")

    async def test_render_timeout_error(self, mock_session):
        """Test that timeout errors raise KrokiConnectionError."""
        mock_session.post = MagicMock(side_effect=TimeoutError())
        client = KrokiClient(mock_session, "https://kroki.example.com")

        with pytest.raises(KrokiConnectionError, match="Timeout"):
            await client.async_render_diagram("graphviz", "digraph { A -> B }", "svg")
