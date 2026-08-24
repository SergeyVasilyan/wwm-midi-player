"""Settings dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.dialog_style import apply_dialog_theme
from ui.key_configurator import KeyConfigurator
from ui.toggle_switch import ToggleSwitch
from utils.common import apply_theme, current_theme, theme_bus


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
        theme_bus.changed.connect(lambda: apply_dialog_theme(self))
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

    def __construct_theme_section(self, layout: QGridLayout, row: int) -> int:
        """Add the "Theme" row with a Dark/Light toggle.

        Args:
            layout: The grid layout to add the row to.
            row: The next free row index in layout.

        Returns:
            The next free row index after the added row.
        """
        toggle: ToggleSwitch = ToggleSwitch()
        toggle.setChecked(current_theme() == "light")
        toggle.toggled.connect(lambda checked: apply_theme("light" if checked else "dark"))
        row_widget: QWidget = QWidget()
        row_layout: QHBoxLayout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(QLabel("Dark"))
        row_layout.addWidget(toggle)
        row_layout.addWidget(QLabel("Light"))
        layout.addWidget(QLabel("Theme"), row, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(row_widget, row, 1, 1, 1)
        return row + 1

    def __create_layout(self) -> None:
        """Create the dialog's full layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        row = self.__construct_key_binding_section(layout, row)
        row = self.__construct_theme_section(layout, row)
        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

if __name__ == "__main__":
    ...
