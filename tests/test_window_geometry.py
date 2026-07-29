"""Tests for frameless-window resize edge-detection math."""

from PySide6.QtCore import Qt

from utils.window_geometry import compute_resize_edges

SIZE = (400, 300)
MARGIN = 6


def test_no_edge_at_center() -> None:
    assert compute_resize_edges((200, 150), SIZE, MARGIN) == Qt.Edge(0)


def test_left_edge() -> None:
    assert compute_resize_edges((0, 150), SIZE, MARGIN) == Qt.Edge.LeftEdge


def test_right_edge() -> None:
    assert compute_resize_edges((399, 150), SIZE, MARGIN) == Qt.Edge.RightEdge


def test_top_edge() -> None:
    assert compute_resize_edges((200, 0), SIZE, MARGIN) == Qt.Edge.TopEdge


def test_bottom_edge() -> None:
    assert compute_resize_edges((200, 299), SIZE, MARGIN) == Qt.Edge.BottomEdge


def test_top_left_corner() -> None:
    assert compute_resize_edges((0, 0), SIZE, MARGIN) == Qt.Edge.LeftEdge | Qt.Edge.TopEdge


def test_top_right_corner() -> None:
    assert compute_resize_edges((399, 0), SIZE, MARGIN) == Qt.Edge.RightEdge | Qt.Edge.TopEdge


def test_bottom_left_corner() -> None:
    assert compute_resize_edges((0, 299), SIZE, MARGIN) == Qt.Edge.LeftEdge | Qt.Edge.BottomEdge


def test_bottom_right_corner() -> None:
    assert compute_resize_edges((399, 299), SIZE, MARGIN) == (
        Qt.Edge.RightEdge | Qt.Edge.BottomEdge)


def test_just_outside_margin_is_no_edge() -> None:
    assert compute_resize_edges((MARGIN + 1, 150), SIZE, MARGIN) == Qt.Edge(0)
