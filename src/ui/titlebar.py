"""Custom frameless-window title bar: icon, title, minimize, close."""

from typing import override

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QWidget

from ui.buttons.close import CloseButton
from ui.buttons.minimize import MinimizeButton
from utils.common import SPACING_XS, TITLEBAR_HEIGHT, Colors

ICON_SIZE = QSize(16, 16)


class TitleBar(QWidget):
    """Draggable title bar replacing the native window frame's caption area."""

    def __init__(self, window: QMainWindow, title: str, icon: QIcon,
                 parent: QWidget|None=None) -> None:
        """Initialize the title bar for the given top-level window."""
        super().__init__(parent=parent)
        self.__window: QMainWindow = window
        self.setFixedHeight(TITLEBAR_HEIGHT)
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND.value.hex};")
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING_XS * 2, 0, SPACING_XS, 0)
        layout.setSpacing(SPACING_XS)
        icon_label: QLabel = QLabel()
        icon_label.setPixmap(icon.pixmap(ICON_SIZE))
        title_label: QLabel = QLabel(title)
        title_label.setStyleSheet(f"color: {Colors.WHITE.value.hex}; font-weight: bold;")
        layout.addWidget(icon_label)
        layout.addWidget(title_label, stretch=1)
        layout.addWidget(MinimizeButton())
        layout.addWidget(CloseButton())
        self.__wire_buttons(layout)

    def __wire_buttons(self, layout: QHBoxLayout) -> None:
        """Connect the minimize/close buttons to the window."""
        minimize_button: MinimizeButton = layout.itemAt(2).widget()
        close_button: CloseButton = layout.itemAt(3).widget()
        minimize_button.clicked.connect(self.__window.showMinimized)
        close_button.clicked.connect(self.__window.close)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start an OS-native window move via QWindow.startSystemMove()."""
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.__window.windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)

if __name__ == "__main__":
    ...
