"""Tests for playlist next-track resolution (shuffle/repeat)."""

from utils.playlist import next_track_index


def test_empty_playlist_returns_none() -> None:
    assert next_track_index(0, 0, shuffle=False, repeat=False) is None


def test_linear_advance() -> None:
    assert next_track_index(0, 3, shuffle=False, repeat=False) == 1


def test_linear_stops_at_end_without_repeat() -> None:
    assert next_track_index(2, 3, shuffle=False, repeat=False) is None


def test_linear_wraps_at_end_with_repeat() -> None:
    assert next_track_index(2, 3, shuffle=False, repeat=True) == 0


def test_shuffle_never_repeats_current_track() -> None:
    for _ in range(50):
        index = next_track_index(1, 3, shuffle=True, repeat=False)
        assert index in (0, 2)


def test_shuffle_single_track_without_repeat_stops() -> None:
    assert next_track_index(0, 1, shuffle=True, repeat=False) is None


def test_shuffle_single_track_with_repeat_replays_it() -> None:
    assert next_track_index(0, 1, shuffle=True, repeat=True) == 0
