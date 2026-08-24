"""Pill-shaped search box with hand-drawn magnifying-glass and clear icons."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLineEdit, QWidget

from utils.common import SPACING_MD, Colors, theme_bus

ICON_SIZE = 14
HANDLE_ANGLE_DEG = -45.0
HANDLE_LENGTH_RATIO = 0.32
CLEAR_GLYPH_MARGIN_RATIO = 0.2


def _magnifier_pixmap(size: int, color: QColor) -> QPixmap:
    """Render a magnifying-glass glyph to a transparent QPixmap once, at construction time.

    The handle line starts from a point on the lens circle's own boundary
    (derived from its center/radius at a fixed angle) rather than an
    independent hardcoded offset, so it always visually touches the lens.

    Args:
        size: The pixmap's width and height in pixels.
        color: The glyph's stroke color.

    Returns:
        A transparent square pixmap containing the rendered glyph.
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


def _clear_pixmap(size: int, color: QColor) -> QPixmap:
    """Render an "x" glyph to a transparent QPixmap, mirroring CloseButton's crossed-line glyph.

    Args:
        size: The pixmap's width and height in pixels.
        color: The glyph's stroke color.

    Returns:
        A transparent square pixmap containing the rendered glyph.
    """
    pixmap: QPixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter: QPainter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen: QPen = QPen(color)
    pen.setWidthF(size * 0.11)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    margin: float = size * CLEAR_GLYPH_MARGIN_RATIO
    painter.drawLine(QPointF(margin, margin), QPointF(size - margin, size - margin))
    painter.drawLine(QPointF(size - margin, margin), QPointF(margin, size - margin))
    painter.end()
    return pixmap


class SearchBox(QLineEdit):
    """Song-search input: pill shape, leading magnifying-glass icon, trailing clear icon."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize the search box, placeholder text, and leading/trailing icons.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent=parent)
        self.setPlaceholderText("Search songs...")
        self.__magnifier_action: QAction = self.addAction(
            QIcon(_magnifier_pixmap(ICON_SIZE, QColor(Colors.WHITE.value.hex))),
            QLineEdit.ActionPosition.LeadingPosition)
        self.__clear_action: QAction = self.addAction(
            QIcon(_clear_pixmap(ICON_SIZE, QColor(Colors.TEXT_MUTED.value.hex))),
            QLineEdit.ActionPosition.TrailingPosition)
        self.__clear_action.setVisible(False)
        self.__clear_action.triggered.connect(self.clear)
        self.textChanged.connect(lambda text: self.__clear_action.setVisible(bool(text)))
        self.set_style()
        theme_bus.changed.connect(self.set_style)
        theme_bus.changed.connect(self.__refresh_icons)

    def __refresh_icons(self) -> None:
        """Regenerate the leading/trailing icon pixmaps after a theme switch."""
        self.__magnifier_action.setIcon(
            QIcon(_magnifier_pixmap(ICON_SIZE, QColor(Colors.WHITE.value.hex))))
        self.__clear_action.setIcon(
            QIcon(_clear_pixmap(ICON_SIZE, QColor(Colors.TEXT_MUTED.value.hex))))

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
