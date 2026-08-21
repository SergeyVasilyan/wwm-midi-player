"""Synthesia-style falling-note piano visualizer panel."""

import bisect
from typing import override

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from utils.common import Colors, note_color_hex
from utils.note_events import NoteEvent
from utils.piano_layout import (
    MIDI_NOTE_MAX,
    MIDI_NOTE_MIN,
    clamp_note,
    is_white_key,
    key_width,
    key_x_position,
)

KEYBOARD_HEIGHT_RATIO: float = 0.22
LOOKAHEAD_SECONDS: float = 3.0
MIN_BAR_HEIGHT: float = 3.0
BAR_MARGIN_RATIO: float = 0.12
BAR_CORNER_RADIUS: float = 5.0
KEY_CORNER_RADIUS: float = 3.0
BLACK_KEY_HEIGHT_RATIO: float = 0.62
HIT_LINE_HEIGHT: float = 3.0


class PianoVisualizer(QWidget):
    """Draws an 88-key keyboard with falling note bars synced to playback position."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """Initialize PianoVisualizer."""
        super().__init__(parent=parent)
        self.__events: list[NoteEvent] = []
        self.__starts: list[float] = []
        self.__max_note_duration: float = 0.0
        self.__duration: float = 0.0
        self.__position: float = 0.0
        self.__muted_tracks: set[int] = set()
        self.__geometry_width: float = -1.0
        self.__key_geometry: dict[int, tuple[float, float]] = {}
        self.setAutoFillBackground(False)

    def load_notes(self, events: list[NoteEvent], duration: float) -> None:
        """Replace the current note set for a newly-loaded track and reset scroll."""
        self.__events = events
        self.__starts = [event.start for event in events]
        self.__max_note_duration = max((event.end - event.start for event in events), default=0.0)
        self.__duration = duration
        self.__position = 0.0
        self.update()

    def set_position(self, seconds: float) -> None:
        """Update the current playback time; triggers a repaint."""
        self.__position = seconds
        self.update()

    def set_muted_tracks(self, tracks: set[int]) -> None:
        """Hide falling notes/keyboard highlights for the given tracks; repaints immediately."""
        self.__muted_tracks = tracks
        self.update()

    def clear(self) -> None:
        """Reset to the empty/idle state (stop, track switch, playlist clear)."""
        self.__events = []
        self.__starts = []
        self.__max_note_duration = 0.0
        self.__duration = 0.0
        self.__position = 0.0
        self.__muted_tracks = set()
        self.update()

    def __ensure_key_geometry(self) -> None:
        """(Re)compute per-note (x, width) once per width change, not every frame.

        key_x_position()/white_key_index() do an O(range) scan per call; calling
        them for all 88 notes on every paintEvent (30fps) was the main source of
        visible animation stutter. The geometry only actually changes when the
        widget is resized, so cache it and recompute only then.
        """
        width: float = self.width()
        if width == self.__geometry_width:
            return
        self.__geometry_width = width
        self.__key_geometry = {
            note: (key_x_position(note, width), key_width(note, width))
            for note in range(MIDI_NOTE_MIN, MIDI_NOTE_MAX + 1)
        }

    def __visible_events(self) -> list[NoteEvent]:
        """Return events that overlap the current lookahead window, cheaply.

        self.__events is pre-sorted by start time (utils.note_events.build_note_events
        guarantees this), so a bisect finds the first note that could still be visible;
        the scan then stops as soon as a note starts beyond the window instead of
        walking the whole file every frame. The bisect target is pushed back by
        self.__max_note_duration (not just the 0.5s margin) so a long/sustained note
        that started well before the window - but is still sounding - isn't skipped:
        bisecting on window_start alone would cut it off mid-fall as soon as its start
        time fell behind the window.
        """
        window_start: float = self.__position - 0.5
        window_end: float = self.__position + LOOKAHEAD_SECONDS
        lookback: float = window_start - self.__max_note_duration
        first_index: int = bisect.bisect_left(self.__starts, lookback)
        visible: list[NoteEvent] = []
        for event in self.__events[first_index:]:
            if event.start > window_end:
                break
            if event.track in self.__muted_tracks:
                continue
            if event.end >= window_start:
                visible.append(event)
        return visible

    def __draw_falling_notes(self, painter: QPainter, fall_rect: QRectF) -> None:
        """Draw one bar per visible note, colored by originating track.

        Bars are inset from the full key width so adjacent notes read as
        distinct blocks, and shaded with a vertical gradient that brightens
        toward the keyboard to suggest motion toward the strike line.
        """
        pixels_per_second: float = fall_rect.height() / LOOKAHEAD_SECONDS
        for event in self.__visible_events():
            note: int = clamp_note(event.note)
            x, width = self.__key_geometry[note]
            top: float = fall_rect.bottom() - (event.end - self.__position) * pixels_per_second
            bottom: float = (fall_rect.bottom()
                              - (event.start - self.__position) * pixels_per_second)
            top = max(top, fall_rect.top())
            bottom = min(bottom, fall_rect.bottom())
            if bottom - top < MIN_BAR_HEIGHT:
                bottom = top + MIN_BAR_HEIGHT
            margin: float = max(1.0, width * BAR_MARGIN_RATIO)
            bar_rect: QRectF = QRectF(x + margin, top, width - margin * 2, bottom - top)
            base_color: QColor = QColor(note_color_hex(event.track, event.is_drum))
            gradient: QLinearGradient = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
            gradient.setColorAt(0.0, base_color.darker(125))
            gradient.setColorAt(1.0, base_color.lighter(135))
            painter.setPen(QPen(base_color.lighter(160), 1))
            painter.setBrush(QBrush(gradient))
            radius: float = min(BAR_CORNER_RADIUS, bar_rect.width() / 2)
            painter.drawRoundedRect(bar_rect, radius, radius)

    def __sounding_notes(self) -> dict[int, str]:
        """Return clamped note numbers currently sounding, mapped to their track color."""
        sounding: dict[int, str] = {}
        for event in self.__visible_events():
            if event.start <= self.__position <= event.end:
                sounding[clamp_note(event.note)] = note_color_hex(event.track, event.is_drum)
        return sounding

    def __draw_hit_line(self, painter: QPainter, fall_rect: QRectF) -> None:
        """Draw a thin glowing line marking where falling notes strike the keys."""
        line_rect: QRectF = QRectF(fall_rect.left(), fall_rect.bottom() - HIT_LINE_HEIGHT,
                                    fall_rect.width(), HIT_LINE_HEIGHT)
        # Copy rather than mutate the shared Colors.ACCENT_1 QColor instance in place.
        color: QColor = QColor(Colors.ACCENT_1.value.qcolor)
        color.setAlpha(160)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(line_rect)

    def __draw_white_keys(self, painter: QPainter, keyboard_rect: QRectF,
                                sounding: dict[int, str]) -> None:
        """Draw the white keys with a subtle top-to-bottom shading for depth."""
        painter.setPen(QPen(Colors.BACKGROUND.value.qcolor, 1))
        for note in range(MIDI_NOTE_MIN, MIDI_NOTE_MAX + 1):
            if not is_white_key(note):
                continue
            x, width = self.__key_geometry[note]
            rect: QRectF = QRectF(x, keyboard_rect.top(), width, keyboard_rect.height())
            gradient: QLinearGradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if note in sounding:
                glow: QColor = QColor(sounding[note])
                gradient.setColorAt(0.0, glow.lighter(150))
                gradient.setColorAt(1.0, glow)
            else:
                gradient.setColorAt(0.0, QColor(Colors.WHITE.value.hex))
                gradient.setColorAt(1.0, QColor("#D8D8D8"))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(rect, KEY_CORNER_RADIUS, KEY_CORNER_RADIUS)

    def __draw_black_keys(self, painter: QPainter, keyboard_rect: QRectF,
                                sounding: dict[int, str]) -> None:
        """Draw the black keys on top of the white keys, shaded for depth."""
        black_height: float = keyboard_rect.height() * BLACK_KEY_HEIGHT_RATIO
        painter.setPen(Qt.PenStyle.NoPen)
        for note in range(MIDI_NOTE_MIN, MIDI_NOTE_MAX + 1):
            if is_white_key(note):
                continue
            x, width = self.__key_geometry[note]
            rect: QRectF = QRectF(x, keyboard_rect.top(), width, black_height)
            gradient: QLinearGradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if note in sounding:
                glow: QColor = QColor(sounding[note])
                gradient.setColorAt(0.0, glow.lighter(140))
                gradient.setColorAt(1.0, glow.darker(110))
            else:
                gradient.setColorAt(0.0, QColor("#3A3A3A"))
                gradient.setColorAt(1.0, QColor(Colors.BLACK.value.hex))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(rect, KEY_CORNER_RADIUS, KEY_CORNER_RADIUS)

    def __draw_keyboard(self, painter: QPainter, keyboard_rect: QRectF) -> None:
        """Draw white keys, then black keys on top, highlighting sounding notes."""
        sounding: dict[int, str] = self.__sounding_notes()
        self.__draw_white_keys(painter, keyboard_rect, sounding)
        self.__draw_black_keys(painter, keyboard_rect, sounding)

    @override
    def paintEvent(self, _event: QPaintEvent) -> None:
        """Paint the falling-notes area and the piano keyboard."""
        self.__ensure_key_geometry()
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        background: QLinearGradient = QLinearGradient(0, 0, 0, self.height())
        background.setColorAt(0.0, QColor(Colors.BACKGROUND.value.hex))
        background.setColorAt(1.0, QColor(Colors.BACKGROUND_1.value.hex))
        painter.fillRect(self.rect(), QBrush(background))
        keyboard_height: float = self.height() * KEYBOARD_HEIGHT_RATIO
        fall_rect: QRectF = QRectF(0, 0, self.width(), self.height() - keyboard_height)
        keyboard_rect: QRectF = QRectF(0, fall_rect.bottom(), self.width(), keyboard_height)
        self.__draw_falling_notes(painter, fall_rect)
        self.__draw_hit_line(painter, fall_rect)
        self.__draw_keyboard(painter, keyboard_rect)
        painter.end()

if __name__ == "__main__":
    ...
