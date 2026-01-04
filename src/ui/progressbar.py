"""ProgressBar widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar, QWidget
from src.utils.common import Colors


class ProgressBar(QProgressBar):
    """ProgressBar widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize ProgressBar."""
        super().__init__(parent=parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setFixedHeight(6)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setTextVisible(False)
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.BACKGROUND.value.hex};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT_1.value.hex}, stop:1 #C0A060
                );
            }}
        """)

if "__main__" == __name__:
    ...
