"""Volume slider widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget

from utils.common import Colors, theme_bus


class Volume(QSlider):
    """Volume slider widget.."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Volume slider widget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent=parent)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setRange(0, 127)
        self.setValue(100)
        self.set_style()
        theme_bus.changed.connect(self.set_style)

    def set_style(self) -> None:
        """Apply the gradient-filled track and handle styling."""
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {Colors.BACKGROUND_2.value.hex};
                border: none;
                border-radius: 4px;
                height: 8px;
            }}
            QSlider::handle:horizontal {{
                background: {Colors.WHITE.value.hex};
                border: none;
                border-radius: 8px;
                width: 16px;
                height: 16px;
                margin: -4px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: #C0A060;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT_1.value.hex}, stop:1 #C0A060
                );
                border-radius: 4px;
            }}
        """)

if __name__ == "__main__":
    ...
