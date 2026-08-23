"""Pure window edge-detection math for frameless-window resize hit-testing."""

from PySide6.QtCore import Qt


def compute_resize_edges(pos: tuple[int, int], size: tuple[int, int],
                          margin: int) -> Qt.Edge:
    """Return which window edges pos is within margin px of.

    Used to decide whether a mouse press near the border of a frameless
    window should start an OS-native resize, and which edge(s) to resize.

    Args:
        pos: The (x, y) position to test, in window-local coordinates.
        size: The window's current (width, height).
        margin: How many pixels from an edge still counts as "on" that edge.

    Returns:
        The edge(s) pos is within margin of, combined with bitwise OR, or
        Qt.Edge(0) if pos isn't near any edge.
    """
    x, y = pos
    width, height = size
    edges: Qt.Edge = Qt.Edge(0)
    if x <= margin:
        edges |= Qt.Edge.LeftEdge
    elif x >= width - margin:
        edges |= Qt.Edge.RightEdge
    if y <= margin:
        edges |= Qt.Edge.TopEdge
    elif y >= height - margin:
        edges |= Qt.Edge.BottomEdge
    return edges
