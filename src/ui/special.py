"""Special dialog."""

from random import choice

from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QWidget,
)

from ui.dialog_style import apply_dialog_theme


class SpecialDialog(QDialog):
    """Special Dialog."""

    def __init__(self, parent: QWidget|None=None) -> None:
        """INIT."""
        super().__init__(parent)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setWindowTitle("Special")
        self.setModal(True)
        apply_dialog_theme(self)
        self.__create_layout()

    def __create_layout(self) -> None:
        """Create Dialog layout."""
        layout: QGridLayout = QGridLayout()
        row: int = 0
        header: QLabel = QLabel("Special thanks to")
        header.setStyleSheet(
            "font-size: 14pt; font-weight: bold; padding-bottom: 8px; background: transparent;")
        layout.addWidget(header, row, 0, 1, -1, alignment=Qt.AlignmentFlag.AlignCenter)
        row += 1
        hearts: list[str] = ["💚", "🧡", "❤️", "🩷", "💛", "💙", "🩵", "💜", "🤎", "🖤", "🩶",
                             "🤍"]
        for contributor in ["Ash (friend and comrade of mine)"]:
            layout.addWidget(QLabel(choice(hearts)), row, 0, 1, 1,
                             alignment=Qt.AlignmentFlag.AlignRight)
            layout.addWidget(QLabel(contributor), row, 1, 1, 1,
                             alignment=Qt.AlignmentFlag.AlignLeft)
            row += 1
        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

if __name__ == "__main__":
    ...
