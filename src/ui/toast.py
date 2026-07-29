"""Toast/banner widget for non-blocking notifications."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from utils.common import Colors

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
        layout.setContentsMargins(12, 8, 8, 8)
        label: QLabel = QLabel(message)
        label.setWordWrap(True)
        close_button: QPushButton = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-weight: bold;
            }
        """)
        close_button.clicked.connect(self.__dismiss)
        layout.addWidget(label, stretch=1)
        layout.addWidget(close_button, stretch=0)

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_2.value.hex};
                border-left: 3px solid {Colors.RED.value.hex};
                border-radius: 10px;
            }}
        """)

if __name__ == "__main__":
    ...
