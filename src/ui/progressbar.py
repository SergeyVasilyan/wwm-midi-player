"""ProgressBar widget: custom-painted track + hover-reveal thumb (no seek)."""

from typing import override

from PySide6.QtCore import QEasingCurve, QEvent, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QEnterEvent, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QProgressBar, QWidget

from ui.animation import AnimatedProgress
from utils.common import Colors

HIT_AREA_HEIGHT = 18
TRACK_HEIGHT = 6
THUMB_RADIUS = 6.0
THUMB_HOVER_DURATION_MS = 120
FILL_ANIMATION_DURATION_MS = 950


class ProgressBar(QProgressBar):
    """Custom-painted progress bar with a thumb that only appears on hover."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize ProgressBar."""
        super().__init__(parent=parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setFixedHeight(HIT_AREA_HEIGHT)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setTextVisible(False)
        self.setStyleSheet("QProgressBar { background: transparent; border: none; }")
        self.__thumb_reveal: AnimatedProgress = AnimatedProgress(
            self, self.__on_reveal_changed, THUMB_HOVER_DURATION_MS)
        self.__fill: AnimatedProgress = AnimatedProgress(
            self, self.__on_fill_changed, FILL_ANIMATION_DURATION_MS,
            easing=QEasingCurve.Type.Linear)

    def __on_reveal_changed(self, _value: float) -> None:
        """Repaint as the thumb-reveal animation progresses."""
        self.update()

    def __on_fill_changed(self, _value: float) -> None:
        """Repaint as the fill animation progresses."""
        self.update()

    @override
    def setValue(self, value: int) -> None:
        """Set the progress value, animating the visual fill smoothly forward.

        A backward jump (new track, error reset) snaps instantly instead of
        visually rewinding.
        """
        old_fraction: float = self.__fraction()
        super().setValue(value)
        new_fraction: float = self.__fraction()
        if new_fraction < old_fraction:
            self.__fill.snap_to(new_fraction)
        else:
            self.__fill.animate_to(new_fraction)

    def __track_rect(self) -> QRectF:
        """Return the visual track rect, vertically centered in the hit area."""
        return QRectF(0, (self.height() - TRACK_HEIGHT) / 2, self.width(), TRACK_HEIGHT)

    def __fraction(self) -> float:
        """Return current progress as a 0..1 fraction, guarding against a zero-range bar."""
        span: int = self.maximum() - self.minimum()
        return 0.0 if span <= 0 else (self.value() - self.minimum()) / span

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        """Reveal the thumb on hover."""
        self.__thumb_reveal.animate_to(1.0)
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        """Hide the thumb when the mouse leaves."""
        self.__thumb_reveal.animate_to(0.0)
        super().leaveEvent(event)

    @override
    def paintEvent(self, _event: QPaintEvent) -> None:
        """Paint the track, filled portion, and (if hovered) the thumb."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track: QRectF = self.__track_rect()
        radius: float = TRACK_HEIGHT / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.BACKGROUND_2.value.hex))
        painter.drawRoundedRect(track, radius, radius)
        fraction: float = self.__fill.value
        if fraction > 0:
            fill: QRectF = QRectF(track)
            fill.setWidth(track.width() * fraction)
            gradient: QLinearGradient = QLinearGradient(fill.topLeft(), fill.topRight())
            gradient.setColorAt(0.0, QColor(Colors.ACCENT_1.value.hex))
            gradient.setColorAt(1.0, QColor("#C0A060"))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(fill, radius, radius)
        if self.__thumb_reveal.value > 0:
            center_x: float = track.left() + track.width() * fraction
            center_y: float = track.center().y()
            thumb_color: QColor = QColor(Colors.WHITE.value.hex)
            thumb_color.setAlpha(int(255 * self.__thumb_reveal.value))
            painter.setBrush(thumb_color)
            painter.drawEllipse(QPointF(center_x, center_y), THUMB_RADIUS, THUMB_RADIUS)

if __name__ == "__main__":
    ...
