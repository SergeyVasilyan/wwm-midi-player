"""Key Catcher dialog."""

import re
from typing import override

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QWidget


class KeyCatcher(QDialog):
    """Key Catcher dialog."""

    def __init__(self, forbidden_keys: list[str], parent: QWidget|None=None) -> None:
        """Initialize Key Catcher."""
        super().__init__(parent)
        self.setWindowTitle("Key Catcher")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.__pressed_key: str = ""
        self.__label: QLabel
        self.__error_label: QLabel
        self.__forbidden_keys: list[str] = forbidden_keys
        self.__save_button: QPushButton
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
        layout.addWidget(QLabel("Allowed keys A-Z, and 0-9"), row, 0, 1, -1,
                        alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        self.__label = QLabel("Waiting....")
        self.__label.setStyleSheet("font-size: 14pt; padding: 0px 8xp; font-weight: bold;"
                                   "color: yellow;")
        layout.addWidget(self.__label, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        self.__error_label = QLabel("Key is already assigned to another note")
        self.__error_label.setStyleSheet("color: red;")
        self.__error_label.hide()
        layout.addWidget(self.__error_label, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        return row + 1

    def __construct_buttons_section(self, layout: QGridLayout, row: int) -> int:
        """Construct buttons section."""
        self.__save_button = QPushButton("Save")
        self.__save_button.setDisabled(True)
        self.__save_button.clicked.connect(self.__save_on_click)
        widget: QWidget = QWidget()
        buttons_layout: QHBoxLayout = QHBoxLayout(widget)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.__save_button)
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

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Override key press event."""
        pressed_key: str = event.text().upper()
        if re.match(r"^[A-Z0-9]$", pressed_key):
            self.__label.setText(pressed_key)
            if pressed_key in self.__forbidden_keys:
                self.__save_button.setDisabled(True)
                self.__error_label.show()
            else:
                self.__save_button.setEnabled(True)
                self.__error_label.hide()
                event.accept()
        super().keyPressEvent(event)


if "__main__" == __name__:
    ...
