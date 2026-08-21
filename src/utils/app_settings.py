"""Persisted app settings: volume, last Audio/WWM mode, last playlist and selection.

Mirrors utils.wwm_macro.KeyManager's keybindings.json persistence pattern:
a JSON file resolved via utils.common.resource_path, loaded on startup with
a safe fallback to defaults, saved on close.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from utils.common import resource_path

DEFAULT_VOLUME: int = 100
SETTINGS_PATH: Path = resource_path("src/input/settings.json")


@dataclass
class AppSettings:
    """Everything persisted between launches."""

    volume: int = DEFAULT_VOLUME
    is_audio_mode: bool = False
    playlist: list[str] = field(default_factory=list)
    current_index: int = -1


def load_settings(path: Path = SETTINGS_PATH) -> AppSettings:
    """Load settings from disk, falling back to defaults if missing or invalid."""
    if not path.exists():
        return AppSettings()
    try:
        with path.open(encoding="utf-8") as f:
            data: dict = json.load(f)
        known_fields: set[str] = {"volume", "is_audio_mode", "playlist", "current_index"}
        return AppSettings(**{key: value for key, value in data.items() if key in known_fields})
    except (OSError, json.JSONDecodeError, TypeError):
        return AppSettings()


def save_settings(settings: AppSettings, path: Path = SETTINGS_PATH) -> None:
    """Save settings to disk, overwriting any existing file."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=4)
