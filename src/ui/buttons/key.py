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
        """Initialize key Button widget."""
        super().__init__(parent=parent, size=SIZE)
        self.__octave: str = octave
        self.__note: str = note
        self.setText(key)
        self.__error: bool = False

    @property
    def octave(self) -> str:
        """Return key octave."""
        return self.__octave

    @property
    def note(self) -> str:
        """Return key note."""
        return self.__note

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Override paint event."""
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
