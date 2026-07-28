"""Pure playlist navigation logic (shuffle/repeat index resolution)."""

import random


def next_track_index(current_index: int, count: int, *, shuffle: bool, repeat: bool) -> int | None:
    """Return the next playlist index to play, or None if playback should stop.

    Args:
        current_index: Index of the currently playing track.
        count: Total number of tracks in the playlist.
        shuffle: Pick a random track other than the current one.
        repeat: Wrap around to the start (or replay a single track) at the end.

    Returns:
        The next index to play, or None when there is nothing left to play.
    """
    if not count:
        return None
    if shuffle:
        if count == 1:
            return 0 if repeat else None
        candidates: list[int] = [i for i in range(count) if i != current_index]
        return random.choice(candidates)
    if current_index < count - 1:
        return current_index + 1
    return 0 if repeat else None
