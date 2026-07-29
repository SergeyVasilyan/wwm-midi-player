"""Next Button widget."""

from typing import override

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPaintEvent, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.buttons.abstract import AbstractButton

SECONDARY_BACKGROUND_ALPHA = 35


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
        circle: QRectF = self._scaled_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._background_color(SECONDARY_BACKGROUND_ALPHA))
        painter.drawEllipse(circle)
        painter.setBrush(self._draw_color())
        glyph: QRectF = circle.adjusted(circle.width() * 0.30, circle.height() * 0.27,
                                        -circle.width() * 0.34, -circle.height() * 0.27)
        points: list[QPointF] = [glyph.topLeft(),
                                 QPointF(glyph.right() - glyph.width() * 0.25, glyph.center().y()),
                                 glyph.bottomLeft()]
        painter.drawPolygon(QPolygonF(points))
        bar_width: float = glyph.width() * 0.22
        painter.drawRect(QRectF(glyph.right() - bar_width, glyph.top(), bar_width, glyph.height()))
        painter.end()
        return super().paintEvent(event)

if __name__ == "__main__":
    ...
