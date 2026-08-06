"""Common functionality used by different modules."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PySide6.QtGui import QColor


def resource_path(path: str) -> Path:
    """Resolve a bundled resource path for both source and PyInstaller onedir builds.

    PyInstaller's onedir build collects data files under an ``_internal`` directory
    next to the executable, while running from source resolves paths relative to the
    working directory. Callers pass a path as it exists in the source tree (e.g.
    ``"src/input/logo.ico"``); if that path doesn't exist and an ``_internal``
    directory is present, the ``_internal``-prefixed location is returned instead.
    """
    resolved: Path = Path(path)
    if resolved.exists() or not Path("_internal").is_dir():
        return resolved
    return Path("_internal") / resolved

class Singleton(type):
    """Singleton implementation."""

    _instances: dict[Callable, Callable] = {}

    def __call__(cls, *args, **kwargs) -> Callable:
        """Override object call dunder method."""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

@dataclass
class Color:
    """Color representation class."""

    hex: str = "#000000"
    qcolor: QColor  = field(init=False)

    def __post_init__(self) -> None:
        """Post initialization calculation."""
        if not self.hex.startswith("#"):
            self.hex = "#" + self.hex
        self.qcolor = QColor(self.hex)

class Colors(Enum):
    """Global colors enumeration."""

    ACCENT_1 = Color("#2E7D32")
    ACCENT_2 = Color("#8D6E63")
    BACKGROUND = Color("#111111")
    BACKGROUND_1 = Color("#101010")
    BACKGROUND_2 = Color("#2A2A2A")
    RED = Color("#FF0000")
    GREEN = Color("#00FF00")
    BLUE = Color("#0000FF")
    BLACK = Color("#000000")
    WHITE = Color("#FFFFFF")

# Falling-note colors for the piano visualizer, one per MIDI channel (0-15).
# Index 9 (the GM percussion channel) gets a distinct silver/grey so drum hits
# read as visually different from pitched instruments.
CHANNEL_COLORS: tuple[str, ...] = (
    "#4FC3F7", "#81C784", "#FFB74D", "#E57373",
    "#BA68C8", "#4DB6AC", "#FFD54F", "#7986CB",
    "#F06292", "#B0BEC5",
    "#AED581", "#FF8A65", "#9575CD", "#4DD0E1",
    "#DCE775", "#F48FB1",
)


def channel_color_hex(channel: int) -> str:
    """Return the hex color for a MIDI channel, wrapping defensively via modulo 16."""
    return CHANNEL_COLORS[channel % 16]

# Index 9 is reserved exclusively for drum-channel notes (see note_color_hex)
# so percussion always reads as visually distinct; pitched tracks cycle
# through the other 15.
_PITCHED_COLOR_INDICES: tuple[int, ...] = tuple(i for i in range(16) if i != 9)


def note_color_hex(track: int, is_drum: bool) -> str:
    """Return the hex color for a note, keyed by its originating track.

    Colors by track rather than MIDI channel: many real-world files route
    every instrument through the same channel (commonly channel 0) and
    differentiate instruments by track instead, so coloring by channel alone
    would collapse them all into a single color. Drum-channel notes still get
    the same reserved color regardless of track, so percussion always stands
    out.
    """
    if is_drum:
        return CHANNEL_COLORS[9]
    return CHANNEL_COLORS[_PITCHED_COLOR_INDICES[track % len(_PITCHED_COLOR_INDICES)]]

# Shared corner-radius scale, applied consistently across panels/dialogs.
RADIUS_SM: int = 6
RADIUS_MD: int = 10

# Shared spacing scale, applied consistently for margins/spacing in layouts.
SPACING_XS: int = 4
SPACING_SM: int = 8
SPACING_MD: int = 12
SPACING_LG: int = 16

TITLEBAR_HEIGHT: int = 32
RESIZE_MARGIN: int = 6
