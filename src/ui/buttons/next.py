"""Next Button widget."""

from typing import override

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPaintEvent, QPolygon
from PySide6.QtWidgets import QWidget
from src.ui.buttons.abstract import AbstractButton


class NextButton(AbstractButton):
    """Next Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Next Button widget."""
        super().__init__(parent=parent)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        rect: QRect = self.rect().adjusted(10, 8, -10, -8)
        points: list[QPoint] = [QPoint(rect.left(), rect.top()),
                                QPoint(rect.right() - 6, rect.center().y()),
                                QPoint(rect.left(), rect.bottom())]
        painter.drawPolygon(QPolygon(points))
        painter.drawRect(QRect(rect.right() - 4, rect.top(), 3, rect.height()))
        painter.end()
        return super().paintEvent(event)

if "__main__" == __name__:
    ...
