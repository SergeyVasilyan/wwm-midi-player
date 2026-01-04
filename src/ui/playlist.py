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
                background-color: #1A1A1A;
                border: 1px solid {Colors.ACCENT_2.value.hex};
                color: #E0E0E0;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT_1.value.hex};
                color: #FFFFFF;
            }}
        """)

if "__main__" == __name__:
    ...
