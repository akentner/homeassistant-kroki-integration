"""Tests for the Kroki image platform."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kroki.cache import KrokiCache
from custom_components.kroki.const import (
    CONF_CACHE_MAX_SIZE,
    CONF_DEFAULT_ENTITY_ID,
    CONF_DEFAULT_OUTPUT_FORMAT,
    CONF_DIAGRAM_SOURCE,
    CONF_DIAGRAM_TYPE,
    CONF_DIAGRAMS,
    CONF_OUTPUT_FORMAT,
    CONF_SERVER_URL,
    CONF_UNIQUE_ID,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SERVER_URL,
    DOMAIN,
)
from custom_components.kroki.image import (
    KrokiImageEntity,
    _compute_hash,
    _generate_error_svg,
    async_setup_platform,
)
from custom_components.kroki.kroki_client import KrokiConnectionError, KrokiRenderError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_template(hass: HomeAssistant, template_str: str) -> Template:
    """Create a Template attached to hass."""
    tpl = Template(template_str, hass)
    tpl.hass = hass
    return tpl


def _make_entity(
    hass: HomeAssistant,
    client: MagicMock,
    cache: KrokiCache,
    *,
    name: str = "Test Diagram",
    diagram_type: str = "mermaid",
    template_str: str = "graph TD; A-->B;",
    output_format: str = "svg",
    unique_id: str | None = None,
    default_entity_id: str | None = None,
) -> KrokiImageEntity:
    """Create a KrokiImageEntity for testing."""
    tpl = _make_template(hass, template_str)
    return KrokiImageEntity(
        hass=hass,
        client=client,
        cache=cache,
        name=name,
        diagram_type=diagram_type,
        diagram_source_template=tpl,
        output_format=output_format,
        unique_id=unique_id,
        default_entity_id=default_entity_id,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a mock KrokiClient."""
    client = MagicMock()
    client.server_url = DEFAULT_SERVER_URL
    client.async_render_diagram = AsyncMock(return_value=b"<svg>rendered</svg>")
    return client


@pytest.fixture
def cache(tmp_path: Path) -> KrokiCache:
    """Return a temporary KrokiCache."""
    return KrokiCache(tmp_path / "test_cache", max_size=10)


# ---------------------------------------------------------------------------
# Tests for helper functions
# ---------------------------------------------------------------------------


class TestComputeHash:
    """Tests for the _compute_hash helper."""

    def test_returns_sha256_hex(self):
        """Test that _compute_hash returns a valid SHA256 hex digest."""
        result = _compute_hash("hello", "svg")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_includes_output_format(self):
        """Test that different output formats produce different hashes."""
        svg_hash = _compute_hash("hello", "svg")
        png_hash = _compute_hash("hello", "png")
        assert svg_hash != png_hash

    def test_deterministic(self):
        """Test that the same input always gives the same hash."""
        h1 = _compute_hash("graph TD; A-->B;", "svg")
        h2 = _compute_hash("graph TD; A-->B;", "svg")
        assert h1 == h2

    def test_matches_manual_sha256(self):
        """Test that the hash matches a manually-computed SHA256."""
        content = "test content"
        fmt = "svg"
        expected = hashlib.sha256(f"{fmt}:{content}".encode()).hexdigest()
        assert _compute_hash(content, fmt) == expected


class TestGenerateErrorSvg:
    """Tests for the _generate_error_svg helper."""

    def test_returns_bytes(self):
        """Test that the result is bytes."""
        result = _generate_error_svg("Something went wrong")
        assert isinstance(result, bytes)

    def test_contains_svg_tags(self):
        """Test that the result is valid SVG-like content."""
        result = _generate_error_svg("Error message")
        text = result.decode("utf-8")
        assert text.startswith("<svg")
        assert text.endswith("</svg>")

    def test_contains_error_message(self):
        """Test that the error message appears in the SVG."""
        result = _generate_error_svg("Connection refused")
        text = result.decode("utf-8")
        assert "Connection refused" in text

    def test_escapes_html_entities(self):
        """Test that special characters are escaped."""
        result = _generate_error_svg("a < b & c > d")
        text = result.decode("utf-8")
        assert "&lt;" in text
        assert "&amp;" in text
        assert "&gt;" in text

    def test_contains_kroki_error_title(self):
        """Test that the SVG contains the 'Kroki Error' title."""
        result = _generate_error_svg("test")
        text = result.decode("utf-8")
        assert "Kroki Error" in text


