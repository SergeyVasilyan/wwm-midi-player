"""Play/Pause Button widget."""

from typing import override

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation, Signal, Slot
from PySide6.QtGui import QBrush, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from ui.buttons.abstract import AbstractButton


class PlayButton(AbstractButton):
    """Play/Pause Button widget."""

    change: Signal = Signal(bool)

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Play/Pause Button widget."""
        super().__init__(parent=parent)
        self.__is_playing: bool = False
        self.__animation: QVariantAnimation = QVariantAnimation(self)
        self.__animation.setDuration(400)
        self.__animation.setStartValue(0.0)
        self.__animation.setEndValue(1.0)
        self.__animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.__animation.valueChanged.connect(self.update)
        self.__morph: float = 0.0
        self.change.connect(self.__toggle_state)

    @Slot(bool)
    def __toggle_state(self, new_state: bool) -> None:
        """Start animation."""
        if self.__is_playing == new_state:
            return
        self.__is_playing = new_state
        if self.__is_playing:
            self.__animation.setDirection(QVariantAnimation.Direction.Forward)
        else:
            self.__animation.setDirection(QVariantAnimation.Direction.Backward)
        self.__animation.start()

    @override
    def paintEvent(self, _event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect: QRectF = self.rect().adjusted(5, 5, -5, -5).toRectF()
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        self.__morph = 1.0 if self.__is_playing else 0.0
        if self.__animation.state() == self.__animation.State.Running:
            self.__morph = self.__animation.currentValue()
        if self.__morph < 0.5:
            p1: QPointF = rect.bottomLeft()
            p2: QPointF = rect.topLeft()
            p3: QPointF = QPointF(rect.right(), rect.center().y())
            p3.setX(p3.x() - (p3.x() - rect.center().x()) * (self.__morph * 2))
            painter.drawPolygon([p1, p2, p3])
        else:
            bar_width: float = rect.width() / 3
            gap: float = bar_width / 2
            left_bar: QRectF = QRectF(rect.left(), rect.top(), bar_width, rect.height())
            right_bar: QRectF = QRectF(rect.left() + bar_width + gap, rect.top(), bar_width,
                                      rect.height())
            factor: float = (self.__morph - 0.5) * 2
            left_bar.setWidth(left_bar.width() * factor)
            right_bar.setWidth(right_bar.width() * factor)
            painter.drawRect(left_bar)
            painter.drawRect(right_bar)

if __name__ == "__main__":
    ...
