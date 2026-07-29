"""Abstract Button widget."""

from typing import override

from PySide6.QtCore import QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QEnterEvent, QMouseEvent
from PySide6.QtWidgets import QPushButton, QWidget

from ui.animation import AnimatedProgress
from utils.common import Colors

DEFAULT_SIZE = QSize(36, 36)
HOVER_ANIMATION_DURATION_MS = 150
PRESS_ANIMATION_DURATION_MS = 100
HOVER_GROW = 0.08
PRESS_SHRINK = 0.10


class AbstractButton(QPushButton):
    """Abstract Button widget.

    Provides the shared visual language for every button in the app: a
    filled, tinted shape (circle or pill, chosen by the subclass) that grows
    slightly on hover and shrinks slightly on press, both animated. Also
    exposes copy-safe color helpers so subclasses never mutate the shared
    Colors enum QColor instances while painting.
    """

    def __init__(self, parent: QWidget|None=None, size: QSize=DEFAULT_SIZE) -> None:
        """Initialize Abstract Button widget."""
        super().__init__(parent=parent)
        self.setFixedSize(size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color: QColor = Colors.ACCENT_1.value.qcolor
        self.__hover: AnimatedProgress = AnimatedProgress(
            self, self.__on_progress_changed, HOVER_ANIMATION_DURATION_MS)
        self.__press: AnimatedProgress = AnimatedProgress(
            self, self.__on_progress_changed, PRESS_ANIMATION_DURATION_MS)
        self.set_style()

    def _hover_progress(self) -> float:
        """Return the current hover animation progress (0..1)."""
        return self.__hover.value

    def _scale_factor(self) -> float:
        """Combined hover-grow / press-shrink scale, centered at 1.0."""
        return 1.0 + HOVER_GROW * self.__hover.value - PRESS_SHRINK * self.__press.value

    def _scaled_rect(self, margin: float=3.0) -> QRectF:
        """Return the button's drawable area, inset by margin and scaled for hover/press."""
        base: QRectF = self.rect().adjusted(margin, margin, -margin, -margin).toRectF()
        scale: float = self._scale_factor()
        width: float = base.width() * scale
        height: float = base.height() * scale
        center = base.center()
        return QRectF(center.x() - width / 2, center.y() - height / 2, width, height)

    def _background_color(self, alpha: int, base: QColor|None=None) -> QColor:
        """Return the shape's fill color at the given base alpha, brightened on hover."""
        color: QColor = QColor(base if base is not None else self._color)
        if self.__hover.value > 0:
            color = color.lighter(100 + int(25 * self.__hover.value))
        color.setAlpha(alpha)
        return color

    def _draw_color(self, base: QColor|None=None) -> QColor:
        """Return a fresh glyph color, brightened on hover.

        Always returns a new QColor instance so callers can safely mutate
        alpha/etc. without corrupting shared Colors enum values.
        """
        color: QColor = QColor(base if base is not None else self._color)
        if self.__hover.value > 0:
            return color.lighter(100 + int(20 * self.__hover.value))
        return color

    def __on_progress_changed(self, _value: float) -> None:
        """Repaint as a hover/press animation progresses."""
        self.update()

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        """Animate hover-in."""
        self.__hover.animate_to(1.0)
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        """Animate hover-out."""
        self.__hover.animate_to(0.0)
        super().leaveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Animate press-in."""
        self.__press.animate_to(1.0)
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Animate press-out."""
        self.__press.animate_to(0.0)
        super().mouseReleaseEvent(event)

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
            }
        """)

if __name__ == "__main__":
    ...
