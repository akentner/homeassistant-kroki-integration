"""Image platform for the Kroki integration."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback, AddEntitiesCallback
from homeassistant.helpers.event import TrackTemplate, async_track_template_result
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from .cache import KrokiCache
from .const import (
    CONF_CACHE_MAX_SIZE,
    CONF_DEFAULT_ENTITY_ID,
    CONF_DEFAULT_OUTPUT_FORMAT,
    CONF_DIAGRAM_SOURCE,
    CONF_DIAGRAM_TYPE,
    CONF_DIAGRAMS,
    CONF_OUTPUT_FORMAT,
    CONF_SERVER_URL,
    CONF_UNIQUE_ID,
    CONTENT_TYPE_MAP,
    DEFAULT_CACHE_MAX_SIZE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SERVER_URL,
    DOMAIN,
    SUPPORTED_DIAGRAM_TYPES,
)
from .kroki_client import KrokiClient, KrokiConnectionError, KrokiRenderError

_LOGGER = logging.getLogger(__name__)

DIAGRAM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DIAGRAM_TYPE): vol.In(SUPPORTED_DIAGRAM_TYPES),
        vol.Required(CONF_DIAGRAM_SOURCE): cv.template,
        vol.Optional(CONF_OUTPUT_FORMAT, default=DEFAULT_OUTPUT_FORMAT): vol.In(["svg", "png"]),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_DEFAULT_ENTITY_ID): cv.string,
    }
)

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DIAGRAMS): vol.All(cv.ensure_list, [DIAGRAM_SCHEMA]),
    }
)


def _generate_error_svg(message: str) -> bytes:
    """Generate a simple SVG image displaying an error message."""
    escaped = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">'
        '<rect width="400" height="100" fill="#fff3f3" stroke="#cc0000" '
        'stroke-width="2" rx="8"/>'
        '<text x="200" y="35" text-anchor="middle" font-family="monospace" '
        'font-size="14" fill="#cc0000" font-weight="bold">Kroki Error</text>'
        f'<text x="200" y="60" text-anchor="middle" font-family="monospace" '
        f'font-size="11" fill="#333">{escaped}</text>'
        "</svg>"
    )
    return svg.encode("utf-8")


def _compute_hash(content: str, output_format: str) -> str:
    """Compute SHA256 hash of diagram content and output format."""
    raw = f"{output_format}:{content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Kroki image entities from YAML configuration."""
    # Determine which Kroki server and options to use.
    # Use the first configured config entry, or fall back to defaults.
    # Per D-11: reuse shared client and cache from hass.data if available.
    server_url = DEFAULT_SERVER_URL
    cache_max_size = DEFAULT_CACHE_MAX_SIZE
    default_output_format = DEFAULT_OUTPUT_FORMAT

    config_entries = hass.config_entries.async_entries(DOMAIN)
    if config_entries:
        entry = config_entries[0]
        server_url = entry.data.get(CONF_SERVER_URL, DEFAULT_SERVER_URL)
        cache_max_size = entry.options.get(CONF_CACHE_MAX_SIZE, DEFAULT_CACHE_MAX_SIZE)
        default_output_format = entry.options.get(CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT)
        # Reuse shared client and cache from hass.data if available (D-11)
        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if entry_data:
            client = entry_data["client"]
            cache = entry_data["cache"]
        else:
            session = async_get_clientsession(hass)
            client = KrokiClient(session, server_url)
            cache_dir = Path(hass.config.path(".storage")) / DOMAIN
            cache = KrokiCache(cache_dir, max_size=cache_max_size)
    else:
        session = async_get_clientsession(hass)
        client = KrokiClient(session, DEFAULT_SERVER_URL)
        cache_dir = Path(hass.config.path(".storage")) / DOMAIN
        cache = KrokiCache(cache_dir, max_size=DEFAULT_CACHE_MAX_SIZE)
        default_output_format = DEFAULT_OUTPUT_FORMAT

    entities: list[KrokiImageEntity] = []
    for diagram_config in config[CONF_DIAGRAMS]:
        # Use diagram-specific output format, or fall back to entry option
        output_format = diagram_config.get(CONF_OUTPUT_FORMAT, default_output_format)
        entities.append(
            KrokiImageEntity(
                hass=hass,
                client=client,
                cache=cache,
                name=diagram_config[CONF_NAME],
                diagram_type=diagram_config[CONF_DIAGRAM_TYPE],
                diagram_source_template=diagram_config[CONF_DIAGRAM_SOURCE],
                output_format=output_format,
                unique_id=diagram_config.get(CONF_UNIQUE_ID),
                default_entity_id=diagram_config.get(CONF_DEFAULT_ENTITY_ID),
            )
        )

    async_add_entities(entities)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up GUI-managed diagram entities from config entry subentries."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    client: KrokiClient = entry_data["client"]
    cache: KrokiCache = entry_data["cache"]

    def _create_entity(subentry: ConfigSubentry) -> KrokiImageEntity:
        output_format_raw = subentry.data.get(CONF_OUTPUT_FORMAT)
        effective_output_format = (
            output_format_raw
            if output_format_raw in ("svg", "png")
            else config_entry.options.get(CONF_DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_FORMAT)
        )
        return KrokiImageEntity.from_subentry(hass, client, cache, subentry, effective_output_format)

    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "diagram":
            continue
        async_add_entities([_create_entity(subentry)], config_subentry_id=subentry.subentry_id)

    known_subentry_ids: set[str] = {
        sid for sid, sub in config_entry.subentries.items() if sub.subentry_type == "diagram"
    }

    async def _async_handle_entry_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
        nonlocal known_subentry_ids
        current_ids = {sid for sid, sub in entry.subentries.items() if sub.subentry_type == "diagram"}
        new_ids = current_ids - known_subentry_ids
        known_subentry_ids = current_ids
        for subentry_id in new_ids:
            async_add_entities([_create_entity(entry.subentries[subentry_id])], config_subentry_id=subentry_id)

    config_entry.async_on_unload(config_entry.add_update_listener(_async_handle_entry_update))


