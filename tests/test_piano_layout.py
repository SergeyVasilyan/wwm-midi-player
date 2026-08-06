"""Tests for pure piano keyboard geometry."""

import pytest

from utils.piano_layout import (
    MIDI_NOTE_MAX,
    MIDI_NOTE_MIN,
    WHITE_KEY_COUNT,
    clamp_note,
    is_white_key,
    key_width,
    key_x_position,
    note_to_x_center,
    white_key_index,
)


def test_full_range_has_52_white_keys() -> None:
    white_notes = [n for n in range(MIDI_NOTE_MIN, MIDI_NOTE_MAX + 1) if is_white_key(n)]
    assert len(white_notes) == WHITE_KEY_COUNT


def test_a0_is_leftmost_white_key() -> None:
    assert is_white_key(MIDI_NOTE_MIN)
    assert white_key_index(MIDI_NOTE_MIN) == 0
    assert key_x_position(MIDI_NOTE_MIN, 520) == pytest.approx(0.0)


def test_c8_is_rightmost_white_key() -> None:
    assert is_white_key(MIDI_NOTE_MAX)
    assert white_key_index(MIDI_NOTE_MAX) == WHITE_KEY_COUNT - 1
    keyboard_width = 520.0
    white_width = keyboard_width / WHITE_KEY_COUNT
    expected_x = (WHITE_KEY_COUNT - 1) * white_width
    assert key_x_position(MIDI_NOTE_MAX, keyboard_width) == pytest.approx(expected_x)


def test_black_key_sits_between_its_white_neighbors() -> None:
    # C4 and D4 are adjacent white keys (no white key between them), so C#4's
    # center should land exactly on their shared boundary: c4's right edge,
    # which is also d4's left edge.
    keyboard_width = 520.0
    c4, c_sharp4, d4 = 60, 61, 62
    assert is_white_key(c4)
    assert not is_white_key(c_sharp4)
    assert is_white_key(d4)
    c4_x = key_x_position(c4, keyboard_width)
    c4_right_edge = c4_x + key_width(c4, keyboard_width)
    d4_x = key_x_position(d4, keyboard_width)
    c_sharp4_center = note_to_x_center(c_sharp4, keyboard_width)
    assert c4_x < c_sharp4_center == pytest.approx(c4_right_edge) == pytest.approx(d4_x)


def test_black_key_narrower_than_white_key() -> None:
    keyboard_width = 520.0
    assert key_width(61, keyboard_width) < key_width(60, keyboard_width)


def test_clamp_note_boundaries() -> None:
    assert clamp_note(0) == MIDI_NOTE_MIN
    assert clamp_note(127) == MIDI_NOTE_MAX
    assert clamp_note(60) == 60


def test_key_x_position_monotonic_across_full_range() -> None:
    keyboard_width = 520.0
    positions = [
        key_x_position(n, keyboard_width) + key_width(n, keyboard_width) / 2
        for n in range(MIDI_NOTE_MIN, MIDI_NOTE_MAX + 1)
        if is_white_key(n)
    ]
    assert positions == sorted(positions)
