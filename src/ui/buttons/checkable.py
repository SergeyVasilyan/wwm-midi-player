"""Base for checkable icon buttons with an animated active-state fade."""

from PySide6.QtWidgets import QWidget

from ui.animation import AnimatedProgress
from ui.buttons.abstract import AbstractButton

ACTIVE_ANIMATION_DURATION_MS = 200
INACTIVE_ALPHA = 90
ACTIVE_ALPHA = 255
INACTIVE_BACKGROUND_ALPHA = 15
ACTIVE_BACKGROUND_ALPHA = 110


class CheckableIconButton(AbstractButton):
    """Checkable icon button that fades its glyph in/out on toggle."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize Checkable Icon Button widget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent=parent)
        self.setCheckable(True)
        self.__active: AnimatedProgress = AnimatedProgress(
            self, self.__on_active_changed, ACTIVE_ANIMATION_DURATION_MS)
        self.toggled.connect(self.__animate_active)

    def _active_alpha(self) -> int:
        """Return the current glyph alpha, interpolated by the active-state animation.

        Returns:
            The glyph alpha (0-255).
        """
        return INACTIVE_ALPHA + int((ACTIVE_ALPHA - INACTIVE_ALPHA) * self.__active.value)

    def _active_background_alpha(self) -> int:
        """Return the current background alpha, interpolated by the active-state animation.

        Returns:
            The background alpha (0-255).
        """
        return INACTIVE_BACKGROUND_ALPHA + int(
            (ACTIVE_BACKGROUND_ALPHA - INACTIVE_BACKGROUND_ALPHA) * self.__active.value)

    def __on_active_changed(self, _value: float) -> None:
        """Repaint as the active-state animation progresses.

        Args:
            _value: The animation's current progress (0..1); unused, since
                painting reads live active state directly.
        """
        self.update()

    def __animate_active(self, checked: bool) -> None:
        """Animate the active-state progress toward the new checked state.

        Args:
            checked: The button's new checked state.
        """
        self.__active.animate_to(1.0 if checked else 0.0)

if __name__ == "__main__":
    ...
