"""WWM Macro Module (Konghou) — programmatic mapping + calibration."""

import json
from copy import deepcopy
from enum import IntEnum
from pathlib import Path

import win32api
import win32con
from PySide6.QtCore import Slot

from utils.common import Singleton, resource_path

NOTE_MIN: int = 48
NOTE_MAX: int = 83
OCTAVE: int = 12
MAX_SHIFT_OCTAVES: int = 4


def fold_note(note: int, note_min: int = NOTE_MIN, note_max: int = NOTE_MAX) -> int:
    """Fold a MIDI note into [note_min, note_max] by shifting whole octaves.

    Notes below the range always land on the range's lowest octave and notes
    above it always land on the highest octave, so pitch class (the note
    "name") is always preserved exactly - only octave information for notes
    more than one octave outside the range can be lost.
    """
    while note < note_min:
        note += OCTAVE
    while note > note_max:
        note -= OCTAVE
    return note


def count_fold_collisions(chords: list[list[int]], shift: int,
                           note_min: int = NOTE_MIN, note_max: int = NOTE_MAX) -> int:
    """Count note instances lost when distinct simultaneous notes fold onto the same key.

    A chord is a list of MIDI note numbers sounding at the same time. Two
    different notes landing on the same folded key after shift is applied
    means one of them won't be audible as a separate key press; notes that
    were already identical (a genuine unison) don't count as a loss.
    """
    lost: int = 0
    for notes in chords:
        if len(notes) < 2:
            continue
        by_target: dict[int, set[int]] = {}
        for n in notes:
            target: int = fold_note(n + shift, note_min, note_max)
            by_target.setdefault(target, set()).add(n)
        lost += sum(len(originals) - 1 for originals in by_target.values()
                    if len(originals) > 1)
    return lost


def best_octave_shift(chords: list[list[int]], max_octaves: int = MAX_SHIFT_OCTAVES,
                       note_min: int = NOTE_MIN, note_max: int = NOTE_MAX) -> int:
    """Return the whole-octave transposition (in semitones) minimizing fold collisions.

    Searches shifts from -max_octaves to +max_octaves octaves and keeps the
    one with the fewest lost note instances; ties favor the smallest shift
    magnitude, and 0 (no transposition) wins ties against itself first.
    """
    best_shift: int = 0
    best_lost: int = count_fold_collisions(chords, 0, note_min, note_max)
    for octaves in range(1, max_octaves + 1):
        for candidate in (octaves * OCTAVE, -octaves * OCTAVE):
            lost: int = count_fold_collisions(chords, candidate, note_min, note_max)
            if lost < best_lost:
                best_shift, best_lost = candidate, lost
    return best_shift


