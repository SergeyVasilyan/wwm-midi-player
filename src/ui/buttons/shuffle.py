"""Shuffle Button widget."""

from typing import override

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.buttons.checkable import CheckableIconButton


class ShuffleButton(CheckableIconButton):
    """Shuffle toggle Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Shuffle Button widget."""
        super().__init__(parent=parent)
        self.setToolTip("Shuffle")

    def __draw_crossed_arrow(self, painter: QPainter, rect: QRectF, top: bool) -> None:
        """Draw one of the two crossed arrows."""
        y: float = rect.top() if top else rect.bottom()
        other_y: float = rect.bottom() if top else rect.top()
        start: QPointF = QPointF(rect.left(), y)
        end: QPointF = QPointF(rect.right(), other_y)
        painter.drawLine(QLineF(start, end))
        arrow: float = rect.width() * 0.12
        direction: float = 1.0 if other_y > y else -1.0
        painter.drawPolygon(QPolygonF([
            QPointF(end.x() - arrow, end.y() - arrow * direction),
            QPointF(end.x(), end.y()),
            QPointF(end.x() - arrow, end.y() + arrow * direction),
        ]))

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        circle: QRectF = self._scaled_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._background_color(self._active_background_alpha()))
        painter.drawEllipse(circle)
        color: QColor = self._draw_color()
        color.setAlpha(self._active_alpha())
        pen: QPen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(color)
        rect: QRectF = circle.adjusted(circle.width() * 0.26, circle.height() * 0.26,
                                       -circle.width() * 0.26, -circle.height() * 0.26)
        self.__draw_crossed_arrow(painter, rect, top=True)
        self.__draw_crossed_arrow(painter, rect, top=False)
        painter.end()
        return super().paintEvent(event)

if __name__ == "__main__":
    ...
