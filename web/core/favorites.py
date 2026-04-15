"""Favorites: persistent skill bookmark management."""
import json
from pathlib import Path
from typing import List

DATA_DIR = Path(__file__).parent.parent / "data"
FAVORITES_FILE = DATA_DIR / "favorites.json"

MAX_FAVORITES = 8


def load_favorites() -> List[str]:
    """Load favorite skill names from file."""
    if FAVORITES_FILE.exists():
        try:
            return json.loads(FAVORITES_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_favorites(favorites: List[str]) -> None:
    """Save favorite skill names to file (atomic write)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = FAVORITES_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(favorites, ensure_ascii=False, indent=2))
    tmp.rename(FAVORITES_FILE)


def is_favorite(skill_name: str) -> bool:
    """Check if a skill is favorited."""
    return skill_name in load_favorites()


def toggle_favorite(skill_name: str) -> bool:
    """Toggle favorite status. Returns new state (True = added)."""
    favs = load_favorites()
    if skill_name in favs:
        favs.remove(skill_name)
        save_favorites(favs)
        return False
    else:
        # Enforce max favorites: remove oldest if at limit
        if len(favs) >= MAX_FAVORITES:
            favs.pop(0)
        favs.append(skill_name)
        save_favorites(favs)
        return True
