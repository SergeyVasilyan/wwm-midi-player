"""Pure MIDI timing calculations used to compute track duration."""

import mido


def build_tempo_map(midi: mido.MidiFile) -> list[tuple[int, int]]:
    """Return a list of (abs_tick, tempo_microsec_per_beat), sorted by abs_tick.

    Default tempo is 500_000 (120 BPM). Tempo messages are taken from all tracks,
    but commonly live in track 0.
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


def find_max_end_tick(midi: mido.MidiFile) -> int:
    """Find max end tick value."""
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
    """Convert an absolute tick position to seconds by walking the tempo segments."""
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
    """Calculate the overall duration of a MIDI file, in seconds."""
    tempo_map: list[tuple[int, int]] = build_tempo_map(midi)
    max_end_tick: int = find_max_end_tick(midi)
    return ticks_to_seconds(midi, max_end_tick, tempo_map)
