"""Tests for track filename parsing."""

from utils.track_info import TrackInfo, parse_track_info


def test_parses_artist_and_title() -> None:
    assert parse_track_info("Hans Zimmer - Time.mid") == TrackInfo(
        artist="Hans Zimmer", title="Time",
    )


def test_strips_extension_only_once() -> None:
    assert parse_track_info("Artist - Song Pt. 2.mid") == TrackInfo(
        artist="Artist", title="Song Pt. 2",
    )


def test_falls_back_to_unknown_artist_without_separator() -> None:
    assert parse_track_info("just_a_filename.mid") == TrackInfo(
        artist="Unknown", title="just_a_filename",
    )


def test_handles_no_extension() -> None:
    assert parse_track_info("Artist - Title") == TrackInfo(
        artist="Artist", title="Title",
    )


def test_handles_empty_string() -> None:
    assert parse_track_info("") == TrackInfo(artist="Unknown", title="")
