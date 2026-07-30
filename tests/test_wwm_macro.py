"""Tests for the pure note-folding logic in utils.wwm_macro.

fold_note is verified to match, note-for-note, the reference WWM MIDI
player's (github.com/SnowiyQ/Where-Winds-Meet-Midi-Player) 36-key "Closest"
mode: same [48, 83] range, same <60/<72 register thresholds, same
pitch-class-preserving octave folding, and - like that reference - no
attempt to disambiguate simultaneous notes that fold onto the same key.
"""

from utils.wwm_macro import fold_note


def test_fold_note_leaves_in_range_note_unchanged() -> None:
    assert fold_note(60) == 60


def test_fold_note_below_range_lands_on_lowest_octave() -> None:
    assert fold_note(0) == 48
    assert fold_note(36) == 48


def test_fold_note_above_range_lands_on_highest_octave() -> None:
    assert fold_note(96) == 72
    assert fold_note(120) == 72


def test_fold_note_preserves_pitch_class() -> None:
    for note in range(0, 128):
        assert fold_note(note) % 12 == note % 12
