"""Viewer widget."""


from PySide6.QtWidgets import QFrame, QListWidget, QVBoxLayout, QWidget

from utils.common import Colors


class Viewer(QFrame):
    """Viewer widget.."""

    def __init__(self, accent: Colors=Colors.ACCENT_1, parent: QWidget|None=None) -> None:
        """Initialize Viewer."""
        super().__init__(parent=parent)
        self.__widget: QListWidget = QListWidget(self)
        self.__radius: int = 10
        self.__accent: Colors = accent
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__widget)
        self.set_style()

    @property
    def widget(self) -> QListWidget:
        """Return widget."""
        return self.__widget

    def set_style(self) -> None:
        """Override size hint."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                border-radius: {self.__radius}px;
                border: 1px solid {Colors.BACKGROUND.value.hex};
            }}
        """)
        self.__widget.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                font-size: 14px;
                outline: 0;
            }}
            QListWidget::item {{
                background-color: transparent;
                border-bottom: 1px solid {Colors.BACKGROUND_2.value.hex};
                border-radius: {self.__radius}px;
                padding: 6px;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
                border-left: 3px solid {self.__accent.value.hex};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.BACKGROUND_2.value.hex};
                border-radius: {self.__radius}px;
            }}
        """)

if __name__ == "__main__":
    ...
