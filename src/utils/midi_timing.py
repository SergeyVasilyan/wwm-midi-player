"""Pure MIDI timing calculations used to compute track duration."""

import mido


def build_tempo_map(midi: mido.MidiFile) -> list[tuple[int, int]]:
    """Return a list of (abs_tick, tempo_microsec_per_beat), sorted by abs_tick.

    Default tempo is 500_000 (120 BPM). Tempo messages are taken from all tracks,
    but commonly live in track 0.

    Args:
        midi: The parsed MIDI file to scan for tempo changes.

    Returns:
        A list of (abs_tick, tempo) pairs, sorted by abs_tick, always
        starting with (0, 500_000).
    """
    tempo_map: list[tuple[int, int]] = [(0, 500_000)]
    for track in midi.tracks:
        abs_ticks: int = 0
        for msg in track:
            abs_ticks += msg.time
            if msg.type == "set_tempo":
                tempo_map.append((abs_ticks, msg.tempo))
    clean_tempo_map: dict[int, int] = {}
    for tick, tempo in tempo_map:
        clean_tempo_map[tick] = tempo
    return sorted(clean_tempo_map.items())


class TickClock:
    """Converts a single track's monotonically increasing absolute ticks to seconds.

    ticks_to_seconds() re-walks the whole tempo map from tick 0 on every
    call, which is fine for the one-off duration calculation it was written
    for, but calling it once per event would make a per-track precompute
    O(events * tempo changes) - slow enough on tempo-change-heavy files
    (common in expressive film/game scores) to stall the GUI thread's
    mandatory Worker.wait(). Ticks only increase within one track, so this
    instead walks the tempo map forward incrementally, making a full
    per-track walk O(events + tempo changes). Used by both
    utils.note_events.build_note_events (visualizer precompute) and
    utils.playback_stream.build_playback_messages (live playback).
    """

    def __init__(self, tempo_map: list[tuple[int, int]], ticks_per_beat: int) -> None:
        """Initialize TickClock for one track, sharing the file's tempo_map.

        Args:
            tempo_map: (abs_tick, tempo) pairs from build_tempo_map(), shared
                read-only across every track's own TickClock instance.
            ticks_per_beat: The MIDI file's ticks-per-beat resolution.
        """
        self.__tempo_map: list[tuple[int, int]] = tempo_map
        self.__ticks_per_beat: int = ticks_per_beat
        self.__index: int = 0
        self.__elapsed: float = 0.0
        self.__prev_tick, self.__prev_tempo = tempo_map[0]

    def seconds_at(self, abs_ticks: int) -> float:
        """Return the elapsed seconds at abs_ticks; abs_ticks must not decrease between calls.

        Args:
            abs_ticks: Absolute tick position within this track; must be
                greater than or equal to the abs_ticks of the previous call.

        Returns:
            Elapsed seconds from the start of the track to abs_ticks.
        """
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


def find_max_end_tick(midi: mido.MidiFile) -> int:
    """Find max end tick value.

    Args:
        midi: The parsed MIDI file to scan.

    Returns:
        The absolute tick of the last note event across all tracks that
        contain at least one note, or 0 if no track has any notes.
    """
    max_end_tick: int = 0
    for track in midi.tracks:
        abs_ticks: int = 0
        has_notes: bool = False
        for msg in track:
            abs_ticks += msg.time
            if msg.type in ("note_on", "note_off"):
                has_notes = True
        if has_notes:
            max_end_tick = max(max_end_tick, abs_ticks)
    return max_end_tick


def ticks_to_seconds(
    midi: mido.MidiFile, max_end_tick: int, tempo_map: list[tuple[int, int]],
) -> float:
    """Convert an absolute tick position to seconds by walking the tempo segments.

    Args:
        midi: The parsed MIDI file (used for its ticks_per_beat resolution).
        max_end_tick: The absolute tick to convert to seconds.
        tempo_map: (abs_tick, tempo) pairs from build_tempo_map().

    Returns:
        The elapsed seconds from tick 0 to max_end_tick.
    """
    ticks_per_beat: int = midi.ticks_per_beat
    total_seconds: float = 0.0
    previous_tick, previous_tempo = tempo_map[0]
    for tick, tempo in tempo_map[1:]:
        segment_end: int = min(max_end_tick, tick)
        if segment_end > previous_tick:
            segment_ticks: int = segment_end - previous_tick
            total_seconds += mido.tick2second(segment_ticks, ticks_per_beat, previous_tempo)
            previous_tick = segment_end
        if max_end_tick <= tick:
            return total_seconds
        previous_tempo = tempo
    if max_end_tick > previous_tick:
        segment_ticks = max_end_tick - previous_tick
        total_seconds += mido.tick2second(segment_ticks, ticks_per_beat, previous_tempo)
    return total_seconds


def calculate_duration(midi: mido.MidiFile) -> float:
    """Calculate the overall duration of a MIDI file, in seconds.

    Args:
        midi: The parsed MIDI file to measure.

    Returns:
        The file's total duration in seconds.
    """
    tempo_map: list[tuple[int, int]] = build_tempo_map(midi)
    max_end_tick: int = find_max_end_tick(midi)
    return ticks_to_seconds(midi, max_end_tick, tempo_map)
