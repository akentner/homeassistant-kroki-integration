"""Hash-based LRU file cache for Kroki rendered images."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

METADATA_FILE = "cache_meta.json"


class KrokiCache:
    """LRU file cache for Kroki rendered images.

    Images are stored on disk in the .storage/kroki/ directory.
    A metadata JSON file tracks access times for LRU eviction.
    """

    def __init__(self, storage_dir: Path, max_size: int = 50) -> None:
        """Initialize the cache.

        Args:
            storage_dir: Directory to store cached images.
            max_size: Maximum number of cached images before eviction.

        """
        self._storage_dir = storage_dir
        self._max_size = max_size
        self._metadata: dict[str, dict] = {}
        self._ensure_directory()
        self._load_metadata()

    def _ensure_directory(self) -> None:
        """Create the storage directory if it doesn't exist."""
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _metadata_path(self) -> Path:
        """Return the path to the metadata file."""
        return self._storage_dir / METADATA_FILE

    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        meta_path = self._metadata_path()
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, OSError) as err:
                _LOGGER.warning("Failed to load cache metadata, resetting: %s", err)
                self._metadata = {}
        else:
            self._metadata = {}

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            with open(self._metadata_path(), "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2)
        except OSError as err:
            _LOGGER.error("Failed to save cache metadata: %s", err)

    def _file_path(self, content_hash: str, suffix: str) -> Path:
        """Return the file path for a cached image."""
        return self._storage_dir / f"{content_hash}.{suffix}"

    def get(self, content_hash: str) -> bytes | None:
        """Retrieve a cached image by its content hash.

        Updates the access time for LRU tracking.

        Args:
            content_hash: SHA256 hash of the rendered template string.

        Returns:
            The image bytes if found, None otherwise.

        """
        if content_hash not in self._metadata:
            return None

        entry = self._metadata[content_hash]
        file_path = self._file_path(content_hash, entry["suffix"])

        if not file_path.exists():
            # File was deleted externally, clean up metadata
            del self._metadata[content_hash]
            self._save_metadata()
            return None

        # Update access time for LRU
        entry["last_access"] = time.time()
        self._save_metadata()

        try:
            return file_path.read_bytes()
        except OSError as err:
            _LOGGER.error("Failed to read cached file %s: %s", file_path, err)
            return None

    def get_suffix(self, content_hash: str) -> str | None:
        """Return the file suffix for a cached entry."""
        if content_hash in self._metadata:
            return self._metadata[content_hash].get("suffix")
        return None

    def put(self, content_hash: str, data: bytes, suffix: str) -> None:
        """Store an image in the cache.

        Args:
            content_hash: SHA256 hash of the rendered template string.
            data: The image bytes to cache.
            suffix: File suffix (e.g., "svg" or "png").

        """
        # Evict if necessary (before adding new entry)
        self._evict()

        file_path = self._file_path(content_hash, suffix)

        try:
            file_path.write_bytes(data)
        except OSError as err:
            _LOGGER.error("Failed to write cache file %s: %s", file_path, err)
            return

        self._metadata[content_hash] = {
            "suffix": suffix,
            "size": len(data),
            "created": time.time(),
            "last_access": time.time(),
        }
        self._save_metadata()

    def _evict(self) -> None:
        """Remove oldest entries if cache exceeds max size."""
        while len(self._metadata) >= self._max_size:
            # Find the entry with the oldest last_access time
            oldest_hash = min(
                self._metadata,
                key=lambda h: self._metadata[h].get("last_access", 0),
            )
            oldest_entry = self._metadata[oldest_hash]
            file_path = self._file_path(oldest_hash, oldest_entry["suffix"])

            try:
                if file_path.exists():
                    os.remove(file_path)
            except OSError as err:
                _LOGGER.warning("Failed to remove cached file %s: %s", file_path, err)

            del self._metadata[oldest_hash]
            _LOGGER.debug("Evicted cache entry: %s", oldest_hash)

        self._save_metadata()

    def clear(self) -> None:
        """Clear all cached images."""
        for content_hash, entry in list(self._metadata.items()):
            file_path = self._file_path(content_hash, entry["suffix"])
            try:
                if file_path.exists():
                    os.remove(file_path)
            except OSError as err:
                _LOGGER.warning("Failed to remove cached file %s: %s", file_path, err)

        self._metadata = {}
        self._save_metadata()
