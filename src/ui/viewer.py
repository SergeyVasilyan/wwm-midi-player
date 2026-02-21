"""Viewer widget."""


from PySide6.QtWidgets import QFrame, QListWidget, QVBoxLayout, QWidget

from utils.common import Colors


class Viewer(QFrame):
    """Viewer widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Viewer."""
        super().__init__(parent=parent)
        self.__playlist: QListWidget = QListWidget(self)
        self.__radius: int = 6
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__playlist)
        self.set_style()

    @property
    def playlist(self) -> QListWidget:
        """Return playlist."""
        return self.__playlist

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                border-radius: {self.__radius}px;
                border: 1px solid {Colors.BACKGROUND.value.hex};
            }}
        """)
        self.__playlist.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                font-size: 14px;
                outline: 0;
            }}
            QListWidget::item {{
                background-color: transparent;
                border-bottom: 1px solid #303030;
                border-radius: {self.__radius}px;
                padding: 6px;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
                border-left: 3px solid {Colors.ACCENT_1.value.hex};
            }}
            QListWidget::item:hover {{
                background-color: #2A2A2A;
                border-radius: {self.__radius}px;
            }}
        """)

if __name__ == "__main__":
    ...
