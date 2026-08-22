"""Floating toast notification: a compact, auto-dismissing overlay card."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.animation import AnimatedProgress
from utils.common import RADIUS_MD, SPACING_MD, SPACING_SM, Colors

DISMISS_AFTER_MS = 5_000
FADE_DURATION_MS = 200
MAX_WIDTH = 380
MARGIN = SPACING_MD * 2


class Toast(QFrame):
    """Compact, auto-dismissing notification card that floats above the window's content.

    Unlike a banner embedded in a layout, this never reflows/pushes the rest
    of the UI: it's a free-floating child positioned in the parent's
    top-right corner, raised above its siblings, and faded in/out rather
    than inserted/removed.
    """

    dismissed: Signal = Signal()

    def __init__(self, message: str, parent: QWidget) -> None:
        """Initialize Toast, fade it in, and position it in parent's top-right corner."""
        super().__init__(parent=parent)
        self.__is_dismissed: bool = False
        self.setMaximumWidth(MAX_WIDTH)
        self.__construct_layout(message)
        self.__set_style()
        opacity: QGraphicsOpacityEffect = QGraphicsOpacityEffect(self)
        opacity.setOpacity(0.0)
        self.setGraphicsEffect(opacity)
        self.__fade: AnimatedProgress = AnimatedProgress(
            self, opacity.setOpacity, FADE_DURATION_MS)
        self.reposition()
        self.show()
        self.raise_()
        self.__fade.animate_to(1.0)
        QTimer.singleShot(DISMISS_AFTER_MS, self.__request_dismiss)

    def reposition(self) -> None:
        """Anchor to the parent's top-right corner; call again if the parent resizes."""
        parent: QWidget|None = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()
        x: int = parent.width() - self.width() - MARGIN
        self.move(max(MARGIN, x), MARGIN)

    def __request_dismiss(self) -> None:
        """Fade out, then actually hide and notify once the fade finishes."""
        if self.__is_dismissed:
            return
        self.__is_dismissed = True
        self.__fade.animate_to(0.0)
        QTimer.singleShot(FADE_DURATION_MS, self.__finish_dismiss)

    def __finish_dismiss(self) -> None:
        """Hide and emit dismissed, once the fade-out animation has finished."""
        self.hide()
        self.dismissed.emit()

    def __construct_layout(self, message: str) -> None:
        """Construct Toast layout."""
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
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
                background-color: {Colors.BACKGROUND_2.value.hex};
            }}
            QPushButton:pressed {{
                background-color: {Colors.ACCENT_1.value.hex};
            }}
        """)
        close_button.clicked.connect(self.__request_dismiss)
        layout.addWidget(icon, stretch=0)
        layout.addWidget(label, stretch=1)
        layout.addWidget(close_button, stretch=0)

    def __set_style(self) -> None:
        """Apply the exact same card chrome as Viewer/TrackListPanel/dialogs.

        A mismatched-width border-left "accent edge" combined with
        border-radius is a real Qt QSS rendering trap: at a rounded corner,
        Qt has to reconcile two different edge thicknesses meeting at the
        arc, and draws a visible seam/double line instead of a clean curve.
        Simplest fix is to not fight it - use one uniform border like every
        other card, and let the red icon badge alone carry the "this is an
        error" signal.
        """
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                border: 1px solid {Colors.BACKGROUND_2.value.hex};
                border-radius: {RADIUS_MD}px;
            }}
        """)

if __name__ == "__main__":
    ...
