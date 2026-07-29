"""Pure filename parsing for the "now playing" display."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrackInfo:
    """Artist/title parsed from a track filename."""

    artist: str
    title: str


def parse_track_info(filename: str) -> TrackInfo:
    """Parse an "Artist - Title.ext" filename into a TrackInfo.

    Falls back to artist "Unknown" and the full stem as title when the
    filename doesn't contain a " - " separator.
    """
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
        return TrackInfo(artist=artist.strip(), title=title.strip())
    return TrackInfo(artist="Unknown", title=stem.strip())