class KeyManager(metaclass=Singleton):
    """WWM Key binding manager."""

    class _Note(IntEnum):
        """Note information enumeration."""

        MIN = NOTE_MIN
        MAX = NOTE_MAX
        OFFSET = OCTAVE
        SEMITONE_OFFSET = 0

    def __init__(self) -> None:
        """Initialize WWM Key binding manager."""
        self.__offsets: dict[str, int] = {
            "1" : 0,  "#1": 1,
            "2" : 2,
            "b3": 3,  "3" : 4,
            "4" : 5,  "#4": 6,
            "5" : 7,  "#5": 8,
            "6" : 9,
            "b7": 10, "7" : 11,
        }
        self.__default_bindings: dict[str, dict[str, str]] = {
            "high": {
                "1" : "Q",      "#1": "Shift+Q",
                "2" : "W",
                "b3": "Ctrl+E", "3" : "E",
                "4" : "R",      "#4": "Shift+R",
                "5" : "T",      "#5": "Shift+T",
                "6" : "Y",
                "b7": "Ctrl+U", "7" : "U",
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
            "low": {
                "1" : "Z",      "#1": "Shift+Z",
                "2" : "X",
                "b3": "Ctrl+C", "3" : "C",
                "4" : "V",      "#4": "Shift+V",
                "5" : "B",      "#5": "Shift+B",
                "6" : "N",
                "b7": "Ctrl+M", "7" : "M",
            },
        }
        self.__bindings: dict[str, dict[str, str]] = {}
        self.__base_notes: dict[str, int] = {
            "low": 48,   # C3
            "med": 60,   # C4
            "high": 72,  # C5
        }
        self.__mapping: dict[int, str] = {}
        self.__cache: Path = resource_path("src/input/keybindings.json")
        self.__load_keybindings()
        self.__build_map()

    @property
    def default_bindings(self) -> dict[str, dict[str, str]]:
        """Return default keybindings."""
        return self.__default_bindings

    @property
    def bindings(self) -> dict[str, dict[str, str]]:
        """Return current keybindings."""
        return self.__bindings

    @Slot(str, str, str)
    def update_keybinding(self, octave: str, note: str, new_key: str) -> None:
        """Update keybindings."""
        octave_info: dict[str, str] = self.__bindings.get(octave, {})
        if not octave_info:
            return
        if note not in octave_info:
            return
        if new_key == octave_info.get(note, ""):
            return
        octave_info[note] = new_key
        sharp_note: str = f"#{note}"
        if sharp_note in octave_info:
            octave_info[sharp_note] = f"{octave_info[sharp_note].split('+')[0]}+{new_key}"
        b_note: str = f"b{note}"
        if b_note in octave_info:
            octave_info[b_note] = f"{octave_info[b_note].split('+')[0]}+{new_key}"
        self.__build_map()
        self.__save_keybindings()

    @Slot()
    def reset_keybindings(self) -> None:
        """Reset keybindings."""
        self.__bindings = deepcopy(self.__default_bindings)
        self.__build_map()
        self.__save_keybindings()

    def __load_keybindings(self) -> None:
        """Load save keybindings."""
        if not self.__cache.exists():
            self.__bindings = deepcopy(self.__default_bindings)
            return
        with self.__cache.open() as f:
            self.__bindings = json.load(f)

    def __save_keybindings(self) -> None:
        """Save current keybinding."""
        with self.__cache.open("w") as f:
            json.dump(self.__bindings, f, indent=4)

    def __build_map(self) -> None:
        """Construct NOTE_TO_WWM_KEY from BASE_NOTES, DEGREE_OFFSETS, and REGISTER_KEYS."""
        for note_type, note in self.__base_notes.items():
            base: int = note + self._Note.SEMITONE_OFFSET
            for degree, key in self.__bindings[note_type].items():
                note: int = base + self.__offsets[degree]
                if self._Note.MIN <= note <= self._Note.MAX:
                    self.__mapping[note] = key

    def __get_note(self, note: int) -> str|None:
        """Fold note into [48, 83] by octaves to reach playable range."""
        return self.__mapping.get(fold_note(note, self._Note.MIN, self._Note.MAX), None)

    def __make_lparam(self, key: int, is_down: bool=False) -> int:
        """Construct the complex lParam integer that Windows expects.

        This mimics the hardware details of a keypress.
        """
        scan_code: int = win32api.MapVirtualKey(key, 0)
        lparam: int = 1
        lparam |= (scan_code << 16)
        if not is_down:
            lparam |= (1 << 30)
            lparam |= (1 << 31)
        return lparam

    def __post_key_event(self, handle: int, vk_code: int) -> None:
        """Send a complete Press & Release cycle."""
        lparam_down: int = self.__make_lparam(vk_code, True)
        lparam_up: int = self.__make_lparam(vk_code, False)
        win32api.PostMessage(handle, win32con.WM_KEYDOWN, vk_code, lparam_down)
        win32api.PostMessage(handle, win32con.WM_KEYUP, vk_code, lparam_up)

    def __send_keypress_to_window(self, handle: int, key_string: str) -> None:
        """Send keypress to a specified window."""
        parts: list[str] = key_string.split("+")
        modifier_vk: int|None = None
        main_char: str = parts[-1]
        if "Shift" in parts:
            modifier_vk = win32con.VK_SHIFT
        elif "Ctrl" in parts:
            modifier_vk = win32con.VK_CONTROL
        main_vk: int = win32api.VkKeyScan(main_char) & 0xFF
        if modifier_vk:
            lp_mod: int = self.__make_lparam(modifier_vk, True)
            win32api.PostMessage(handle, win32con.WM_KEYDOWN, modifier_vk, lp_mod)
        self.__post_key_event(handle, main_vk)
        if modifier_vk:
            lp_mod_up: int = self.__make_lparam(modifier_vk, False)
            win32api.PostMessage(handle, win32con.WM_KEYUP, modifier_vk, lp_mod_up)

    def play_note(self, handle: int, note: int) -> None:
        """Play note."""
        if key := self.__get_note(note):
            self.__send_keypress_to_window(handle, key)

    def play_chord(self, handle: int, notes: list[int]) -> None:
        """Play chord."""
        for n in notes:
            self.play_note(handle, n)
