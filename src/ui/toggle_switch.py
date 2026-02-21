"""Simple Toggle switch."""

from typing import override

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QAbstractButton, QWidget

from utils.common import Colors


class ToggleSwitch(QAbstractButton):
    """Modern Toggle Switch."""

    __position_changed: Signal = Signal(float)

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize toggle."""
        super().__init__(parent=parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__checked_color: QColor = Colors.ACCENT_1.value.qcolor
        self.__unchecked_color: QColor = Colors.ACCENT_2.value.qcolor
        self.__knob_color: QColor = QColor("#FFFFFF")
        self.__width: int = 45
        self.__height: int = int(self.__width * .52)
        self.__offset: int = 2
        self.__knob_size: int = self.__height - (self.__offset * 2)
        self.__position: float = self.__offset
        self.setMinimumSize(self.__width, self.__height)
        self.__animation: QPropertyAnimation = QPropertyAnimation(self, b"position", self)
        self.__animation.setDuration(250)
        self.__animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.toggled.connect(self.__start_animation)

    @Property(float, notify=__position_changed)
    def position(self) -> float:
        """Return current position."""
        return self.__position

    @position.setter
    def position(self, value: float) -> None:
        """Update position."""
        value = max(self.__offset, min(self.__width - self.__knob_size - self.__offset, value))
        if value == self.__position:
            return
        self.__position = value
        self.__position_changed.emit(value)
        self.update()

    @override
    def sizeHint(self) -> QSize:
        """Override size hint."""
        return QSize(self.__width, self.__height)

    @override
    def hitButton(self, pos: QPoint, /) -> bool:
        """Override hitButton."""
        return self.rect().contains(pos)

    @override
    def paintEvent(self, _event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track_rect: QRect = QRect(0, 0, self.width(), self.height())
        painter.setBrush(self.__checked_color if self.isChecked() else self.__unchecked_color)
        painter.setPen(Qt.PenStyle.NoPen)
        radius: int = self.__width // 4
        painter.drawRoundedRect(track_rect, radius, radius)
        painter.setPen(QColor(0, 0, 0, 30))
        painter.setBrush(self.__knob_color)
        painter.drawEllipse(QRect(int(self.__position), self.__offset, self.__knob_size,
                                  self.__knob_size))
        painter.end()

    @Slot()
    def __start_animation(self, /) -> None:
        """Start animation.."""
        self.__animation.stop()
        self.__animation.setStartValue(self.__position)
        if self.isChecked():
            self.__animation.setEndValue(self.__width - self.__knob_size - self.__offset)
        else:
            self.__animation.setEndValue(self.__offset)
        self.__animation.start()

if __name__ == "__main__":
    ...
