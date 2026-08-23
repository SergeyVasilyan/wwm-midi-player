"""Settings dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.dialog_style import apply_dialog_theme
from ui.key_configurator import KeyConfigurator


class SettingsDialog(QDialog):
    """Simple Settings selection Dialog."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize the Settings dialog.

        Args:
            parent: Optional parent widget; also supplies the window icon.
        """
        super().__init__(parent)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setWindowTitle("Settings")
        self.setModal(True)
        apply_dialog_theme(self)
        self.__create_layout()

    def __open_key_configurator_on_click(self) -> None:
        """Open the KeyConfigurator dialog modally."""
        dialog: KeyConfigurator = KeyConfigurator(self)
        dialog.exec()

    def __construct_key_binding_section(self, layout: QGridLayout, row: int) -> int:
        """Add the "Configure keybindings" row.

        Args:
            layout: The grid layout to add the row to.
            row: The next free row index in layout.

        Returns:
            The next free row index after the added row.
        """
        button: QPushButton = QPushButton()
        button.setText("Open")
        button.clicked.connect(self.__open_key_configurator_on_click)
        layout.addWidget(QLabel("Configure keybindings"), row, 0, 1, 1,
                         alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(button, row, 1, 1, 1)
        return row + 1

    def __create_layout(self) -> None:
        """Create the dialog's full layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        row = self.__construct_key_binding_section(layout, row)
        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

if __name__ == "__main__":
    ...
