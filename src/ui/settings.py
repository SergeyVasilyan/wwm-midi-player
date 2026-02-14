"""Settings dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class SettingsDialog(QDialog):
    """Simple Settings selection Dialog."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """INIT."""
        super().__init__(parent)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.__create_layout()

    def __construct_key_binding_section(self, layout: QGridLayout, row: int) -> int:
        """Construct key binding configuration section."""
        button: QPushButton = QPushButton()
        button.setText("Open")
        layout.addWidget(QLabel("Configure keybindings"), row, 0, 1, 1,
                         alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(button, row, 1, 1, 1)
        return row + 1

    def __create_layout(self) -> None:
        """Create Dialog layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        row = self.__construct_key_binding_section(layout, row)
        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

if "__main__" == __name__:
    ...
