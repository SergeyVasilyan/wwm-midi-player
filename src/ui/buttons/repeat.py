"""Repeat Button widget."""

from typing import override

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.buttons.checkable import CheckableIconButton

START_ANGLE = 90.0
SWEEP_ANGLE = -300.0


class RepeatButton(CheckableIconButton):
    """Repeat toggle Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Repeat Button widget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent=parent)
        self.setToolTip("Repeat")

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw the button's circular background and repeat-loop glyph.

        Args:
            event: The Qt paint event.
        """
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
        rect: QRectF = circle.adjusted(circle.width() * 0.24, circle.height() * 0.24,
                                       -circle.width() * 0.24, -circle.height() * 0.24)
        path: QPainterPath = QPainterPath()
        path.arcMoveTo(rect, START_ANGLE)
        path.arcTo(rect, START_ANGLE, SWEEP_ANGLE)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        end_point: QPointF = path.currentPosition()
        tangent_angle: float = path.angleAtPercent(1.0)
        arrow: float = rect.width() * 0.16
        painter.save()
        painter.translate(end_point)
        painter.rotate(-tangent_angle)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF([
            QPointF(-arrow * 0.6, -arrow),
            QPointF(arrow * 0.6, 0),
            QPointF(-arrow * 0.6, arrow),
        ]))
        painter.restore()
        painter.end()
        return super().paintEvent(event)

if __name__ == "__main__":
    ...
