"""Key Configurator dialog."""

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from src.ui.key_catcher import KeyCatcher
from src.utils.wwm_macro import KeyManager


class KeyConfigurator(QDialog):
    """Key Configurator Dialog."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Key Configurator."""
        super().__init__(parent)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setWindowTitle("Key Configurator")
        self.setModal(True)
        self.__manager: KeyManager = KeyManager()
        self.__create_layout()

    def __key_button_on_click(self, octave: str, note: str) -> None:
        """Key button click callback."""
        dialog: KeyCatcher = KeyCatcher(self)
        dialog.exec()
        pressed_key: str = dialog.key
        if not pressed_key:
            return
        self.__manager.update_keybinding(octave, note, pressed_key)

    def __construct_key_button(self, layout: QHBoxLayout, octave: str, note: str, key: str) -> None:
        """Construct key button."""
        button: QPushButton = QPushButton(key)
        button.clicked.connect(lambda: self.__key_button_on_click(octave, note))
        layout.addWidget(button)

    def __construct_key_binding_section(self, layout: QGridLayout, row: int) -> int:
        """Construct key binding configuration section."""
        for octave, notes in self.__manager.bindings.items():
            group: QGroupBox = QGroupBox(f"{octave.title()} Octave")
            group_layout: QHBoxLayout = QHBoxLayout(group)
            for note, key in notes.items():
                if re.search(r"#|b", note):
                    continue
                self.__construct_key_button(group_layout, octave, note, key)
            layout.addWidget(group, row, 0, 1, -1)
            row += 1
        return row + 1

    def __create_layout(self) -> None:
        """Create Dialog layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        layout.addWidget(QLabel("Customize which keys play each note. Click a key to change it."),
                         row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        row = self.__construct_key_binding_section(layout, row)
        button: QPushButton = QPushButton("Reset")
        button.clicked.connect(self.__manager.reset_keybindings)
        layout.addWidget(button, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

if "__main__" == __name__:
    ...
