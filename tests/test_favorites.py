"""Tests for favorites module: load, save, toggle, persistence."""
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from web.core import favorites


@pytest.fixture(autouse=True)
def _tmp_favorites(tmp_path):
    """Redirect FAVORITES_FILE to a temp directory for each test."""
    original_file = favorites.FAVORITES_FILE
    original_dir = favorites.DATA_DIR
    favorites.DATA_DIR = tmp_path
    favorites.FAVORITES_FILE = tmp_path / "favorites.json"
    yield
    favorites.DATA_DIR = original_dir
    favorites.FAVORITES_FILE = original_file


class TestFavorites:
    """Test favorites persistence and toggle logic."""

    def test_load_empty_favorites(self):
        """Returns empty list when no file exists."""
        assert favorites.load_favorites() == []

    def test_save_and_load_favorites(self):
        """Can save and load favorites."""
        favorites.save_favorites(["power_flow", "n1_security"])
        loaded = favorites.load_favorites()
        assert loaded == ["power_flow", "n1_security"]

    def test_toggle_favorite_add(self):
        """toggle_favorite adds a new skill."""
        assert favorites.toggle_favorite("power_flow") is True
        assert favorites.is_favorite("power_flow") is True
        assert favorites.load_favorites() == ["power_flow"]

    def test_toggle_favorite_remove(self):
        """toggle_favorite removes an existing skill."""
        favorites.save_favorites(["power_flow"])
        assert favorites.toggle_favorite("power_flow") is False
        assert favorites.is_favorite("power_flow") is False
        assert favorites.load_favorites() == []

    def test_is_favorite_empty(self):
        """is_favorite returns False for empty favorites."""
        assert favorites.is_favorite("power_flow") is False

    def test_atomic_write(self):
        """Save uses atomic write (tmp + rename), no partial files left."""
        favorites.save_favorites(["power_flow"])
        assert not favorites.FAVORITES_FILE.with_suffix(".tmp").exists()
        assert favorites.FAVORITES_FILE.exists()
        assert favorites.load_favorites() == ["power_flow"]

    def test_max_favorites_enforced(self):
        """Cannot exceed MAX_FAVORITES; oldest is dropped."""
        max_fav = favorites.MAX_FAVORITES
        for i in range(max_fav + 2):
            favorites.toggle_favorite(f"skill_{i}")
        favs = favorites.load_favorites()
        assert len(favs) == max_fav
        assert "skill_0" not in favs  # oldest dropped
        assert "skill_1" not in favs  # second oldest also dropped

    def test_corrupted_file_handled(self):
        """Returns empty list when favorites file is corrupted JSON."""
        favorites.FAVORITES_FILE.write_text("not valid json{{{")
        assert favorites.load_favorites() == []

    def test_mixed_toggle_sequence(self):
        """Multiple add/remove toggles work correctly."""
        favorites.toggle_favorite("power_flow")
        favorites.toggle_favorite("n1_security")
        favorites.toggle_favorite("emt_simulation")

        favs = favorites.load_favorites()
        assert len(favs) == 3
        assert "power_flow" in favs
        assert "n1_security" in favs
        assert "emt_simulation" in favs

        # Remove one, add another
        favorites.toggle_favorite("n1_security")
        favorites.toggle_favorite("vsi_weak_bus")

        favs = favorites.load_favorites()
        assert "n1_security" not in favs
        assert "vsi_weak_bus" in favs
        assert len(favs) == 3
