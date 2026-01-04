"""Volume slider widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget
from src.utils.common import Colors


class Volume(QSlider):
    """Volume slider widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Volume slider widget."""
        super().__init__(parent=parent)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setRange(0, 127)
        self.setValue(100)
        self.set_style()

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {Colors.BACKGROUND.value.hex};
                border: 1px solid {Colors.ACCENT_2.value.hex};
                border-radius: 4px;
                height: 8px;
            }}
            QSlider::handle:horizontal {{
                background: {Colors.ACCENT_1.value.hex};
                border: 1px solid #C0A060;
                border-radius: 8px;
                width: 16px;
                height: 16px;
                margin: -4px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: #C0A060;
            }}
            QSlider::sub-page:horizontal {{
                background: {Colors.ACCENT_1.value.hex};
                border-radius: 4px;
            }}
        """)

if "__main__" == __name__:
    ...
