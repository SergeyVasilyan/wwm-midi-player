"""Precompute the full list of note on/off events for the visualizer.

Runs ahead of/alongside real-time playback rather than during it, so the UI
can draw falling notes before they're actually triggered.
"""

from dataclasses import dataclass

import mido

from utils.midi_timing import TickClock, build_tempo_map

DRUM_CHANNEL: int = 9  # GM channel 10 (0-indexed) is reserved for percussion.


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """A single sounded note: channel, pitch, absolute on/off time, program, track.

    Attributes:
        channel: MIDI channel (0-15) the note was sent on.
        note: MIDI note number.
        velocity: Note-on velocity (1-127).
        start: Absolute start time in seconds from the start of the track.
        end: Absolute end time in seconds; equals start for a zero-length note.
        program: The channel's active program (instrument) at note-on time.
        is_drum: Whether the note is on the GM percussion channel.
        track: Index into midi.tracks this note originated from.
    """

    channel: int
    note: int
    velocity: int
    start: float
    end: float
    program: int
    is_drum: bool
    track: int


@dataclass(frozen=True, slots=True)
class TrackSummary:
    """A track eligible for the mute UI: its midi.tracks index, display name, and swatch flavor.

    Attributes:
        index: Index into midi.tracks.
        name: Display name for the track (from its track_name meta message,
            or a "Track N" fallback).
        is_drum: Whether the track emitted at least one drum-channel note.
    """

    index: int
    name: str
    is_drum: bool


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

    Args:
        midi: The parsed MIDI file to precompute note events for.

    Returns:
        Every note event in the file, sorted by start time.
    """
    tempo_map: list[tuple[int, int]] = build_tempo_map(midi)
    open_notes: dict[tuple[int, int, int], tuple[float, int, int]] = {}
    programs: dict[int, int] = {}
    events: list[NoteEvent] = []
    for track_index, track in enumerate(midi.tracks):
        abs_ticks: int = 0
        clock: TickClock = TickClock(tempo_map, midi.ticks_per_beat)
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


def extract_track_names(midi: mido.MidiFile) -> list[str]:
    """Return one display name per midi.tracks entry.

    Reads each track's first MetaMessage("track_name"); a track with none
    (or a blank/whitespace-only one) falls back to "Track {index + 1}"
    (1-based, matching how DAWs number tracks for end users).

    Args:
        midi: The parsed MIDI file to read track names from.

    Returns:
        One display name per midi.tracks entry, in the same order.
    """
    names: list[str] = []
    for index, track in enumerate(midi.tracks):
        name: str = ""
        for msg in track:
            if msg.type == "track_name":
                name = msg.name.strip()
                break
        names.append(name or f"Track {index + 1}")
    return names


def summarize_tracks(midi: mido.MidiFile, events: list[NoteEvent]) -> list[TrackSummary]:
    """Return one TrackSummary per track that actually produced a note event.

    Pure meta/conductor tracks (e.g. a tempo-only track 0 in most format-1
    files) are skipped since they have nothing to mute. Order is ascending
    midi.tracks index, not first-note order, so the mute panel is stable
    across reloads. is_drum reflects whether the track emitted at least one
    drum-channel note, used only for the panel's swatch color - the falling
    notes themselves are still colored per-event via NoteEvent.is_drum,
    unaffected by this simplification.

    Args:
        midi: The parsed MIDI file (used to read track names).
        events: Note events already precomputed via build_note_events().

    Returns:
        One TrackSummary per track that produced at least one note event,
        in ascending track-index order.
    """
    names: list[str] = extract_track_names(midi)
    used_tracks: set[int] = {event.track for event in events}
    drum_tracks: set[int] = {event.track for event in events if event.is_drum}
    return [TrackSummary(index, names[index], index in drum_tracks)
            for index in sorted(used_tracks)]