# ---------------------------------------------------------------------------
# Tests for KrokiImageEntity construction
# ---------------------------------------------------------------------------


class TestKrokiImageEntityInit:
    """Tests for entity initialization."""

    def test_default_unique_id_from_name(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that unique_id is generated from name when not provided."""
        entity = _make_entity(hass, mock_client, cache, name="My Test Diagram")
        assert entity.unique_id == "kroki_my_test_diagram"

    def test_explicit_unique_id(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that explicit unique_id overrides the generated one."""
        entity = _make_entity(hass, mock_client, cache, name="My Diagram", unique_id="custom_unique_id")
        assert entity.unique_id == "custom_unique_id"

    def test_default_entity_id_sets_entity_id(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that default_entity_id sets the entity_id when given with domain prefix."""
        entity = _make_entity(hass, mock_client, cache, default_entity_id="image.my_custom_id")
        assert entity.entity_id == "image.my_custom_id"

    def test_default_entity_id_slugified(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that the object_id part of default_entity_id is slugified."""
        entity = _make_entity(hass, mock_client, cache, default_entity_id="image.My Custom ID")
        assert entity.entity_id == "image.my_custom_id"

    def test_default_entity_id_wrong_domain_raises(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that default_entity_id without 'image.' prefix raises ValueError."""
        with pytest.raises(ValueError, match="must start with 'image.'"):
            _make_entity(hass, mock_client, cache, default_entity_id="my_custom_id")

    def test_default_entity_id_wrong_domain_sensor_raises(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that default_entity_id with a wrong domain raises ValueError."""
        with pytest.raises(ValueError, match="must start with 'image.'"):
            _make_entity(hass, mock_client, cache, default_entity_id="sensor.my_diagram")

    def test_no_default_entity_id(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that entity_id is not explicitly set when default_entity_id is not given."""
        entity = _make_entity(hass, mock_client, cache)
        # entity_id should not be set to a custom value — it will be None or auto-assigned
        # We verify the entity was not explicitly set by checking it doesn't start with image.
        # (In practice HA assigns it later, but we haven't added it to hass here)
        # The key test is that no error occurs during construction
        assert entity.unique_id == "kroki_test_diagram"

    def test_svg_content_type(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that SVG output format sets the correct content type."""
        entity = _make_entity(hass, mock_client, cache, output_format="svg")
        assert entity.content_type == "image/svg+xml"

    def test_png_content_type(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that PNG output format sets the correct content type."""
        entity = _make_entity(hass, mock_client, cache, output_format="png")
        assert entity.content_type == "image/png"

    def test_initial_image_is_none(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that the initial image is None before rendering."""
        entity = _make_entity(hass, mock_client, cache)
        assert entity._current_image is None

    def test_initial_error_is_none(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that the initial error is None."""
        entity = _make_entity(hass, mock_client, cache)
        assert entity._error is None

    def test_has_entity_name(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that has_entity_name is True."""
        entity = _make_entity(hass, mock_client, cache)
        assert entity._attr_has_entity_name is True

    def test_name_attribute(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that the name attribute is set correctly."""
        entity = _make_entity(hass, mock_client, cache, name="Network Topology")
        assert entity.name == "Network Topology"


# ---------------------------------------------------------------------------
# Tests for extra_state_attributes
# ---------------------------------------------------------------------------


class TestExtraStateAttributes:
    """Tests for the extra_state_attributes property."""

    def test_initial_attributes(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test initial state attributes before any rendering."""
        entity = _make_entity(hass, mock_client, cache, output_format="svg")
        attrs = entity.extra_state_attributes

        assert attrs["diagram_type"] == "mermaid"
        assert attrs["output_format"] == "svg"
        assert attrs["last_rendered"] is None
        assert attrs["template_hash"] is None
        assert attrs["error"] is None
        assert attrs["server_url"] == DEFAULT_SERVER_URL

    def test_server_url_from_client(self, hass: HomeAssistant, cache: KrokiCache):
        """Test that server_url comes from the client."""
        client = MagicMock()
        client.server_url = "https://custom.kroki.io"
        entity = _make_entity(hass, client, cache)
        assert entity.extra_state_attributes["server_url"] == "https://custom.kroki.io"


# ---------------------------------------------------------------------------
# Tests for async_image
# ---------------------------------------------------------------------------


class TestAsyncImage:
    """Tests for the async_image method."""

    async def test_returns_none_initially(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that async_image returns None when no image has been rendered."""
        entity = _make_entity(hass, mock_client, cache)
        result = await entity.async_image()
        assert result is None

    async def test_returns_current_image(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that async_image returns the current image bytes."""
        entity = _make_entity(hass, mock_client, cache)
        entity._current_image = b"<svg>test</svg>"
        result = await entity.async_image()
        assert result == b"<svg>test</svg>"


# ---------------------------------------------------------------------------
# Tests for _async_update_image
# ---------------------------------------------------------------------------


class TestAsyncUpdateImage:
    """Tests for the _async_update_image method.

    These tests call _async_update_image directly (outside the full entity
    lifecycle), so we mock async_write_ha_state to avoid HA registration checks.
    """

    async def test_renders_via_api(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that _async_update_image calls the Kroki API and stores the result."""
        entity = _make_entity(hass, mock_client, cache, output_format="svg")
        mock_client.async_render_diagram.return_value = b"<svg>beautiful diagram</svg>"

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image("graph TD; A-->B;")

        mock_client.async_render_diagram.assert_called_once_with(
            diagram_type="mermaid",
            diagram_source="graph TD; A-->B;",
            output_format="svg",
        )
        assert entity._current_image == b"<svg>beautiful diagram</svg>"
        assert entity._error is None
        assert entity._current_hash is not None

    async def test_uses_cache_on_hit(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that _async_update_image uses cached data and skips API call."""
        entity = _make_entity(hass, mock_client, cache, output_format="svg")

        # Pre-populate cache
        source = "graph TD; A-->B;"
        content_hash = _compute_hash(source, "svg")
        cache.put(content_hash, b"<svg>cached diagram</svg>", "svg")

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image(source)

        # API should NOT be called
        mock_client.async_render_diagram.assert_not_called()
        assert entity._current_image == b"<svg>cached diagram</svg>"
        assert entity._error is None

    async def test_skips_update_when_hash_unchanged(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that _async_update_image skips when content hash hasn't changed."""
        entity = _make_entity(hass, mock_client, cache)

        with patch.object(entity, "async_write_ha_state"):
            # First render
            await entity._async_update_image("graph TD; A-->B;")
            assert mock_client.async_render_diagram.call_count == 1

            # Same content again
            await entity._async_update_image("graph TD; A-->B;")
            # Should still be 1 call (skipped)
            assert mock_client.async_render_diagram.call_count == 1

    async def test_stores_in_cache_after_render(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that rendered images are stored in the cache."""
        entity = _make_entity(hass, mock_client, cache, output_format="svg")
        mock_client.async_render_diagram.return_value = b"<svg>new</svg>"

        source = "graph TD; X-->Y;"
        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image(source)

        content_hash = _compute_hash(source, "svg")
        cached = cache.get(content_hash)
        assert cached == b"<svg>new</svg>"

    async def test_connection_error_produces_error_svg(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that a connection error results in an error SVG."""
        entity = _make_entity(hass, mock_client, cache)
        mock_client.async_render_diagram.side_effect = KrokiConnectionError("Connection refused")

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image("graph TD; A-->B;")

        assert entity._error == "Connection refused"
        assert entity._current_image is not None
        assert b"Connection refused" in entity._current_image
        assert entity._attr_content_type == "image/svg+xml"

    async def test_render_error_produces_error_svg(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that a render error results in an error SVG."""
        entity = _make_entity(hass, mock_client, cache)
        mock_client.async_render_diagram.side_effect = KrokiRenderError("Invalid syntax")

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image("bad diagram source")

        assert entity._error == "Invalid syntax"
        assert entity._current_image is not None
        assert b"Invalid syntax" in entity._current_image

    async def test_updates_last_rendered(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that _last_rendered is updated after successful render."""
        entity = _make_entity(hass, mock_client, cache)
        assert entity._last_rendered is None

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image("graph TD; A-->B;")

        assert entity._last_rendered is not None

    async def test_updates_image_last_updated(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that image_last_updated is set after render."""
        entity = _make_entity(hass, mock_client, cache)

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image("graph TD; A-->B;")

        assert entity.image_last_updated is not None

    async def test_content_type_restored_after_error_then_success(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that content type is restored to PNG after an error (which forces SVG) then success."""
        entity = _make_entity(hass, mock_client, cache, output_format="png")

        with patch.object(entity, "async_write_ha_state"):
            # First: error → forces SVG content type
            mock_client.async_render_diagram.side_effect = KrokiConnectionError("fail")
            await entity._async_update_image("source1")
            assert entity._attr_content_type == "image/svg+xml"

            # Second: success → should restore PNG content type
            mock_client.async_render_diagram.side_effect = None
            mock_client.async_render_diagram.return_value = b"\x89PNG..."
            await entity._async_update_image("source2")
            assert entity._attr_content_type == "image/png"

    async def test_different_source_triggers_new_render(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that a different source triggers a new API call."""
        entity = _make_entity(hass, mock_client, cache)

        with patch.object(entity, "async_write_ha_state"):
            await entity._async_update_image("source A")
            assert mock_client.async_render_diagram.call_count == 1

            await entity._async_update_image("source B")
            assert mock_client.async_render_diagram.call_count == 2


# ---------------------------------------------------------------------------
# Tests for async_added_to_hass / async_will_remove_from_hass
# ---------------------------------------------------------------------------


class TestTemplateTracking:
    """Tests for template tracking lifecycle."""

    async def test_added_to_hass_sets_up_tracking(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that async_added_to_hass sets up template tracking."""
        entity = _make_entity(hass, mock_client, cache, template_str="static content")
        entity.hass = hass
        entity.entity_id = "image.test_diagram"

        with patch.object(entity, "async_write_ha_state"):
            await entity.async_added_to_hass()

        assert entity._unsub_track is not None
        # Allow the template render task to complete
        await hass.async_block_till_done()

    async def test_remove_from_hass_cleans_up(self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache):
        """Test that async_will_remove_from_hass cleans up tracking."""
        entity = _make_entity(hass, mock_client, cache, template_str="static content")
        entity.hass = hass
        entity.entity_id = "image.test_diagram"

        with patch.object(entity, "async_write_ha_state"):
            await entity.async_added_to_hass()
            await hass.async_block_till_done()

        assert entity._unsub_track is not None

        await entity.async_will_remove_from_hass()
        assert entity._unsub_track is None

    async def test_remove_from_hass_noop_when_no_tracking(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that async_will_remove_from_hass is safe when no tracking exists."""
        entity = _make_entity(hass, mock_client, cache)
        assert entity._unsub_track is None

        # Should not raise
        await entity.async_will_remove_from_hass()
        assert entity._unsub_track is None

    async def test_template_render_triggers_update(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that template tracking triggers _async_update_image on initial render."""
        mock_client.async_render_diagram.return_value = b"<svg>initial</svg>"
        entity = _make_entity(hass, mock_client, cache, template_str="graph TD; A-->B;")
        entity.hass = hass
        entity.entity_id = "image.test_diagram"

        with patch.object(entity, "async_write_ha_state"):
            await entity.async_added_to_hass()
            await hass.async_block_till_done()

        # The initial template render should have triggered an API call
        mock_client.async_render_diagram.assert_called_once()
        assert entity._current_image == b"<svg>initial</svg>"

        # Cleanup
        await entity.async_will_remove_from_hass()

    async def test_template_error_produces_error_svg(
        self, hass: HomeAssistant, mock_client: MagicMock, cache: KrokiCache
    ):
        """Test that a template rendering error produces an error SVG."""
        # Use a template that will fail
        entity = _make_entity(hass, mock_client, cache, template_str="{{ invalid_func() }}")
        entity.hass = hass
        entity.entity_id = "image.test_diagram"

        with patch.object(entity, "async_write_ha_state"):
            await entity.async_added_to_hass()
            await hass.async_block_till_done()

        # Should have an error SVG, not call the API
        mock_client.async_render_diagram.assert_not_called()
        assert entity._error is not None
        assert entity._current_image is not None
        assert b"Kroki Error" in entity._current_image

        # Cleanup
        await entity.async_will_remove_from_hass()


# ---------------------------------------------------------------------------
# Tests for async_setup_platform
# ---------------------------------------------------------------------------


class TestAsyncSetupPlatform:
    """Tests for the async_setup_platform function."""

    async def test_setup_with_no_config_entry_uses_defaults(self, hass: HomeAssistant, tmp_path: Path):
        """Test platform setup without config entry uses default server URL."""
        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl = Template("graph TD; A-->B;", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "My Diagram",
                    CONF_DIAGRAM_TYPE: "mermaid",
                    CONF_DIAGRAM_SOURCE: tpl,
                    CONF_OUTPUT_FORMAT: DEFAULT_OUTPUT_FORMAT,
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession") as mock_session,
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache"),
        ):
            mock_session.return_value = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = DEFAULT_SERVER_URL
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 1
        entity = added_entities[0]
        assert entity.name == "My Diagram"
        assert entity.unique_id == "kroki_my_diagram"
        # Client should have been created with default server URL
        mock_client_cls.assert_called_once_with(mock_session.return_value, DEFAULT_SERVER_URL)

    async def test_setup_with_config_entry_uses_entry_data(self, hass: HomeAssistant, tmp_path: Path):
        """Test platform setup with a config entry uses the entry's server URL."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: "https://custom.kroki.io"},
            options={CONF_CACHE_MAX_SIZE: 100, CONF_DEFAULT_OUTPUT_FORMAT: "png"},
            unique_id="https://custom.kroki.io",
        )
        entry.add_to_hass(hass)

        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl = Template("graph TD; X-->Y;", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "Custom Diagram",
                    CONF_DIAGRAM_TYPE: "plantuml",
                    CONF_DIAGRAM_SOURCE: tpl,
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession") as mock_session,
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache") as mock_cache_cls,
        ):
            mock_session.return_value = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = "https://custom.kroki.io"
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 1
        entity = added_entities[0]
        assert entity.name == "Custom Diagram"
        mock_client_cls.assert_called_once_with(mock_session.return_value, "https://custom.kroki.io")
        mock_cache_cls.assert_called_once()
        # Cache should be created with the entry's max_size
        _, kwargs = mock_cache_cls.call_args
        assert kwargs["max_size"] == 100

    async def test_setup_multiple_diagrams(self, hass: HomeAssistant, tmp_path: Path):
        """Test platform setup with multiple diagram configurations."""
        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl1 = Template("graph TD; A-->B;", hass)
        tpl2 = Template("sequenceDiagram", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "Diagram One",
                    CONF_DIAGRAM_TYPE: "mermaid",
                    CONF_DIAGRAM_SOURCE: tpl1,
                    CONF_OUTPUT_FORMAT: "svg",
                },
                {
                    CONF_NAME: "Diagram Two",
                    CONF_DIAGRAM_TYPE: "plantuml",
                    CONF_DIAGRAM_SOURCE: tpl2,
                    CONF_OUTPUT_FORMAT: "png",
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession"),
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache"),
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = DEFAULT_SERVER_URL
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 2
        assert added_entities[0].name == "Diagram One"
        assert added_entities[1].name == "Diagram Two"

    async def test_setup_with_explicit_unique_id(self, hass: HomeAssistant, tmp_path: Path):
        """Test platform setup passes unique_id through to entity."""
        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl = Template("graph TD; A-->B;", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "My Diagram",
                    CONF_DIAGRAM_TYPE: "mermaid",
                    CONF_DIAGRAM_SOURCE: tpl,
                    CONF_OUTPUT_FORMAT: "svg",
                    CONF_UNIQUE_ID: "my_explicit_id",
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession"),
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache"),
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = DEFAULT_SERVER_URL
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 1
        assert added_entities[0].unique_id == "my_explicit_id"

    async def test_setup_with_default_entity_id(self, hass: HomeAssistant, tmp_path: Path):
        """Test platform setup passes default_entity_id through to entity."""
        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl = Template("graph TD; A-->B;", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "My Diagram",
                    CONF_DIAGRAM_TYPE: "mermaid",
                    CONF_DIAGRAM_SOURCE: tpl,
                    CONF_OUTPUT_FORMAT: "svg",
                    CONF_DEFAULT_ENTITY_ID: "image.network_topology",
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession"),
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache"),
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = DEFAULT_SERVER_URL
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 1
        assert added_entities[0].entity_id == "image.network_topology"

    async def test_setup_diagram_specific_format_overrides_entry_default(self, hass: HomeAssistant, tmp_path: Path):
        """Test that diagram-specific output_format overrides the entry default."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: DEFAULT_SERVER_URL},
            options={CONF_DEFAULT_OUTPUT_FORMAT: "png"},
            unique_id=DEFAULT_SERVER_URL,
        )
        entry.add_to_hass(hass)

        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl = Template("graph TD; A-->B;", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "SVG Override",
                    CONF_DIAGRAM_TYPE: "mermaid",
                    CONF_DIAGRAM_SOURCE: tpl,
                    CONF_OUTPUT_FORMAT: "svg",  # Explicitly override entry default of PNG
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession"),
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache"),
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = DEFAULT_SERVER_URL
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 1
        assert added_entities[0]._output_format == "svg"
        assert added_entities[0].content_type == "image/svg+xml"

    async def test_setup_uses_entry_default_format_when_not_specified(self, hass: HomeAssistant, tmp_path: Path):
        """Test that diagrams without output_format use the entry's default."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: DEFAULT_SERVER_URL},
            options={CONF_DEFAULT_OUTPUT_FORMAT: "png"},
            unique_id=DEFAULT_SERVER_URL,
        )
        entry.add_to_hass(hass)

        added_entities: list[KrokiImageEntity] = []

        def capture_entities(entities):
            added_entities.extend(entities)

        tpl = Template("graph TD; A-->B;", hass)

        config = {
            CONF_DIAGRAMS: [
                {
                    CONF_NAME: "Default Format",
                    CONF_DIAGRAM_TYPE: "mermaid",
                    CONF_DIAGRAM_SOURCE: tpl,
                    # No CONF_OUTPUT_FORMAT → should use entry default "png"
                },
            ],
        }

        with (
            patch("custom_components.kroki.image.async_get_clientsession"),
            patch("custom_components.kroki.image.KrokiClient") as mock_client_cls,
            patch("custom_components.kroki.image.KrokiCache"),
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.server_url = DEFAULT_SERVER_URL
            mock_client_cls.return_value = mock_client_instance

            await async_setup_platform(hass, config, capture_entities)

        assert len(added_entities) == 1
        assert added_entities[0]._output_format == "png"
        assert added_entities[0].content_type == "image/png"


# ---------------------------------------------------------------------------
# Tests for async_setup_entry (GUI path)
# ---------------------------------------------------------------------------


class TestAsyncSetupEntry:
    """Tests for the async_setup_entry function (GUI diagram entities)."""

    async def test_async_setup_entry_creates_entities_for_subentries(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test that async_setup_entry creates one entity per diagram subentry."""
        from homeassistant.config_entries import ConfigSubentryDataWithId

        from custom_components.kroki.cache import KrokiCache
        from custom_components.kroki.image import KrokiImageEntity, async_setup_entry

        subentry_id = "01JTEST00000000000000000001"
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: "https://kroki.example.com"},
            options={},
            subentries_data=(
                ConfigSubentryDataWithId(
                    subentry_id=subentry_id,
                    subentry_type="diagram",
                    title="My Mermaid",
                    data={
                        CONF_DIAGRAM_TYPE: "mermaid",
                        CONF_DIAGRAM_SOURCE: "graph TD\nA-->B",
                        CONF_OUTPUT_FORMAT: "svg",
                    },
                    unique_id=None,
                ),
            ),
        )
        entry.add_to_hass(hass)

        # Pre-populate hass.data as __init__.async_setup_entry would
        cache = MagicMock(spec=KrokiCache)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": mock_kroki_client,
            "cache": cache,
        }

        entities_added = []

        def mock_add_entities(entities, **kwargs):
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(entities_added) == 1
        entity = entities_added[0]
        assert isinstance(entity, KrokiImageEntity)
        assert entity._attr_unique_id == subentry_id
        assert entity._attr_name == "My Mermaid"
        assert entity._diagram_type == "mermaid"

    async def test_async_setup_entry_skips_non_diagram_subentries(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock
    ) -> None:
        """Test that subentries with wrong type are skipped."""
        from homeassistant.config_entries import ConfigSubentryDataWithId

        from custom_components.kroki.cache import KrokiCache
        from custom_components.kroki.image import async_setup_entry

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: "https://kroki.example.com"},
            subentries_data=(
                ConfigSubentryDataWithId(
                    subentry_id="01JTEST00000000000000000002",
                    subentry_type="other_type",
                    title="Not a diagram",
                    data={},
                    unique_id=None,
                ),
            ),
        )
        entry.add_to_hass(hass)
        cache = MagicMock(spec=KrokiCache)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": mock_kroki_client,
            "cache": cache,
        }

        entities_added = []

        def mock_add_entities(entities, **kwargs):
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)
        assert len(entities_added) == 0

    async def test_async_setup_entry_no_subentries_creates_no_entities(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock
    ) -> None:
        """Test that no entities are created when there are no subentries."""
        from custom_components.kroki.cache import KrokiCache
        from custom_components.kroki.image import async_setup_entry

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: "https://kroki.example.com"},
        )
        entry.add_to_hass(hass)
        cache = MagicMock(spec=KrokiCache)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": mock_kroki_client,
            "cache": cache,
        }

        entities_added = []

        def mock_add_entities(entities, **kwargs):
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)
        assert len(entities_added) == 0

    async def test_async_setup_entry_adds_entity_when_subentry_added_dynamically(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock
    ) -> None:
        """Entity appears immediately when a subentry is added after setup — no reload required."""
        from homeassistant.config_entries import ConfigSubentry, ConfigSubentryDataWithId

        from custom_components.kroki.cache import KrokiCache
        from custom_components.kroki.image import KrokiImageEntity, async_setup_entry

        # Start with one existing subentry
        existing_id = "01JTEST00000000000000000010"
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SERVER_URL: "https://kroki.example.com"},
            options={},
            subentries_data=(
                ConfigSubentryDataWithId(
                    subentry_id=existing_id,
                    subentry_type="diagram",
                    title="Existing",
                    data={CONF_DIAGRAM_TYPE: "mermaid", CONF_DIAGRAM_SOURCE: "A-->B", CONF_OUTPUT_FORMAT: "svg"},
                    unique_id=None,
                ),
            ),
        )
        entry.add_to_hass(hass)
        cache = MagicMock(spec=KrokiCache)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {"client": mock_kroki_client, "cache": cache}

        entities_added = []

        def mock_add_entities(entities, **kwargs):
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)
        assert len(entities_added) == 1  # existing subentry set up

        # Dynamically add a new subentry via HA's config entries API
        new_id = "01JTEST00000000000000000011"
        new_subentry = ConfigSubentry(
            subentry_id=new_id,
            subentry_type="diagram",
            title="New Diagram",
            data={CONF_DIAGRAM_TYPE: "graphviz", CONF_DIAGRAM_SOURCE: "digraph {}", CONF_OUTPUT_FORMAT: "png"},
            unique_id=None,
        )
        hass.config_entries.async_add_subentry(entry, new_subentry)
        await hass.async_block_till_done()

        assert len(entities_added) == 2
        new_entity = entities_added[1]
        assert isinstance(new_entity, KrokiImageEntity)
        assert new_entity._attr_unique_id == new_id
        assert new_entity._attr_name == "New Diagram"


# ---------------------------------------------------------------------------
# Tests for KrokiImageEntity.from_subentry (GUI entity factory)
# ---------------------------------------------------------------------------


class TestFromSubentry:
    """Tests for KrokiImageEntity.from_subentry class method."""

    def test_from_subentry_unique_id_is_subentry_id(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock, mock_config_subentry
    ) -> None:
        """Test that from_subentry sets unique_id = subentry_id (not name-derived). Pitfall 1."""
        from custom_components.kroki.cache import KrokiCache

        cache = MagicMock(spec=KrokiCache)
        entity = KrokiImageEntity.from_subentry(hass, mock_kroki_client, cache, mock_config_subentry, "svg")

        assert entity._attr_unique_id == mock_config_subentry.subentry_id
        # Must NOT be name-derived (Pitfall 1)
        assert entity._attr_unique_id != f"kroki_{mock_config_subentry.title.lower().replace(' ', '_')}"

    def test_from_subentry_and_yaml_unique_ids_do_not_collide(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock
    ) -> None:
        """Test that GUI (subentry_id) and YAML (kroki_slugified) unique_ids never collide. Pitfall 1."""
        from homeassistant.config_entries import ConfigSubentry
        from homeassistant.helpers.template import Template

        from custom_components.kroki.cache import KrokiCache

        cache = MagicMock(spec=KrokiCache)

        # GUI entity: uses subentry_id as unique_id
        subentry = ConfigSubentry(
            subentry_id="01JTEST00000000000000000003",
            subentry_type="diagram",
            title="Network",  # same name as YAML entity below
            data={
                CONF_DIAGRAM_TYPE: "mermaid",
                CONF_DIAGRAM_SOURCE: "graph TD\nA-->B",
                CONF_OUTPUT_FORMAT: "svg",
            },
            unique_id=None,
        )
        gui_entity = KrokiImageEntity.from_subentry(hass, mock_kroki_client, cache, subentry, "svg")

        # YAML entity: uses name-derived unique_id "kroki_network"
        yaml_entity = KrokiImageEntity(
            hass=hass,
            client=mock_kroki_client,
            cache=cache,
            name="Network",
            diagram_type="mermaid",
            diagram_source_template=Template("graph TD\nA-->B", hass),
            output_format="svg",
        )

        # unique_ids must differ
        assert gui_entity._attr_unique_id != yaml_entity._attr_unique_id
        # GUI entity uses ULID (subentry_id), not name-derived
        assert gui_entity._attr_unique_id == "01JTEST00000000000000000003"
        assert yaml_entity._attr_unique_id == "kroki_network"

    def test_from_subentry_server_default_format_resolved(
        self, hass: HomeAssistant, mock_kroki_client: MagicMock
    ) -> None:
        """Test that from_subentry uses the effective_output_format parameter."""
        from homeassistant.config_entries import ConfigSubentry

        from custom_components.kroki.cache import KrokiCache

        cache = MagicMock(spec=KrokiCache)

        subentry = ConfigSubentry(
            subentry_id="01JTEST00000000000000000004",
            subentry_type="diagram",
            title="PNG Diagram",
            data={
                CONF_DIAGRAM_TYPE: "plantuml",
                CONF_DIAGRAM_SOURCE: "@startuml\nA->B\n@enduml",
                CONF_OUTPUT_FORMAT: "server_default",
            },
            unique_id=None,
        )
        # The caller (async_setup_entry) resolves server_default → effective_output_format
        entity = KrokiImageEntity.from_subentry(hass, mock_kroki_client, cache, subentry, "png")

        assert entity._output_format == "png"
        assert entity.content_type == "image/png"


# ---------------------------------------------------------------------------
# KrokiImageEntity.async_force_render()
# ---------------------------------------------------------------------------


async def test_force_render_clears_state_and_triggers_refresh(hass: HomeAssistant, mock_kroki_client, tmp_path) -> None:
    """force_render clears hash, evicts cache, clears image, triggers refresh."""
    from unittest.mock import MagicMock

    cache = KrokiCache(tmp_path / "test_cache_fr1", max_size=10)
    entity = _make_entity(hass, mock_kroki_client, cache)

    # Simulate a previously rendered state
    entity._current_hash = "somehash"
    entity._current_image = b"<svg/>"

    mock_unsub = MagicMock()
    entity._unsub_track = mock_unsub

    # Seed the cache with the current hash so evict has something to remove
    cache.put("somehash", b"<svg/>", "svg")

    await entity.async_force_render()

    assert entity._current_hash is None
    assert entity._current_image is None
    assert cache.get("somehash") is None  # disk cache evicted
    mock_unsub.async_refresh.assert_called_once()


async def test_force_render_noop_evict_when_no_hash(hass: HomeAssistant, mock_kroki_client, tmp_path) -> None:
    """force_render skips disk eviction when entity has never rendered (D-04)."""
    from unittest.mock import MagicMock

    cache = KrokiCache(tmp_path / "test_cache_fr2", max_size=10)
    entity = _make_entity(hass, mock_kroki_client, cache)

    # Entity has never rendered: _current_hash is None
    assert entity._current_hash is None

    mock_unsub = MagicMock()
    entity._unsub_track = mock_unsub

    await entity.async_force_render()

    # State cleared
    assert entity._current_hash is None
    assert entity._current_image is None
    # Refresh still triggered
    mock_unsub.async_refresh.assert_called_once()


async def test_force_render_does_nothing_if_no_tracker(hass: HomeAssistant, mock_kroki_client, tmp_path) -> None:
    """force_render is safe to call before entity is added to hass."""
    cache = KrokiCache(tmp_path / "test_cache_fr3", max_size=10)
    entity = _make_entity(hass, mock_kroki_client, cache)
    entity._unsub_track = None  # not yet added to hass

    # Must not raise
    await entity.async_force_render()
    assert entity._current_hash is None
