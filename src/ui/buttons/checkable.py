"""Base for checkable icon buttons with an animated active-state fade."""

from PySide6.QtCore import QEasingCurve, QVariantAnimation
from PySide6.QtWidgets import QWidget

from ui.buttons.abstract import AbstractButton

ACTIVE_ANIMATION_DURATION_MS = 200
INACTIVE_ALPHA = 90
ACTIVE_ALPHA = 255
INACTIVE_BACKGROUND_ALPHA = 15
ACTIVE_BACKGROUND_ALPHA = 110


class CheckableIconButton(AbstractButton):
    """Checkable icon button that fades its glyph in/out on toggle."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Checkable Icon Button widget."""
        super().__init__(parent=parent)
        self.setCheckable(True)
        self._active_progress: float = 0.0
        self.__animation: QVariantAnimation = QVariantAnimation(self)
        self.__animation.setDuration(ACTIVE_ANIMATION_DURATION_MS)
        self.__animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.__animation.valueChanged.connect(self.__on_active_progress_changed)
        self.toggled.connect(self.__animate_active)

    def _active_alpha(self) -> int:
        """Return the current glyph alpha, interpolated by the active-state animation."""
        return INACTIVE_ALPHA + int((ACTIVE_ALPHA - INACTIVE_ALPHA) * self._active_progress)

    def _active_background_alpha(self) -> int:
        """Return the current background alpha, interpolated by the active-state animation."""
        return INACTIVE_BACKGROUND_ALPHA + int(
            (ACTIVE_BACKGROUND_ALPHA - INACTIVE_BACKGROUND_ALPHA) * self._active_progress)

    def __on_active_progress_changed(self, value: float) -> None:
        """Repaint as the active-state animation progresses."""
        self._active_progress = value
        self.update()

    def __animate_active(self, checked: bool) -> None:
        """Animate the active-state progress toward the new checked state."""
        self.__animation.stop()
        self.__animation.setStartValue(self._active_progress)
        self.__animation.setEndValue(1.0 if checked else 0.0)
        self.__animation.start()

if __name__ == "__main__":
    ...
