"""Viewer widget."""


from PySide6.QtWidgets import QFrame, QListWidget, QVBoxLayout, QWidget

from ui.song_delegate import SongDelegate
from utils.common import RADIUS_MD, Colors


class Viewer(QFrame):
    """Viewer widget.."""

    def __init__(self, accent: Colors=Colors.ACCENT_1, parent: QWidget|None=None) -> None:
        """Initialize Viewer.

        Args:
            accent: The accent color used for the now-playing glyph and
                selection bar.
            parent: Optional parent widget.
        """
        super().__init__(parent=parent)
        self.__widget: QListWidget = QListWidget(self)
        self.__delegate: SongDelegate = SongDelegate(self.__widget, accent, self.__widget)
        self.__widget.setItemDelegate(self.__delegate)
        self.__radius: int = RADIUS_MD
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__widget)
        self.set_style()

    @property
    def widget(self) -> QListWidget:
        """Return widget.

        Returns:
            The underlying list widget.
        """
        return self.__widget

    def set_now_playing_row(self, row: int) -> None:
        """Mark row as the now-playing track (or -1 for none).

        Args:
            row: The now-playing row index, or -1 if nothing is playing.
        """
        self.__delegate.set_now_playing_row(row)

    def set_style(self) -> None:
        """Apply the panel background and border."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                border-radius: {self.__radius}px;
                border: 1px solid {Colors.BACKGROUND.value.hex};
            }}
        """)
        self.__widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: 0;
            }
        """)

if __name__ == "__main__":
    ...
