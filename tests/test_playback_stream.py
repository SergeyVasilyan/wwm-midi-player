"""Tests for the track-tagged, time-sorted live-playback message stream."""

import mido
import pytest

from utils.playback_stream import build_playback_messages


def _track(*messages: mido.Message) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.extend(messages)
    return track


def test_messages_tagged_with_originating_track() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
    ))
    midi.tracks.append(_track(
        mido.Message("note_on", channel=0, note=67, velocity=100, time=0),
    ))
    messages = build_playback_messages(midi)
    tracks_by_note = {pm.message.note: pm.track for pm in messages if pm.message.type == "note_on"}
    assert tracks_by_note[60] == 0
    assert tracks_by_note[67] == 1


def test_globally_sorted_by_time() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=480),
    ))
    midi.tracks.append(_track(
        mido.Message("note_on", channel=0, note=67, velocity=100, time=0),
    ))
    messages = build_playback_messages(midi)
    times = [pm.time for pm in messages]
    assert times == sorted(times)
    assert messages[0].message.note == 67
    assert messages[1].message.note == 60


def test_unhandled_message_types_filtered_out() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("pitchwheel", channel=0, pitch=100, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
    ))
    messages = build_playback_messages(midi)
    assert [pm.message.type for pm in messages] == ["note_on"]


def test_handled_types_all_pass_through() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("program_change", channel=0, program=5, time=0),
        mido.Message("control_change", channel=0, control=7, value=100, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),
    ))
    messages = build_playback_messages(midi)
    assert [pm.message.type for pm in messages] == [
        "program_change", "control_change", "note_on", "note_off",
    ]


def test_same_tick_order_preserved_within_a_track() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.Message("program_change", channel=0, program=5, time=0),
        mido.Message("note_on", channel=0, note=60, velocity=100, time=0),
    ))
    messages = build_playback_messages(midi)
    assert [pm.message.type for pm in messages] == ["program_change", "note_on"]


def test_time_correct_across_a_tempo_change() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    midi.tracks.append(_track(
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),  # 120bpm
        mido.Message("note_on", channel=0, note=60, velocity=100, time=480),  # at 1 beat (0.5s)
        mido.MetaMessage("set_tempo", tempo=250_000, time=0),  # 240bpm, same tick
        mido.Message("note_off", channel=0, note=60, velocity=0, time=480),  # +1 beat at 240bpm
    ))
    messages = build_playback_messages(midi)
    assert messages[0].time == pytest.approx(0.5)
    assert messages[1].time == pytest.approx(0.75)
