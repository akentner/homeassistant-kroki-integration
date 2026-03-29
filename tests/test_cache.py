"""Tests for the Kroki file cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.kroki.cache import METADATA_FILE, KrokiCache


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """Return a temporary cache directory."""
    return tmp_path / "kroki_cache"


@pytest.fixture
def cache(cache_dir: Path) -> KrokiCache:
    """Return a KrokiCache with default settings."""
    return KrokiCache(cache_dir, max_size=5)


class TestCacheInit:
    """Tests for cache initialization."""

    def test_creates_directory(self, cache_dir: Path):
        """Test that the cache creates the storage directory."""
        assert not cache_dir.exists()
        KrokiCache(cache_dir)
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_loads_existing_metadata(self, cache_dir: Path):
        """Test that existing metadata is loaded on init."""
        cache_dir.mkdir(parents=True)
        meta = {"abc123": {"suffix": "svg", "size": 100, "created": 1.0, "last_access": 2.0}}
        (cache_dir / METADATA_FILE).write_text(json.dumps(meta))

        # Also create the file
        (cache_dir / "abc123.svg").write_bytes(b"<svg/>")

        cache = KrokiCache(cache_dir)
        result = cache.get("abc123")
        assert result == b"<svg/>"

    def test_handles_corrupt_metadata(self, cache_dir: Path):
        """Test that corrupt metadata is handled gracefully."""
        cache_dir.mkdir(parents=True)
        (cache_dir / METADATA_FILE).write_text("not valid json {{{")

        # Should not raise
        cache = KrokiCache(cache_dir)
        assert cache.get("anything") is None


class TestCachePutGet:
    """Tests for put and get operations."""

    def test_put_and_get_svg(self, cache: KrokiCache):
        """Test storing and retrieving an SVG image."""
        data = b"<svg>test diagram</svg>"
        cache.put("hash1", data, "svg")

        result = cache.get("hash1")
        assert result == data

    def test_put_and_get_png(self, cache: KrokiCache):
        """Test storing and retrieving a PNG image."""
        data = b"\x89PNG\r\n\x1a\n..."
        cache.put("hash2", data, "png")

        result = cache.get("hash2")
        assert result == data

    def test_get_nonexistent_returns_none(self, cache: KrokiCache):
        """Test that getting a nonexistent entry returns None."""
        assert cache.get("nonexistent") is None

    def test_put_creates_file(self, cache: KrokiCache, cache_dir: Path):
        """Test that put creates the file on disk."""
        cache.put("abc123", b"data", "svg")
        assert (cache_dir / "abc123.svg").exists()

    def test_put_saves_metadata(self, cache: KrokiCache, cache_dir: Path):
        """Test that put saves metadata to disk."""
        cache.put("abc123", b"data", "svg")

        meta_path = cache_dir / METADATA_FILE
        assert meta_path.exists()

        meta = json.loads(meta_path.read_text())
        assert "abc123" in meta
        assert meta["abc123"]["suffix"] == "svg"
        assert meta["abc123"]["size"] == 4

    def test_get_updates_last_access(self, cache: KrokiCache, cache_dir: Path):
        """Test that get updates the last_access time."""
        cache.put("hash1", b"data", "svg")

        meta = json.loads((cache_dir / METADATA_FILE).read_text())
        initial_access = meta["hash1"]["last_access"]

        # Access again
        import time

        time.sleep(0.01)
        cache.get("hash1")

        meta = json.loads((cache_dir / METADATA_FILE).read_text())
        assert meta["hash1"]["last_access"] >= initial_access

    def test_get_suffix(self, cache: KrokiCache):
        """Test get_suffix returns the correct suffix."""
        cache.put("hash1", b"data", "svg")
        assert cache.get_suffix("hash1") == "svg"

        cache.put("hash2", b"data", "png")
        assert cache.get_suffix("hash2") == "png"

    def test_get_suffix_nonexistent_returns_none(self, cache: KrokiCache):
        """Test get_suffix returns None for nonexistent entries."""
        assert cache.get_suffix("nonexistent") is None

    def test_get_with_deleted_file_returns_none(self, cache: KrokiCache, cache_dir: Path):
        """Test that get returns None if the file was deleted externally."""
        cache.put("hash1", b"data", "svg")

        # Delete the file externally
        (cache_dir / "hash1.svg").unlink()

        result = cache.get("hash1")
        assert result is None

        # Metadata should be cleaned up
        meta = json.loads((cache_dir / METADATA_FILE).read_text())
        assert "hash1" not in meta


class TestCacheEviction:
    """Tests for LRU eviction."""

    def test_evicts_oldest_when_full(self, cache_dir: Path):
        """Test that the oldest entry is evicted when cache is full."""
        cache = KrokiCache(cache_dir, max_size=3)

        cache.put("hash1", b"data1", "svg")
        cache.put("hash2", b"data2", "svg")
        cache.put("hash3", b"data3", "svg")

        # Cache is full (3/3), adding a 4th should evict hash1 (oldest)
        cache.put("hash4", b"data4", "svg")

        assert cache.get("hash1") is None
        assert cache.get("hash2") is not None
        assert cache.get("hash3") is not None
        assert cache.get("hash4") is not None

    def test_evicts_least_recently_accessed(self, cache_dir: Path):
        """Test that LRU eviction respects access time, not insertion order."""
        cache = KrokiCache(cache_dir, max_size=3)

        cache.put("hash1", b"data1", "svg")
        cache.put("hash2", b"data2", "svg")
        cache.put("hash3", b"data3", "svg")

        # Access hash1 to make it recently used
        import time

        time.sleep(0.01)
        cache.get("hash1")

        # Adding hash4 should evict hash2 (least recently accessed)
        cache.put("hash4", b"data4", "svg")

        assert cache.get("hash1") is not None  # recently accessed
        assert cache.get("hash2") is None  # evicted
        assert cache.get("hash3") is not None
        assert cache.get("hash4") is not None

    def test_evicted_file_is_removed(self, cache_dir: Path):
        """Test that evicted files are removed from disk."""
        cache = KrokiCache(cache_dir, max_size=2)

        cache.put("hash1", b"data1", "svg")
        cache.put("hash2", b"data2", "svg")

        assert (cache_dir / "hash1.svg").exists()

        # Should evict hash1
        cache.put("hash3", b"data3", "svg")

        assert not (cache_dir / "hash1.svg").exists()


class TestCacheClear:
    """Tests for cache clearing."""

    def test_clear_removes_all_entries(self, cache: KrokiCache):
        """Test that clear removes all cached entries."""
        cache.put("hash1", b"data1", "svg")
        cache.put("hash2", b"data2", "png")

        cache.clear()

        assert cache.get("hash1") is None
        assert cache.get("hash2") is None

    def test_clear_removes_files(self, cache: KrokiCache, cache_dir: Path):
        """Test that clear removes files from disk."""
        cache.put("hash1", b"data1", "svg")
        cache.put("hash2", b"data2", "png")

        cache.clear()

        assert not (cache_dir / "hash1.svg").exists()
        assert not (cache_dir / "hash2.png").exists()

    def test_clear_preserves_metadata_file(self, cache: KrokiCache, cache_dir: Path):
        """Test that clear resets but preserves the metadata file."""
        cache.put("hash1", b"data1", "svg")
        cache.clear()

        meta = json.loads((cache_dir / METADATA_FILE).read_text())
        assert meta == {}
