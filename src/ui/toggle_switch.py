"""Simple Toggle switch."""

from typing import override

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QCheckBox, QWidget


class ToggleSwitch(QCheckBox):
    """Modern Toggle Switch in WWM style."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize toggle."""
        super().__init__(parent=parent)
        self.setChecked(False)
        self.__checked_color: QColor = QColor("#2E7D32")
        self.__unchecked_color: QColor = QColor("#8D6E63")
        self.__knob_color: QColor = QColor("#FFFFFF")
        self.__knob_size: int = 18
        self.__knob_offset: int = 2
        self.setChecked(False)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
            }
        """)

    @override
    def sizeHint(self) -> QSize:
        """Override size hint."""
        return QSize(40, 25)

    @override
    def paintEvent(self, _event: QPaintEvent) -> None:
        """Override paint event."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_rect: QRect = QRect(0, 0, self.width(), self.height())
        painter.setBrush(self.__checked_color if self.isChecked() else self.__unchecked_color)
        painter.setPen(Qt.PenStyle.NoPen)
        radius: int = self.height() // 2
        painter.drawRoundedRect(track_rect, radius, radius)
        knob_x: int = self.__knob_offset
        if self.isChecked():
            knob_x = self.width() - self.__knob_size - self.__knob_offset
        knob_rect: QRect = QRect(knob_x, ((self.height() // 2) - (self.__knob_size // 2)),
                                 self.__knob_size, self.__knob_size)
        painter.setBrush(self.__knob_color)
        painter.drawEllipse(knob_rect)
        painter.end()

if "__main__" == __name__:
    ...
