"""Play/Pause Button widget."""

from typing import override

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPaintEvent, QPolygon
from PySide6.QtWidgets import QWidget
from src.ui.buttons.abstract import AbstractButton


class PlayButton(AbstractButton):
    """Play/Pause Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Play/Pause Button widget."""
        super().__init__(parent=parent)
        self.setCheckable(True)
        self.setChecked(False)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        rect: QRect = self.rect().adjusted(10, 8, -10, -8)
        if self.isChecked():
            bar_width: int = rect.width() // 3
            painter.drawRect(QRect(rect.left(), rect.top(), bar_width, rect.height()))
            painter.drawRect(QRect(rect.right() - bar_width, rect.top(), bar_width, rect.height()))
        else:
            points: list[QPoint] = [QPoint(rect.left(), rect.top()),
                                    QPoint(rect.right(), rect.center().y()),
                                    QPoint(rect.left(), rect.bottom())]
            painter.drawPolygon(QPolygon(points))
        painter.end()
        return super().paintEvent(event)

if "__main__" == __name__:
    ...
