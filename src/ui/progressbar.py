"""ProgressBar widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar, QWidget


class ProgressBar(QProgressBar):
    """ProgressBar widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize ProgressBar."""
        super().__init__(parent=parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setTextVisible(False)
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet("""
            QProgressBar {
                background: #1A1A1A;
                border: 1px solid #8D6E63;
                border-radius: 3px;
                height: 6px;
            }
            QProgressBar::chunk {
                border-radius: 2px;
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E7D32, stop:1 #C0A060
                );
            }
        """)

if "__main__" == __name__:
    ...
