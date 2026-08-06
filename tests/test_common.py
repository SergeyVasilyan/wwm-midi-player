"""Tests for shared resource-path resolution."""

from pathlib import Path

import pytest

from utils.common import CHANNEL_COLORS, channel_color_hex, note_color_hex, resource_path


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_returns_original_path_when_it_exists() -> None:
    Path("logo.ico").touch()
    assert resource_path("logo.ico") == Path("logo.ico")


def test_returns_original_path_when_missing_and_no_internal_dir() -> None:
    assert resource_path("missing.ico") == Path("missing.ico")


def test_returns_internal_prefixed_path_when_missing_and_internal_dir_exists() -> None:
    Path("_internal").mkdir()
    assert resource_path("missing.ico") == Path("_internal/missing.ico")


def test_prefers_direct_path_over_internal_when_both_could_apply() -> None:
    Path("_internal").mkdir()
    Path("present.ico").touch()
    assert resource_path("present.ico") == Path("present.ico")


def test_channel_color_hex_returns_distinct_color_for_drum_channel() -> None:
    drum_channel = 9
    assert channel_color_hex(drum_channel) not in (
        channel_color_hex(channel) for channel in range(16) if channel != drum_channel
    )


def test_channel_color_hex_wraps_out_of_range_channel() -> None:
    assert channel_color_hex(16) == channel_color_hex(0)


def test_channel_color_hex_covers_all_16_channels() -> None:
    assert len(CHANNEL_COLORS) == 16
    assert all(color.startswith("#") for color in CHANNEL_COLORS)


def test_note_color_hex_differs_across_tracks_sharing_a_channel() -> None:
    # This is the scenario that used to collapse every instrument into one
    # color: multiple tracks all routed through channel 0.
    assert note_color_hex(0, is_drum=False) != note_color_hex(1, is_drum=False)


def test_note_color_hex_drum_is_constant_regardless_of_track() -> None:
    assert note_color_hex(0, is_drum=True) == note_color_hex(5, is_drum=True)


def test_note_color_hex_drum_color_never_used_for_pitched_tracks() -> None:
    drum_color = note_color_hex(0, is_drum=True)
    assert all(note_color_hex(track, is_drum=False) != drum_color for track in range(30))
