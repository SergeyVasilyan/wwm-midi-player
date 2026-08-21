"""Per-track mute panel: one row per playable track, each with a ToggleSwitch."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.toggle_switch import ToggleSwitch
from utils.common import RADIUS_MD, SPACING_SM, Colors, note_color_hex
from utils.note_events import TrackSummary

SWATCH_SIZE: int = 12


class _TrackRow(QWidget):
    """One track row: color swatch, name label, mute ToggleSwitch."""

    toggled: Signal = Signal(int, bool)

    def __init__(self, track: TrackSummary, parent: QWidget|None=None) -> None:
        """Initialize a row for one track, defaulting its toggle to ON/unmuted."""
        super().__init__(parent=parent)
        self.__index: int = track.index
        swatch: QLabel = QLabel()
        swatch.setFixedSize(SWATCH_SIZE, SWATCH_SIZE)
        swatch.setStyleSheet(
            f"background-color: {note_color_hex(track.index, track.is_drum)}; "
            f"border-radius: {SWATCH_SIZE // 2}px;")
        name_label: QLabel = QLabel(track.name)
        name_label.setStyleSheet(f"color: {Colors.WHITE.value.hex}; background: transparent;")
        switch: ToggleSwitch = ToggleSwitch()
        switch.setChecked(True)
        # Connect after setChecked(True), not before: setChecked() on a
        # freshly-constructed (default-unchecked) button changes its state
        # and would otherwise emit toggled(True) into an already-wired
        # connection, spamming Player with a redundant "unmute" report for
        # every single row on initial load.
        switch.toggled.connect(lambda checked: self.toggled.emit(self.__index, checked))
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING_SM, SPACING_SM // 2, SPACING_SM, SPACING_SM // 2)
        layout.addWidget(swatch)
        layout.addWidget(name_label, stretch=1)
        layout.addWidget(switch)


class TrackListPanel(QFrame):
    """Track-mute panel, styled like Viewer: one row per playable track of the current song."""

    track_toggled: Signal = Signal(int, bool)

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize TrackListPanel."""
        super().__init__(parent=parent)
        self.__widget: QListWidget = QListWidget(self)
        self.__widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.__widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__widget)
        self.__set_style()

    def load_tracks(self, tracks: list[TrackSummary]) -> None:
        """Clear and rebuild one row per track, in ascending track-index order."""
        self.clear()
        for track in tracks:
            row: _TrackRow = _TrackRow(track)
            row.toggled.connect(self.track_toggled)
            item: QListWidgetItem = QListWidgetItem(self.__widget)
            item.setSizeHint(row.sizeHint())
            self.__widget.addItem(item)
            self.__widget.setItemWidget(item, row)

    def clear(self) -> None:
        """Remove all rows (song changed, playback errored, or playlist cleared)."""
        self.__widget.clear()

    def __set_style(self) -> None:
        """Apply the same panel chrome as Viewer for visual consistency."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                border-radius: {RADIUS_MD}px;
                border: 1px solid {Colors.BACKGROUND.value.hex};
            }}
        """)
        self.__widget.setStyleSheet("""
            QListWidget { background-color: transparent; border: none; outline: 0; }
        """)

if __name__ == "__main__":
    ...
