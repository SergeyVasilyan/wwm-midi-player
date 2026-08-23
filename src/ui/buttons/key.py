"""Key Button widget."""

from typing import override

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from ui.buttons.abstract import AbstractButton
from utils.common import Colors

SIZE = QSize(48, 32)
BACKGROUND_ALPHA = 60


class KeyButton(AbstractButton):
    """Key Button widget."""

    def __init__(self, key: str="", octave: str="", note: str="",
                       parent: QWidget|None=None) -> None:
        """Initialize key Button widget.

        Args:
            key: The key label to display (e.g. "Q").
            octave: The register this key belongs to ("low", "med", "high").
            note: The scale degree this key is bound to (e.g. "1", "#4").
            parent: Optional parent widget.
        """
        super().__init__(parent=parent, size=SIZE)
        self.__octave: str = octave
        self.__note: str = note
        self.setText(key)
        self.__error: bool = False

    @property
    def octave(self) -> str:
        """Return key octave.

        Returns:
            The register this key belongs to ("low", "med", "high").
        """
        return self.__octave

    @property
    def note(self) -> str:
        """Return key note.

        Returns:
            The scale degree this key is bound to (e.g. "1", "#4").
        """
        return self.__note

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw the pill-shaped key body with its bound-key label.

        Args:
            event: The Qt paint event.
        """
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        base: QColor = Colors.RED.value.qcolor if self.__error else self._color
        pill: QRectF = self._scaled_rect(margin=2.0)
        radius: float = pill.height() / 2
        painter.setBrush(self._background_color(BACKGROUND_ALPHA, base))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(pill, radius, radius)
        pen: QPen = QPen(self._draw_color(base))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(pill, radius, radius)
        painter.end()
        return super().paintEvent(event)

if __name__ == "__main__":
    ...
