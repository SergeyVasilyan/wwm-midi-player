"""Shared 0..1 animated-progress helper for hover/press/active-state feedback."""

from collections.abc import Callable

from PySide6.QtCore import QEasingCurve, QObject, QVariantAnimation

DEFAULT_DURATION_MS = 150


class AnimatedProgress:
    """Composable animated 0..1 value, driven by a QVariantAnimation.

    Not a mixin: constructed with a QObject to parent the underlying
    QVariantAnimation (for lifetime management) and a callback invoked on
    every value change (typically a widget repaint trigger). Multiple widget
    types can hold one or more instances of this without any inheritance
    relationship between them (PySide6 forbids multiple inheritance across
    two different QObject-derived branches).
    """

    def __init__(self, parent: QObject, on_change: Callable[[float], None],
                 duration_ms: int=DEFAULT_DURATION_MS,
                 easing: QEasingCurve.Type=QEasingCurve.Type.InOutCubic) -> None:
        """Initialize the progress value at 0.0 and wire the animation.

        Args:
            parent: QObject to parent the underlying QVariantAnimation to,
                for lifetime management.
            on_change: Callback invoked with the new value on every change.
            duration_ms: Animation duration in milliseconds.
            easing: Easing curve applied to the animation.
        """
        self.__value: float = 0.0
        self.__on_change: Callable[[float], None] = on_change
        self.__animation: QVariantAnimation = QVariantAnimation(parent)
        self.__animation.setDuration(duration_ms)
        self.__animation.setEasingCurve(easing)
        self.__animation.valueChanged.connect(self.__on_value_changed)

    @property
    def value(self) -> float:
        """Return the current progress value.

        Returns:
            The current progress value in the 0..1 range.
        """
        return self.__value

    def animate_to(self, target: float) -> None:
        """Animate from the current value toward target.

        Args:
            target: The value to animate toward.
        """
        self.__animation.stop()
        self.__animation.setStartValue(self.__value)
        self.__animation.setEndValue(target)
        self.__animation.start()

    def snap_to(self, value: float) -> None:
        """Jump instantly to value, bypassing animation, still notifying on_change.

        Args:
            value: The value to jump to.
        """
        self.__animation.stop()
        self.__on_value_changed(value)

    def __on_value_changed(self, value: float) -> None:
        """Store the new value and notify the owner.

        Args:
            value: The animation's new current value.
        """
        self.__value = value
        self.__on_change(value)

if __name__ == "__main__":
    ...
