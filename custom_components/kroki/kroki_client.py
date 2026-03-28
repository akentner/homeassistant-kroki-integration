"""Kroki API client."""

from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)

ACCEPT_HEADERS = {
    "svg": "image/svg+xml",
    "png": "image/png",
}


class KrokiError(Exception):
    """Base exception for Kroki errors."""


class KrokiConnectionError(KrokiError):
    """Exception for connection errors."""


class KrokiRenderError(KrokiError):
    """Exception for rendering errors."""


class KrokiClient:
    """Client to interact with a Kroki server."""

    def __init__(self, session: aiohttp.ClientSession, server_url: str) -> None:
        """Initialize the Kroki client."""
        self._session = session
        self._server_url = server_url.rstrip("/")

    @property
    def server_url(self) -> str:
        """Return the server URL."""
        return self._server_url

    async def async_health_check(self) -> bool:
        """Check if the Kroki server is reachable.

        Sends a simple GET request to the server root.
        Returns True if the server responds with a 2xx status.
        """
        try:
            async with self._session.get(
                f"{self._server_url}/health",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                return response.status == 200
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.debug("Health check failed for %s: %s", self._server_url, err)
            return False

    async def async_render_diagram(
        self,
        diagram_type: str,
        diagram_source: str,
        output_format: str,
    ) -> bytes:
        """Render a diagram using the Kroki API.

        Args:
            diagram_type: The type of diagram (e.g., "graphviz", "plantuml").
            diagram_source: The diagram source code.
            output_format: The output format ("svg" or "png").

        Returns:
            The rendered image as bytes.

        Raises:
            KrokiConnectionError: If the server is not reachable.
            KrokiRenderError: If the rendering fails.

        """
        url = f"{self._server_url}/{diagram_type}/{output_format}"
        headers = {
            "Content-Type": "text/plain",
            "Accept": ACCEPT_HEADERS.get(output_format, "image/svg+xml"),
        }

        try:
            async with self._session.post(
                url,
                data=diagram_source.encode("utf-8"),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    return await response.read()

                body = await response.text()
                _LOGGER.error(
                    "Kroki render failed (HTTP %s) for %s: %s",
                    response.status,
                    diagram_type,
                    body,
                )
                raise KrokiRenderError(f"Kroki returned HTTP {response.status}: {body}")
        except aiohttp.ClientError as err:
            raise KrokiConnectionError(
                f"Cannot connect to Kroki server at {self._server_url}: {err}"
            ) from err
        except TimeoutError as err:
            raise KrokiConnectionError(
                f"Timeout connecting to Kroki server at {self._server_url}"
            ) from err
