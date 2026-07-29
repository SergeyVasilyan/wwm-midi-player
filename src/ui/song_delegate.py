"""Item delegate providing animated hover/press feedback for the song list."""

from typing import override

from PySide6.QtCore import QEvent, QModelIndex, QObject
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import QListWidget, QStyle, QStyledItemDelegate, QStyleOptionViewItem

from ui.animation import AnimatedProgress
from utils.common import Colors

HOVER_DURATION_MS = 120
PRESS_DURATION_MS = 80
HOVER_MAX_ALPHA = 140
PRESS_EXTRA_ALPHA = 40


class SongDelegate(QStyledItemDelegate):
    """Paints an animated hover/press overlay under the default item content."""

    def __init__(self, view: QListWidget, parent: QObject|None=None) -> None:
        """Initialize the delegate and wire hover/press tracking on view."""
        super().__init__(parent=parent)
        self.__view: QListWidget = view
        self.__hovered_row: int = -1
        self.__pressed_row: int = -1
        self.__hover: AnimatedProgress = AnimatedProgress(
            self, self.__on_progress_changed, HOVER_DURATION_MS)
        self.__press: AnimatedProgress = AnimatedProgress(
            self, self.__on_progress_changed, PRESS_DURATION_MS)
        view.viewport().setMouseTracking(True)
        view.entered.connect(self.__on_entered)
        view.viewport().installEventFilter(self)

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Reset hover/press state on viewport leave and track press/release."""
        if event.type() == QEvent.Type.Leave:
            self.__hovered_row = -1
            self.__hover.animate_to(0.0)
        elif event.type() == QEvent.Type.MouseButtonPress:
            row: int = self.__view.indexAt(event.position().toPoint()).row()
            self.__pressed_row = row
            self.__press.snap_to(0.0)
            self.__press.animate_to(1.0)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.__press.animate_to(0.0)
        return super().eventFilter(obj, event)

    def __on_entered(self, index: QModelIndex) -> None:
        """Snap the previously-hovered row to 0 and animate the newly-hovered row 0->1."""
        if index.row() == self.__hovered_row:
            return
        self.__hovered_row = index.row()
        self.__hover.snap_to(0.0)
        self.__hover.animate_to(1.0)

    def __on_progress_changed(self, _value: float) -> None:
        """Repaint the viewport as hover/press progress changes."""
        self.__view.viewport().update()

    @override
    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
                    index: QModelIndex) -> None:
        """Paint the row's own background first, then blend hover/press, then default content."""
        opt: QStyleOptionViewItem = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        if opt.backgroundBrush != QBrush():
            painter.fillRect(opt.rect, opt.backgroundBrush)
            opt.backgroundBrush = QBrush()
        if index.row() == self.__hovered_row and self.__hover.value > 0:
            tint: QColor = QColor(Colors.BACKGROUND_2.value.qcolor)
            tint.setAlpha(int(HOVER_MAX_ALPHA * self.__hover.value))
            painter.fillRect(opt.rect, tint)
        if index.row() == self.__pressed_row and self.__press.value > 0:
            extra: QColor = QColor(Colors.BLACK.value.qcolor)
            extra.setAlpha(int(PRESS_EXTRA_ALPHA * self.__press.value))
            painter.fillRect(opt.rect, extra)
        opt.state &= ~QStyle.StateFlag.State_MouseOver
        painter.restore()
        super().paint(painter, opt, index)

if __name__ == "__main__":
    ...
