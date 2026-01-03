"""Play/Pause Button widget."""

from typing import override

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPolygon
from PySide6.QtWidgets import QPushButton, QWidget


class PlayButton(QPushButton):
    """Play/Pause Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Play/Pause Button widget."""
        super().__init__(parent=parent)
        self.setCheckable(True)
        self.setChecked(False)
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
