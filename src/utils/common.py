"""Common functionality used by different modules."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor


def resource_path(path: str) -> Path:
    """Resolve a bundled resource path for both source and PyInstaller onedir builds.

    PyInstaller's onedir build collects data files under an ``_internal`` directory
    next to the executable, while running from source resolves paths relative to the
    working directory. Callers pass a path as it exists in the source tree (e.g.
    ``"src/input/logo.ico"``); if that path doesn't exist and an ``_internal``
    directory is present, the ``_internal``-prefixed location is returned instead.

    Args:
        path: Resource path as it exists in the source tree.

    Returns:
        The resolved path, adjusted for a PyInstaller onedir build if needed.
    """
    resolved: Path = Path(path)
    if resolved.exists() or not Path("_internal").is_dir():
        return resolved
    return Path("_internal") / resolved

class Singleton(type):
    """Singleton implementation."""

    _instances: dict[Callable, Callable] = {}

    def __call__(cls, *args, **kwargs) -> Callable:
        """Return the shared instance, constructing it on first call.

        Args:
            *args: Positional arguments forwarded to the class constructor
                on first call; ignored on subsequent calls.
            **kwargs: Keyword arguments forwarded to the class constructor
                on first call; ignored on subsequent calls.

        Returns:
            The singleton instance of cls.
        """
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
    """Global colors enumeration.

    WHITE/BACKGROUND/BACKGROUND_1/BACKGROUND_2/TEXT_MUTED are theme-dependent
    (see _PALETTES/apply_theme below) - their stored value is mutated in
    place when the theme switches, so every existing `Colors.X.value.hex`/
    `.qcolor` read stays correct without call sites needing to change. The
    remaining members are intentionally invariant across themes (either
    already fine on both backgrounds, like ACCENT_1/RED, or meaning a true
    black/white that must never flip, like BLACK's use as a universal
    "darken on press" overlay tint).
    """

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
    TEXT_MUTED = Color("#999999")

# Theme-dependent members' values per theme name; members not listed here
# (ACCENT_1, ACCENT_2, RED, GREEN, BLUE, BLACK) stay constant across themes.
_PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "WHITE": "#FFFFFF",
        "BACKGROUND": "#111111",
        "BACKGROUND_1": "#101010",
        "BACKGROUND_2": "#2A2A2A",
        "TEXT_MUTED": "#999999",
    },
    "light": {
        "WHITE": "#1A1A1A",
        "BACKGROUND": "#F0F0F0",
        "BACKGROUND_1": "#FFFFFF",
        "BACKGROUND_2": "#D0D0D0",
        "TEXT_MUTED": "#666666",
    },
}

_current_theme: str = "dark"


class _ThemeBus(QObject):
    """Signal bus notifying widgets to restyle after a theme switch."""

    changed: Signal = Signal()


theme_bus: _ThemeBus = _ThemeBus()


def current_theme() -> str:
    """Return the name of the currently active theme.

    Returns:
        "dark" or "light".
    """
    return _current_theme


def apply_theme(name: str) -> None:
    """Switch the active theme, mutating theme-dependent Colors members in place.

    Every `Colors.X.value.hex`/`.qcolor` read across the codebase reflects
    the new palette immediately after this call, since it's the same
    `Color` instance being mutated rather than replaced. Emits
    `theme_bus.changed` afterward so live widgets can restyle/repaint.

    Args:
        name: The theme to switch to, "dark" or "light".
    """
    global _current_theme
    palette: dict[str, str] = _PALETTES[name]
    for member in Colors:
        if member.name in palette:
            hex_value: str = palette[member.name]
            member.value.hex = hex_value
            member.value.qcolor = QColor(hex_value)
    _current_theme = name
    theme_bus.changed.emit()


def scrollbar_qss() -> str:
    """Return QSS for a slim, theme-matched vertical scrollbar.

    A function (not a constant) since it reads theme-dependent Colors
    values that must be re-evaluated after a theme switch, not baked in
    once at import time. Appended to a scrollable widget's own stylesheet
    wherever it needs one - there's no default styling otherwise, which
    leaves the OS's native scrollbar clashing with the app's own chrome.

    Returns:
        A QSS block targeting QScrollBar:vertical and its sub-controls.
    """
    return f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 2px 2px 2px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BACKGROUND_2.value.hex};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.ACCENT_1.value.hex};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            border: none;
            background: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """

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
    """Return the hex color for a MIDI channel, wrapping defensively via modulo 16.

    Args:
        channel: MIDI channel number; wrapped via modulo 16 if out of range.

    Returns:
        The channel's hex color string, e.g. "#4FC3F7".
    """
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

    Args:
        track: Originating MIDI track index.
        is_drum: Whether the note is on the GM percussion channel.

    Returns:
        The note's hex color string.
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
