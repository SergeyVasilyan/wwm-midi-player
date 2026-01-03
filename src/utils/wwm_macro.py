"""WWM Macro Module (Konghou) — programmatic mapping + calibration."""

from enum import IntEnum

import keyboard

DEGREE_OFFSETS: dict[str, int] = {
    "1" : 0,  "#1": 1,
    "2" : 2,
    "b3": 3,  "3" : 4,
    "4" : 5,  "#4": 6,
    "5" : 7,  "#5": 8,
    "6" : 9,
    "b7": 10, "7" : 11,
}
REGISTER_KEYS: dict[str, dict[str, str]] = {
    "low": {
        "1" : "Z",      "#1": "Shift+Z",
        "2" : "X",
        "b3": "Ctrl+C", "3" : "C",
        "4" : "V",      "#4": "Shift+V",
        "5" : "B",      "#5": "Shift+B",
        "6" : "N",
        "b7": "Ctrl+M", "7" : "M",
    },
    "med": {
        "1" : "A",      "#1": "Shift+A",
        "2" : "S",
        "b3": "Ctrl+D", "3" : "D",
        "4" : "F",      "#4": "Shift+F",
        "5" : "G",      "#5": "Shift+G",
        "6" : "H",
        "b7": "Ctrl+J", "7" : "J",
    },
    "high": {
        "1" : "Q",      "#1" : "Shift+Q",
        "2" : "W",
        "b3": "Ctrl+E", "3" : "E",
        "4" : "R",      "#4": "Shift+R",
        "5" : "T",      "#5": "Shift+T",
        "6" : "Y",
        "b7": "Ctrl+U", "7" : "U",
    },
}
BASE_NOTES: dict[str, int] = {
    "low": 48,   # C3
    "med": 60,   # C4
    "high": 72,  # C5
}

class Note(IntEnum):
    """Note information enumeration."""

    MIN = 48
    MAX = 83
    OFFSET = 12
    SEMITONE_OFFSET = 0

def __build_map() -> dict[int, str]:
    """Construct NOTE_TO_WWM_KEY from BASE_NOTES, DEGREE_OFFSETS, and REGISTER_KEYS."""
    mapping: dict[int, str] = {}
    for note_type, note in BASE_NOTES.items():
        base: int = note + Note.SEMITONE_OFFSET
        for degree, key in REGISTER_KEYS[note_type].items():
            note: int = base + DEGREE_OFFSETS[degree]
            if Note.MIN <= note <= Note.MAX:
                mapping[note] = key
    return mapping

NOTE_TO_WWM_KEY: dict[int, str] = __build_map()

def __transpose_into_range(note: int) -> int:
    """Fold note into [48, 83] by octaves to reach playable range."""
    while note < Note.MIN:
        note += Note.OFFSET
    while note > Note.MAX:
        note -= Note.OFFSET
    return note

def play_note(note: int) -> None:
    """Play note."""
    if key := NOTE_TO_WWM_KEY.get(__transpose_into_range(note)):
        keyboard.send(key.lower())

def play_chord(notes: list[int]) -> None:
    """Play chord."""
    for n in notes:
        play_note(n)
