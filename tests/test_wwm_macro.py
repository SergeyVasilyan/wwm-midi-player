"""Tests for the pure note-folding and octave-shift logic in utils.wwm_macro."""

from utils.wwm_macro import best_octave_shift, count_fold_collisions, fold_note


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


def test_count_fold_collisions_ignores_genuine_unison() -> None:
    assert count_fold_collisions([[60, 60]], shift=0) == 0


def test_count_fold_collisions_detects_distinct_notes_on_same_key() -> None:
    # 30 and 6 are both pitch class 6, both below range: both fold to 54.
    assert count_fold_collisions([[30, 6]], shift=0) == 1


def test_count_fold_collisions_ignores_single_note_chords() -> None:
    assert count_fold_collisions([[60]], shift=0) == 0


def test_best_octave_shift_prefers_zero_when_already_optimal() -> None:
    assert best_octave_shift([[60, 64, 67]]) == 0


def test_best_octave_shift_reduces_collisions_when_possible() -> None:
    # Two out-of-range notes an octave apart collide at shift 0 (both fold to
    # the same low-register key); shifting the whole chord up an octave moves
    # them both into the native range as two distinct notes.
    chords = [[24, 36]]
    shift = best_octave_shift(chords)
    assert count_fold_collisions(chords, shift) < count_fold_collisions(chords, 0)


def test_best_octave_shift_never_makes_collisions_worse() -> None:
    chords = [[60, 64, 67], [30, 6], [48, 96]]
    baseline = count_fold_collisions(chords, 0)
    shift = best_octave_shift(chords)
    assert count_fold_collisions(chords, shift) <= baseline
