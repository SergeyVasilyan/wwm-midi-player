"""Common functionality used by different modules."""

import platform
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtGui import QColor

IS_WINDOWS: bool = platform.system() == "Windows"

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
