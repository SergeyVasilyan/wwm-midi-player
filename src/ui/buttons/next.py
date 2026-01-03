"""Next Button widget."""

from typing import override

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPolygon
from PySide6.QtWidgets import QPushButton, QWidget


class NextButton(QPushButton):
    """Next Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Next Button widget."""
        super().__init__(parent=parent)
        self.setFixedSize(QSize(60, 40))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
            }
        """)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#2E7D32"))
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
