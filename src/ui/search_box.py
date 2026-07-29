"""Pill-shaped search box with a hand-drawn magnifying-glass leading icon."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLineEdit, QWidget

from utils.common import SPACING_MD, Colors

ICON_SIZE = 14
HANDLE_ANGLE_DEG = 45.0
HANDLE_LENGTH_RATIO = 0.32


def _magnifier_pixmap(size: int, color: QColor) -> QPixmap:
    """Render a magnifying-glass glyph to a transparent QPixmap once, at construction time.

    The handle line starts from a point on the lens circle's own boundary
    (derived from its center/radius at a fixed angle) rather than an
    independent hardcoded offset, so it always visually touches the lens.
    """
    pixmap: QPixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter: QPainter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen: QPen = QPen(color)
    pen.setWidthF(size * 0.11)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    lens_rect: QRectF = QRectF(size * 0.12, size * 0.12, size * 0.55, size * 0.55)
    painter.drawEllipse(lens_rect)
    center: QPointF = lens_rect.center()
    radius: float = lens_rect.width() / 2
    angle_rad: float = math.radians(HANDLE_ANGLE_DEG)
    start: QPointF = QPointF(center.x() + radius * math.cos(angle_rad),
                             center.y() - radius * math.sin(angle_rad))
    handle_length: float = size * HANDLE_LENGTH_RATIO
    end: QPointF = QPointF(start.x() + handle_length * math.cos(angle_rad),
                           start.y() - handle_length * math.sin(angle_rad))
    painter.drawLine(start, end)
    painter.end()
    return pixmap


class SearchBox(QLineEdit):
    """Song-search input: pill shape, leading magnifying-glass icon."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize the search box, placeholder text, and leading icon."""
        super().__init__(parent=parent)
        self.setPlaceholderText("Search songs...")
        icon: QIcon = QIcon(_magnifier_pixmap(ICON_SIZE, QColor(Colors.WHITE.value.hex)))
        self.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)
        self.set_style()

    def set_style(self) -> None:
        """Apply pill-shaped QSS matching the app palette."""
        height: int = self.sizeHint().height() or 32
        radius: int = height // 2
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                border: 1px solid {Colors.BACKGROUND_2.value.hex};
                border-radius: {radius}px;
                padding: 4px {SPACING_MD}px;
                color: {Colors.WHITE.value.hex};
            }}
            QLineEdit:focus {{
                border: 1px solid {Colors.ACCENT_1.value.hex};
            }}
        """)

if __name__ == "__main__":
    ...
