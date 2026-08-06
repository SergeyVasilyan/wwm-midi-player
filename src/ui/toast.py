"""Toast/banner widget for non-blocking notifications."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from utils.common import RADIUS_MD, SPACING_MD, SPACING_SM, Colors

DISMISS_AFTER_MS = 5_000


class Toast(QFrame):
    """Non-blocking, dismissible notification banner."""

    dismissed: Signal = Signal()

    def __init__(self, message: str, parent: QWidget|None=None) -> None:
        """Initialize Toast."""
        super().__init__(parent=parent)
        self.__is_dismissed: bool = False
        self.__construct_layout(message)
        self.set_style()
        QTimer.singleShot(DISMISS_AFTER_MS, self.__dismiss)

    def __dismiss(self) -> None:
        """Emit dismissed once, guarding against a double-fire from timer + click."""
        if self.__is_dismissed:
            return
        self.__is_dismissed = True
        self.dismissed.emit()

    def __construct_layout(self, message: str) -> None:
        """Construct Toast layout."""
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_SM, SPACING_SM)
        layout.setSpacing(SPACING_SM)
        # "!" (plain ASCII) rather than a Unicode warning-sign glyph, which
        # isn't covered by every font and can render as a garbled fallback
        # glyph instead of an icon.
        icon: QLabel = QLabel("!")
        icon.setFixedSize(20, 20)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"""
            background-color: {Colors.RED.value.hex};
            color: {Colors.WHITE.value.hex};
            font-weight: bold;
            border-radius: 10px;
        """)
        label: QLabel = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {Colors.WHITE.value.hex}; background: transparent;")
        close_button: QPushButton = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background: none;
                border: none;
                color: #999999;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                color: {Colors.WHITE.value.hex};
                background-color: {Colors.BACKGROUND.value.hex};
            }}
        """)
        close_button.clicked.connect(self.__dismiss)
        layout.addWidget(icon, stretch=0)
        layout.addWidget(label, stretch=1)
        layout.addWidget(close_button, stretch=0)

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_2.value.hex};
                border-left: 3px solid {Colors.RED.value.hex};
                border-radius: {RADIUS_MD}px;
            }}
        """)

if __name__ == "__main__":
    ...