class KrokiImageEntity(ImageEntity):
    """Representation of a Kroki diagram as an Image entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        client: KrokiClient,
        cache: KrokiCache,
        name: str,
        diagram_type: str,
        diagram_source_template: Template,
        output_format: str,
        unique_id: str | None = None,
        default_entity_id: str | None = None,
    ) -> None:
        """Initialize the Kroki image entity."""
        super().__init__(hass)
        self._client = client
        self._cache = cache
        self._attr_name = name
        self._diagram_type = diagram_type
        self._source_template = diagram_source_template
        self._source_template.hass = hass
        self._output_format = output_format

        # Image state
        self._current_image: bytes | None = None
        self._current_hash: str | None = None
        self._last_rendered: datetime | None = None
        self._error: str | None = None
        self._unsub_track: callback | None = None

        # Content type based on output format
        self._attr_content_type = CONTENT_TYPE_MAP.get(output_format, "image/svg+xml")

        # Unique ID: use explicit value from YAML, or generate from name
        self._attr_unique_id = unique_id if unique_id else f"kroki_{cv.slugify(name)}"

        # Default entity ID: must be provided as "image.<object_id>"
        if default_entity_id:
            if not default_entity_id.startswith("image."):
                raise ValueError(f"default_entity_id must start with 'image.' (got: '{default_entity_id}')")
            self.entity_id = f"image.{cv.slugify(default_entity_id[len('image.') :])}"

    @classmethod
    def from_subentry(
        cls,
        hass: HomeAssistant,
        client: KrokiClient,
        cache: KrokiCache,
        subentry: ConfigSubentry,
        effective_output_format: str,
    ) -> KrokiImageEntity:
        """Create a KrokiImageEntity from a config subentry (GUI path).

        Uses subentry.subentry_id as unique_id (stable ULID, never name-derived)
        to prevent entity registry collisions with YAML entities (Pitfall 1, D-08).
        """
        source = subentry.data[CONF_DIAGRAM_SOURCE]
        diagram_type = subentry.data[CONF_DIAGRAM_TYPE]
        # Wrap raw source string in a Template object (YAML path uses cv.template which does this)
        source_template = Template(source, hass)

        return cls(
            hass=hass,
            client=client,
            cache=cache,
            name=subentry.title,
            diagram_type=diagram_type,
            diagram_source_template=source_template,
            output_format=effective_output_format,
            unique_id=subentry.subentry_id,  # stable ULID, never name-derived (D-08, Pitfall 1)
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "diagram_type": self._diagram_type,
            "output_format": self._output_format,
            "last_rendered": (self._last_rendered.isoformat() if self._last_rendered else None),
            "template_hash": self._current_hash,
            "error": self._error,
            "server_url": self._client.server_url,
        }

    async def async_added_to_hass(self) -> None:
        """Start tracking template changes when entity is added."""
        await super().async_added_to_hass()

        # Set up template tracking
        track_template = TrackTemplate(self._source_template, None, None)

        @callback
        def _async_template_result_changed(event: Any, updates: list[Any]) -> None:
            """Handle template result changes."""
            for update in updates:
                result = update.result
                if isinstance(result, Exception):
                    _LOGGER.error(
                        "Error rendering template for %s: %s",
                        self._attr_name,
                        result,
                    )
                    self._error = str(result)
                    self._current_image = _generate_error_svg(f"Template error: {result}")
                    self._attr_content_type = "image/svg+xml"
                    self._attr_image_last_updated = dt_util.utcnow()
                    self.async_write_ha_state()
                    return

                # Template rendered successfully
                self.hass.async_create_task(self._async_update_image(str(result)))

        self._unsub_track = async_track_template_result(
            self.hass,
            [track_template],
            _async_template_result_changed,
        )

        # Trigger initial render
        self._unsub_track.async_refresh()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up template tracking when entity is removed."""
        if self._unsub_track is not None:
            self._unsub_track.async_remove()
            self._unsub_track = None

    async def async_force_render(self) -> None:
        """Force an immediate re-render, bypassing hash dedup and disk cache.

        Clears in-memory hash, evicts the disk cache entry for the current hash
        (if any), clears the current image, and triggers a fresh template
        evaluation cycle via the template tracker.

        Per D-04: disk eviction is skipped silently if no hash is known yet.
        Per D-08: logs at DEBUG level on each call.
        """
        _LOGGER.debug("force_render called for %s", self.entity_id)

        old_hash = self._current_hash

        # Wipe in-memory state (D-03 steps 1 and 3)
        self._current_hash = None
        self._current_image = None

        # Evict disk cache entry only if a hash is known (D-04)
        if old_hash is not None:
            self._cache.evict(old_hash)

        # Trigger fresh template evaluation and re-render cycle (D-03 step 4)
        if self._unsub_track is not None:
            self._unsub_track.async_refresh()

    async def _async_update_image(self, rendered_source: str) -> None:
        """Update the image from the rendered template source.

        Checks the cache first, then calls the Kroki API if needed.
        """
        content_hash = _compute_hash(rendered_source, self._output_format)

        # Skip if hash hasn't changed
        if content_hash == self._current_hash and self._current_image is not None:
            return

        # Check cache
        cached_image = self._cache.get(content_hash)
        if cached_image is not None:
            _LOGGER.debug(
                "Cache hit for %s (hash: %s...)",
                self._attr_name,
                content_hash[:12],
            )
            self._current_image = cached_image
            self._current_hash = content_hash
            self._last_rendered = dt_util.utcnow()
            self._error = None
            self._attr_image_last_updated = dt_util.utcnow()
            self.async_write_ha_state()
            return

        # Cache miss - render via Kroki API
        _LOGGER.debug(
            "Cache miss for %s (hash: %s...), rendering via Kroki",
            self._attr_name,
            content_hash[:12],
        )

        try:
            image_data = await self._client.async_render_diagram(
                diagram_type=self._diagram_type,
                diagram_source=rendered_source,
                output_format=self._output_format,
            )
        except (KrokiConnectionError, KrokiRenderError) as err:
            _LOGGER.error("Failed to render diagram %s: %s", self._attr_name, err)
            self._error = str(err)
            self._current_image = _generate_error_svg(str(err))
            self._attr_content_type = "image/svg+xml"
            self._attr_image_last_updated = dt_util.utcnow()
            self.async_write_ha_state()
            return

        # Store in cache
        self._cache.put(content_hash, image_data, self._output_format)

        # Update entity state
        self._current_image = image_data
        self._current_hash = content_hash
        self._last_rendered = dt_util.utcnow()
        self._error = None
        self._attr_content_type = CONTENT_TYPE_MAP.get(self._output_format, "image/svg+xml")
        self._attr_image_last_updated = dt_util.utcnow()
        self.async_write_ha_state()

    async def async_image(self) -> bytes | None:
        """Return the current image bytes."""
        return self._current_image
