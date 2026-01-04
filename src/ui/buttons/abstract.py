"""Abstract Button widget."""


from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QWidget
from src.utils.common import Colors


class AbstractButton(QPushButton):
    """Abstract Button widget."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Next Button widget."""
        super().__init__(parent=parent)
        self.setFixedSize(QSize(40, 30))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color: QColor = Colors.ACCENT_1.value.qcolor
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
            }
        """)

if "__main__" == __name__:
    ...
