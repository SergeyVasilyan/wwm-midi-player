"""Playlist widget."""

from PySide6.QtWidgets import QListWidget, QWidget


class PlayList(QListWidget):
    """Playlist widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize toggle."""
        super().__init__(parent=parent)
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet("""
            QListWidget {
                background-color: #1A1A1A;
                color: #E0E0E0;
                border: 1px solid #8D6E63;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #2E7D32;
                color: #FFFFFF;
            }
        """)

if "__main__" == __name__:
    ...
