"""Key Button widget."""

from typing import override

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget
from src.ui.buttons.abstract import AbstractButton
from src.utils.common import Colors


class KeyButton(AbstractButton):
    """Key Button widget."""

    def __init__(self, key: str="", octave: str="", note: str="",
                       parent: QWidget|None=None) -> None:
        """Initialize key Button widget."""
        super().__init__(parent=parent)
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
        radius: float = self.height() // 2
        rect: QRect = self.rect().adjusted(2, 2, -2, -2)
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color: QColor = self._color
        if self.__error:
            color = Colors.RED.value.qcolor
        color.setAlpha(100)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, radius, radius)
        color.setAlpha(255)
        pen: QPen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
        painter.end()
        return super().paintEvent(event)

if "__main__" == __name__:
    ...
