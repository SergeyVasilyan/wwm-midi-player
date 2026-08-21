"""Tests for pure MIDI timing calculations."""

import mido
import pytest

from utils.midi_timing import (
    TickClock,
    build_tempo_map,
    calculate_duration,
    find_max_end_tick,
    ticks_to_seconds,
)


def _track(*messages: mido.Message) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.extend(messages)
    return track


def test_build_tempo_map_defaults_to_120bpm_when_no_tempo_messages() -> None:
    midi = mido.MidiFile()
    midi.tracks.append(_track(mido.Message("note_on", note=60, velocity=64, time=0)))
    assert build_tempo_map(midi) == [(0, 500_000)]


def test_build_tempo_map_collects_tempo_changes_across_tracks() -> None:
    midi = mido.MidiFile()
    midi.tracks.append(_track(mido.MetaMessage("set_tempo", tempo=300_000, time=480)))
    midi.tracks.append(_track(mido.MetaMessage("set_tempo", tempo=250_000, time=960)))
    assert build_tempo_map(midi) == [(0, 500_000), (480, 300_000), (960, 250_000)]


def test_build_tempo_map_collapses_duplicate_ticks() -> None:
    midi = mido.MidiFile()
    midi.tracks.append(_track(mido.MetaMessage("set_tempo", tempo=300_000, time=480)))
    midi.tracks.append(_track(mido.MetaMessage("set_tempo", tempo=250_000, time=480)))
    tempo_map = build_tempo_map(midi)
    assert tempo_map == [(0, 500_000), (480, 250_000)]


def test_find_max_end_tick_ignores_tracks_without_notes() -> None:
    midi = mido.MidiFile()
    midi.tracks.append(_track(mido.MetaMessage("set_tempo", tempo=300_000, time=10_000)))
    midi.tracks.append(
        _track(
            mido.Message("note_on", note=60, velocity=64, time=0),
            mido.Message("note_off", note=60, velocity=0, time=480),
        ),
    )
    assert find_max_end_tick(midi) == 480


def test_find_max_end_tick_takes_the_longest_track() -> None:
    midi = mido.MidiFile()
    midi.tracks.append(
        _track(
            mido.Message("note_on", note=60, velocity=64, time=0),
            mido.Message("note_off", note=60, velocity=0, time=240),
        ),
    )
    midi.tracks.append(
        _track(
            mido.Message("note_on", note=64, velocity=64, time=0),
            mido.Message("note_off", note=64, velocity=0, time=960),
        ),
    )
    assert find_max_end_tick(midi) == 960


def test_ticks_to_seconds_constant_tempo() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    tempo_map = [(0, 500_000)]
    assert ticks_to_seconds(midi, 480, tempo_map) == pytest.approx(0.5)


def test_ticks_to_seconds_across_tempo_change() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    tempo_map = [(0, 500_000), (240, 250_000)]
    # First 240 ticks at 120bpm (0.25s) + remaining 240 ticks at 240bpm (0.125s).
    assert ticks_to_seconds(midi, 480, tempo_map) == pytest.approx(0.375)


def test_calculate_duration_end_to_end() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(mido.MetaMessage("set_tempo", tempo=500_000, time=0)))
    midi.tracks.append(
        _track(
            mido.Message("note_on", note=60, velocity=64, time=0),
            mido.Message("note_off", note=60, velocity=0, time=480),
        ),
    )
    assert calculate_duration(midi) == pytest.approx(0.5)


def test_tick_clock_constant_tempo() -> None:
    clock = TickClock([(0, 500_000)], ticks_per_beat=480)
    assert clock.seconds_at(480) == pytest.approx(0.5)
    assert clock.seconds_at(960) == pytest.approx(1.0)


def test_tick_clock_across_tempo_change() -> None:
    clock = TickClock([(0, 500_000), (240, 250_000)], ticks_per_beat=480)
    # First 240 ticks at 120bpm (0.25s) + remaining 240 ticks at 240bpm (0.125s).
    assert clock.seconds_at(480) == pytest.approx(0.375)


def test_tick_clock_matches_ticks_to_seconds_incrementally() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    tempo_map = [(0, 500_000), (240, 250_000), (720, 1_000_000)]
    clock = TickClock(tempo_map, ticks_per_beat=480)
    for tick in (100, 240, 480, 720, 960):
        assert clock.seconds_at(tick) == pytest.approx(ticks_to_seconds(midi, tick, tempo_map))
