"""Playlist widget."""

from PySide6.QtWidgets import QListWidget, QWidget
from src.utils.common import Colors


class PlayList(QListWidget):
    """Playlist widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize playlist."""
        super().__init__(parent=parent)
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.BACKGROUND.value.hex};
                border: none;
                color: #E0E0E0;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid #303030;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
                border-left: 3px solid {Colors.ACCENT_1.value.hex};
                color: #E0E0E0;
            }}
            QListWidget::item:hover {{
                background-color: #2A2A2A;
            }}
        """)

if "__main__" == __name__:
    ...
