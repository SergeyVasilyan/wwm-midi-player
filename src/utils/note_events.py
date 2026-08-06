"""Precompute the full list of note on/off events for the visualizer.

Runs ahead of/alongside real-time playback rather than during it, so the UI
can draw falling notes before they're actually triggered.
"""

from dataclasses import dataclass

import mido

from utils.midi_timing import build_tempo_map

DRUM_CHANNEL: int = 9  # GM channel 10 (0-indexed) is reserved for percussion.


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """A single sounded note: channel, pitch, absolute on/off time, program, track."""

    channel: int
    note: int
    velocity: int
    start: float
    end: float
    program: int
    is_drum: bool
    track: int


class _TickClock:
    """Converts a single track's monotonically increasing absolute ticks to seconds.

    utils.midi_timing.ticks_to_seconds() re-walks the whole tempo map from
    tick 0 on every call, which is fine for the one-off duration calculation
    it was written for, but calling it once per note on/off made
    build_note_events O(events * tempo changes) - slow enough on
    tempo-change-heavy files (common in expressive film/game scores) to
    visibly stall the GUI thread's mandatory Worker.wait() when switching
    tracks. Ticks only increase within one track, so this instead walks the
    tempo map forward incrementally, making the whole precompute O(events +
    tempo changes).
    """

    def __init__(self, tempo_map: list[tuple[int, int]], ticks_per_beat: int) -> None:
        self.__tempo_map: list[tuple[int, int]] = tempo_map
        self.__ticks_per_beat: int = ticks_per_beat
        self.__index: int = 0
        self.__elapsed: float = 0.0
        self.__prev_tick, self.__prev_tempo = tempo_map[0]

    def seconds_at(self, abs_ticks: int) -> float:
        """Return the elapsed seconds at abs_ticks; abs_ticks must not decrease between calls."""
        tempo_map: list[tuple[int, int]] = self.__tempo_map
        while self.__index + 1 < len(tempo_map) and tempo_map[self.__index + 1][0] <= abs_ticks:
            next_tick, next_tempo = tempo_map[self.__index + 1]
            segment_ticks: int = next_tick - self.__prev_tick
            self.__elapsed += mido.tick2second(segment_ticks, self.__ticks_per_beat,
                                                self.__prev_tempo)
            self.__prev_tick, self.__prev_tempo = next_tick, next_tempo
            self.__index += 1
        segment_ticks = abs_ticks - self.__prev_tick
        return self.__elapsed + mido.tick2second(segment_ticks, self.__ticks_per_beat,
                                                   self.__prev_tempo)


def build_note_events(midi: mido.MidiFile) -> list[NoteEvent]:
    """Return all note events in the file, sorted by start time.

    Walks each track's own delta-tick stream and converts ticks to seconds via
    the shared tempo map (utils.midi_timing.build_tempo_map), tagging every
    event with its originating track index. This is deliberate: many
    real-world files route every instrument through the same MIDI channel
    (commonly channel 0) and differentiate instruments by track instead, so
    the visualizer colors notes by track rather than channel - iterating
    mido's channel-merged real-time playback stream (as Worker.run() does)
    would lose that track identity entirely. Notes still open at EOF are
    closed at their own start time (a zero-length bar) instead of being
    dropped.
    """
    tempo_map: list[tuple[int, int]] = build_tempo_map(midi)
    open_notes: dict[tuple[int, int, int], tuple[float, int, int]] = {}
    programs: dict[int, int] = {}
    events: list[NoteEvent] = []
    for track_index, track in enumerate(midi.tracks):
        abs_ticks: int = 0
        clock: _TickClock = _TickClock(tempo_map, midi.ticks_per_beat)
        for msg in track:
            abs_ticks += msg.time
            if msg.type == "program_change":
                programs[msg.channel] = msg.program
            elif msg.type == "note_on" and msg.velocity > 0:
                start: float = clock.seconds_at(abs_ticks)
                key: tuple[int, int, int] = (track_index, msg.channel, msg.note)
                open_notes[key] = (start, msg.velocity, programs.get(msg.channel, 0))
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                key = (track_index, msg.channel, msg.note)
                opened = open_notes.pop(key, None)
                if opened is not None:
                    start, velocity, program = opened
                    end: float = clock.seconds_at(abs_ticks)
                    events.append(NoteEvent(msg.channel, msg.note, velocity, start, end,
                                             program, msg.channel == DRUM_CHANNEL, track_index))
    for (track_index, channel, note), (start, velocity, program) in open_notes.items():
        events.append(NoteEvent(channel, note, velocity, start, start, program,
                                 channel == DRUM_CHANNEL, track_index))
    events.sort(key=lambda event: event.start)
    return events
