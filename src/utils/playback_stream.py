"""Track-tagged, time-sorted, real-time-ready MIDI message stream for live playback.

mido.MidiFile's own real-time iterator (used by the old Worker.run() loop)
merges all tracks and converts ticks to seconds internally, but discards
which track each message came from - there is no way to recover track
identity from it. This module re-derives the same real-time stream by
walking each track independently (mirroring utils.note_events.build_note_events:
its own delta-tick accumulator + its own TickClock instance per track), so
track-based muting can filter live playback messages the same way
build_note_events already lets the visualizer filter falling notes.
"""

from dataclasses import dataclass

import mido

from utils.midi_timing import TickClock, build_tempo_map

# Everything else (pitchwheel, aftertouch, sysex, meta messages...) is already
# silently dropped by Worker.run()'s current message-type checks; filtering
# here keeps that exact behavior rather than expanding scope.
_HANDLED_TYPES: frozenset[str] = frozenset(
    {"note_on", "note_off", "control_change", "program_change"})


@dataclass(frozen=True, slots=True)
class PlaybackMessage:
    """One playback-relevant message: absolute song time, originating track, raw message."""

    time: float
    track: int
    message: mido.Message


def build_playback_messages(midi: mido.MidiFile) -> list[PlaybackMessage]:
    """Return every note_on/note_off/control_change/program_change, globally time-sorted.

    Messages are first appended track-by-track (ascending track index, each
    track's own original in-track order preserved), then sorted once by
    .time with Python's stable list.sort() - so two messages at the exact
    same instant keep their original relative order whenever that order
    matters, e.g. a program_change immediately before a note_on at the same
    tick in the same track stays program_change-then-note_on. Across
    different tracks at the same instant, order falls out as ascending track
    index (an implementation detail, not a documented guarantee - MIDI does
    not define a cross-track tie order for simultaneous events anyway).
    """
    tempo_map: list[tuple[int, int]] = build_tempo_map(midi)
    out: list[PlaybackMessage] = []
    for track_index, track in enumerate(midi.tracks):
        abs_ticks: int = 0
        clock: TickClock = TickClock(tempo_map, midi.ticks_per_beat)
        for msg in track:
            abs_ticks += msg.time
            if msg.type not in _HANDLED_TYPES:
                continue
            out.append(PlaybackMessage(clock.seconds_at(abs_ticks), track_index, msg))
    out.sort(key=lambda pm: pm.time)
    return out
