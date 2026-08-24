"""Key Catcher dialog."""

import re
from typing import override

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QWidget

from ui.dialog_style import apply_dialog_theme
from utils.common import theme_bus


class KeyCatcher(QDialog):
    """Key Catcher dialog."""

    def __init__(self, forbidden_keys: list[str], parent: QWidget|None=None) -> None:
        """Initialize Key Catcher.

        Args:
            forbidden_keys: Keys already bound to another note; pressing one
                of these disables Save and shows a conflict warning instead
                of accepting it.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Key Catcher")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        apply_dialog_theme(self)
        theme_bus.changed.connect(lambda: apply_dialog_theme(self))
        self.__pressed_key: str = ""
        self.__label: QLabel
        self.__error_label: QLabel
        self.__forbidden_keys: list[str] = forbidden_keys
        self.__save_button: QPushButton
        self.__construct_layout()

    @property
    def key(self) -> str:
        """Return pressed key.

        Returns:
            The saved key, or an empty string if the dialog was closed
            without pressing Save.
        """
        return self.__pressed_key

    @Slot()
    def __save_on_click(self) -> None:
        """Commit the currently displayed key and close the dialog."""
        self.__pressed_key = self.__label.text()
        self.close()

    def __construct_hint_section(self, layout: QGridLayout, row: int) -> int:
        """Add the allowed-keys hint, pressed-key display, and conflict warning.

        Args:
            layout: The grid layout to add rows to.
            row: The next free row index in layout.

        Returns:
            The next free row index after the added rows.
        """
        layout.addWidget(QLabel("Allowed keys A-Z, and 0-9"), row, 0, 1, -1,
                        alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        self.__label = QLabel("Waiting....")
        self.__label.setStyleSheet("font-size: 14pt; padding: 0px 8xp; font-weight: bold;"
                                   "color: yellow; background: transparent;")
        layout.addWidget(self.__label, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        self.__error_label = QLabel("Key is already assigned to another note")
        self.__error_label.setStyleSheet("color: red; background: transparent;")
        self.__error_label.hide()
        layout.addWidget(self.__error_label, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        return row + 1

    def __construct_buttons_section(self, layout: QGridLayout, row: int) -> int:
        """Add the centered Save button row.

        Args:
            layout: The grid layout to add the row to.
            row: The next free row index in layout.

        Returns:
            The next free row index after the added row.
        """
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
        """Construct the dialog's full layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        row = self.__construct_hint_section(layout, row)
        row = self.__construct_buttons_section(layout, row)
        self.setLayout(layout)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Display the pressed key and validate it against forbidden keys.

        Args:
            event: The Qt key press event.
        """
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


if __name__ == "__main__":
    ...
