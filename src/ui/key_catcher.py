"""Key Catcher dialog."""

import re
from typing import override

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QWidget


class KeyCatcher(QDialog):
    """Key Catcher dialog."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Key Catcher."""
        super().__init__(parent)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setWindowTitle("Key Catcher")
        self.setGeometry(300, 300, 250, 150)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.__pressed_key: str = ""
        self.__label: QLabel = QLabel("Waiting....")
        self.__construct_layout()

    @property
    def key(self) -> str:
        """Return pressed key."""
        return self.__pressed_key

    @Slot()
    def __save_on_click(self) -> None:
        """Save button click callback."""
        self.__pressed_key = self.__label.text()
        self.close()

    def __construct_hint_section(self, layout: QGridLayout, row: int) -> int:
        """Construct hint section."""
        layout.addWidget(QLabel("Allowed keys a-z, A-Z, and 0-9"), row, 0, 1, -1,
                        alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(self.__label, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        return row + 1

    def __construct_buttons_section(self, layout: QGridLayout, row: int) -> int:
        """Construct buttons section."""
        save: QPushButton = QPushButton("Save")
        save.clicked.connect(self.__save_on_click)
        widget: QWidget = QWidget()
        buttons_layout: QHBoxLayout = QHBoxLayout(widget)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save)
        buttons_layout.addStretch()
        layout.addWidget(widget, row, 0, 1, -1)
        return row + 1

    def __construct_layout(self) -> None:
        """Construct layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        row = self.__construct_hint_section(layout, row)
        row = self.__construct_buttons_section(layout, row)
        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Override key press event."""
        if re.match(r"^[a-zA-Z0-9]$", event.text()):
            self.__label.setText(event.text().upper())
            event.accept()
        super().keyPressEvent(event)


if "__main__" == __name__:
    ...
