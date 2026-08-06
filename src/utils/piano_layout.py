"""Pure 88-key piano keyboard geometry (A0=21 .. C8=108).

No Qt types here: callers convert to QRectF/QColor themselves, so this module
stays unit-testable without a QApplication.
"""

MIDI_NOTE_MIN: int = 21   # A0
MIDI_NOTE_MAX: int = 108  # C8
WHITE_KEY_COUNT: int = 52
BLACK_KEY_WIDTH_RATIO: float = 0.6

_WHITE_PITCH_CLASSES: frozenset[int] = frozenset({0, 2, 4, 5, 7, 9, 11})


def is_white_key(note: int) -> bool:
    """Return whether note's pitch class is a white key."""
    return note % 12 in _WHITE_PITCH_CLASSES


def clamp_note(note: int) -> int:
    """Clamp a MIDI note number into the 88-key range [21, 108]."""
    return max(MIDI_NOTE_MIN, min(MIDI_NOTE_MAX, note))


def white_key_index(note: int) -> int:
    """Return the 0-based left-to-right index of note among the 52 white keys.

    For a black note, returns the index of the white key immediately below it
    (used as the basis for centering the black key between its neighbors).
    """
    white_count: int = 0
    for candidate in range(MIDI_NOTE_MIN, note):
        if is_white_key(candidate):
            white_count += 1
    return white_count


def key_width(note: int, keyboard_width: float) -> float:
    """Return the on-screen width of note's key, scaled to keyboard_width."""
    white_width: float = keyboard_width / WHITE_KEY_COUNT
    if is_white_key(note):
        return white_width
    return white_width * BLACK_KEY_WIDTH_RATIO


def key_x_position(note: int, keyboard_width: float) -> float:
    """Return the left x-coordinate of note's key body, scaled to keyboard_width."""
    white_width: float = keyboard_width / WHITE_KEY_COUNT
    if is_white_key(note):
        return white_key_index(note) * white_width
    black_width: float = white_width * BLACK_KEY_WIDTH_RATIO
    # white_key_index(note) for a black note counts the white keys strictly
    # below it, which is exactly the boundary (in white-key units) between
    # the preceding white key and the next one.
    boundary: float = white_key_index(note) * white_width
    return boundary - black_width / 2


def note_to_x_center(note: int, keyboard_width: float) -> float:
    """Return the horizontal center x for note, used to position falling bars."""
    return key_x_position(note, keyboard_width) + key_width(note, keyboard_width) / 2
