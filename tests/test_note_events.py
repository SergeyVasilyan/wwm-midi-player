"""Tests for pure MIDI note-event precomputation."""

import time

import mido
import pytest

from utils.note_events import DRUM_CHANNEL, build_note_events


def _track(*messages: mido.Message) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.extend(messages)
    return track


def test_simple_note_on_off_pair() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),
    ))
    events = build_note_events(midi)
    assert len(events) == 1
    event = events[0]
    assert event.channel == 0
    assert event.note == 60
    assert event.velocity == 100
    assert event.start == pytest.approx(0.0)
    assert event.end == pytest.approx(0.5)
    assert not event.is_drum


def test_overlapping_chord() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_on", channel=0, note=64, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),
        mido.Message("note_off", channel=0, note=64, velocity=0, time=0),
    ))
    events = build_note_events(midi)
    assert {event.note for event in events} == {60, 64}
    for event in events:
        assert event.start == pytest.approx(0.0)


def test_unterminated_note_closes_at_its_own_start() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=480),
    ))
    events = build_note_events(midi)
    assert len(events) == 1
    assert events[0].start == pytest.approx(events[0].end)


def test_program_change_before_note_on_is_recorded() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("program_change", channel=0, program=40, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),
    ))
    events = build_note_events(midi)
    assert events[0].program == 40


def test_drum_channel_is_flagged() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=DRUM_CHANNEL, note=36, velocity=100, time=0),
        mido.Message("note_off", channel=DRUM_CHANNEL, note=36, velocity=0, time=240),
    ))
    events = build_note_events(midi)
    assert events[0].is_drum


def test_events_sorted_by_start_time() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=240),
        mido.Message("note_on", channel=0, note=64, velocity=100, time=240),
        mido.Message("note_off", channel=0, note=64, velocity=0, time=240),
    ))
    events = build_note_events(midi)
    assert [event.note for event in events] == [60, 64]


def test_events_tagged_with_originating_track_index() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),
    ))
    midi.tracks.append(_track(
        mido.Message("note_on", channel=0, note=67, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=67, velocity=0, time=480),
    ))
    events = build_note_events(midi)
    tracks_by_note = {event.note: event.track for event in events}
    assert tracks_by_note[60] == 0
    assert tracks_by_note[67] == 1


def test_same_channel_across_tracks_paired_independently() -> None:
    # Two tracks both use channel 0 with an overlapping note - a naive
    # (channel, note) pairing key would let one track's note_off close the
    # other track's still-sounding note_on.
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=960),
    ))
    midi.tracks.append(_track(
        mido.Message("note_on", channel=0, note=60, velocity=80, time=240),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=240),
    ))
    events = build_note_events(midi)
    assert len(events) == 2
    long_note = next(event for event in events if event.velocity == 100)
    short_note = next(event for event in events if event.velocity == 80)
    assert long_note.end == pytest.approx(1.0)
    assert short_note.start == pytest.approx(0.25)
    assert short_note.end == pytest.approx(0.5)


def test_note_times_correct_across_a_tempo_change() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),  # 120bpm
        mido.Message("note_on", channel=0, note=60, velocity=100, time=480),  # at 1 beat (0.5s)
        mido.MetaMessage("set_tempo", tempo=250_000, time=0),  # 240bpm, same tick
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),  # +1 beat at 240bpm
    ))
    events = build_note_events(midi)
    assert len(events) == 1
    assert events[0].start == pytest.approx(0.5)
    assert events[0].end == pytest.approx(0.75)


def test_many_tempo_changes_stay_fast() -> None:
    # Regression guard: build_note_events used to call ticks_to_seconds()
    # (an O(tempo changes) full re-walk) once per note on/off, making this
    # O(events * tempo changes) and slow enough on tempo-heavy files to
    # block the GUI thread when switching tracks. The incremental _TickClock
    # should keep this roughly linear regardless of tempo change count.
    midi = mido.MidiFile(ticks_per_beat=480)
    messages = []
    for i in range(2000):
        messages.append(mido.MetaMessage("set_tempo", tempo=500_000 + i, time=1))
        messages.append(mido.Message("note_on", channel=0, note=60, velocity=100, time=0))
        messages.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=1))
    midi.tracks.append(_track(*messages))
    start = time.perf_counter()
    events = build_note_events(midi)
    elapsed = time.perf_counter() - start
    assert len(events) == 2000
    assert elapsed < 1.0
