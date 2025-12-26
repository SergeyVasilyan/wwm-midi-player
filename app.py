"""Simple PySide6 MIDI player."""

import os
import sys
import time
from collections.abc import Callable
from typing import Any, override

import fluidsynth
import mido
from PySide6.QtCore import QRect, QSize, QThread, Signal, Slot
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class Worker(QThread):
    """MIDI player worker."""

    progress: Signal = Signal(int)

    def __init__(self, filename: str, soundfont: str) -> None:
        """Initialize worker."""
        super().__init__()
        self.__filename: str = filename
        self.__soundfont: str = soundfont
        self.__running: bool = True
        self.__paused: bool = False
        self.__volume: int = 100

    @property
    def paused(self) -> bool:
        """Return pause state."""
        return self.__paused

    @override
    def run(self) -> None:
        """Worker body."""
        synth: fluidsynth.Synth = fluidsynth.Synth()
        synth.start(driver="dsound")
        soundfont_id: Any = synth.sfload(self.__soundfont)
        synth.program_select(0, soundfont_id, 0, 0)
        player: mido.MidiFile = mido.MidiFile(self.__filename)
        total: int = sum(len(track) for track in player.tracks)
        count: int = 0
        for msg in player.play():
            if not self.__running:
                break
            while self.__paused and self.__running:
                time.sleep(0.05)
            synth.cc(0, 7, self.__volume)
            if not msg.is_meta:
                msg_type: str = msg.type
                if "note_on" == msg_type:
                    synth.noteon(msg.channel, msg.note, msg.velocity)
                elif "note_off" == msg_type:
                    synth.noteoff(msg.channel, msg.note)
                elif "program_change" == msg_type:
                    synth.program_select(msg.channel, soundfont_id, 0, msg.program)
            count += 1
            self.progress.emit(int((count / total) * 100))
        synth.delete()

    def stop(self) -> None:
        """Stop worker."""
        self.__running = False

    def toggle_pause(self) -> None:
        """Pause worker."""
        self.__paused = not self.__paused

    def set_volume(self, volume: int) -> None:
        """Set synth volume."""
        self.__volume = volume

class Player(QMainWindow):
    """MIDI Player."""

    def __init__(self) -> None:
        """Initialize MIDI Player."""
        super().__init__()
        self.setWindowTitle("Windows MIDI Player (FluidSynth)")
        screen_size: QRect = QGuiApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(QSize(screen_size.width() // 2, screen_size.height() // 2))
        self.__files: list[str] = []
        self.__current_index: int = -1
        self.__thread: Worker|None = None
        self.__soundfont: str = "GeneralUser.sf2"
        self.__current: QLabel = QLabel("No files loaded")
        self.__playlist: QListWidget = QListWidget()
        self.__playlist.setStyleSheet("""
            QListWidget {
                background-color: #1A1A1A;
                color: #E0E0E0;
                border: 1px solid #8D6E63;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #2E7D32;
                color: #FFFFFF;
            }
        """)
        self.__playlist.itemDoubleClicked.connect(self.__playlist_on_double_click)
        self.__play: QPushButton
        self.__progressbar: QProgressBar
        self.__construct_layout()
        self.__bind_shortcuts()

    def __bind_shortcuts(self) -> None:
        """Bind shortcuts."""
        QShortcut(QKeySequence("F9"), self, activated=self.__previous_on_click)
        QShortcut(QKeySequence("F10"), self, activated=self.__play_on_click)
        QShortcut(QKeySequence("F11"), self, activated=self.__next_on_click)

    def __playlist_on_double_click(self, item: QListWidgetItem) -> None:
        """Play track when double-clicked in playlist."""
        self.__current_index = self.__playlist.row(item)
        self.__start_playback()

    def __save_playlist(self) -> None:
        """Save playlist to file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "Playlist (*.m3u)")
        if not filename:
            return
        with open(filename, "w", encoding="utf-8") as f:
            for path in self.__files:
                f.write(path + "\n")

    def __load_playlist(self) -> None:
        """Load playlist from file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Playlist", "", "Playlist (*.m3u)")
        if not filename:
            return
        with open(filename, encoding="utf-8") as f:
            self.__files = [line.strip() for line in f if line.strip()]
        self.__playlist.clear()
        for path in self.__files:
            self.__playlist.addItem(os.path.basename(path))
        self.__current_index = 0
        self.__current.setText(f"Loaded playlist with {len(self.__files)} files.")

    def __browse_on_click(self) -> None:
        """Browse button on click callback."""
        files, _ = QFileDialog.getOpenFileNames(self, "Open MIDI Files", "",
                                                "MIDI Files (*.mid *.midi)")
        if not files:
            return
        self.__files = files
        self.__current_index = 0
        self.__playlist.clear()
        for f in files:
            self.__playlist.addItem(os.path.basename(f))
        self.__current.setText(f"Loaded {len(files)} files. Ready to play.")

    def __previous_on_click(self) -> None:
        """Previous button on click callback."""
        if self.__files and self.__current_index > 0:
            self.__current_index -= 1
            self.__start_playback()

    def __play_on_click(self) -> None:
        """Play button on click callback."""
        if -1 == self.__current_index or not self.__files:
            self.__current.setText("Please load MIDI files first!")
            return
        if self.__thread and self.__thread.isRunning():
            self.__thread.toggle_pause()
            if self.__thread.paused:
                self.__play.setText("Resume")
            else:
                self.__play.setText("Pause")
        else:
            self.__start_playback()

    def __next_on_click(self) -> None:
        """Next button on click callback."""
        if self.__files and self.__current_index < len(self.__files) - 1:
            self.__current_index += 1
            self.__start_playback()

    def __set_volume(self, value: int) -> None:
        """Adjust FluidSynth volume gain."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.set_volume(value)

    @Slot(int)
    def __update_progressbar(self, value: int) -> None:
       """Update pprogressbar state."""
       self.__progressbar.setValue(value)

    def __start_playback(self) -> None:
        """Start playback."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.stop()
            self.__thread.wait()
        filename: str = self.__files[self.__current_index]
        self.__current.setText(f"Playing: {filename}")
        self.__play.setText("Pause")
        self.__thread = Worker(filename, self.__soundfont)
        self.__thread.progress.connect(self.__update_progressbar)
        self.__thread.finished.connect(lambda: self.__play.setText("Play"))
        self.__thread.start()
        self.__playlist.setCurrentRow(self.__current_index)

    def __construct_button(self, text: str, callback: Callable) -> QPushButton:
        """Construct button."""
        button: QPushButton = QPushButton(text)
        button.clicked.connect(callback)
        button.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0A060;
                color: #1A1A1A;
            }
        """)
        return button

    def __construct_upper_section(self) -> QHBoxLayout:
        """Construc upper section."""
        layout: QHBoxLayout = QHBoxLayout()
        layout.addWidget(self.__construct_button("Browse MIDI Files", self.__browse_on_click))
        layout.addWidget(self.__construct_button("Save Playlist", self.__save_playlist))
        layout.addWidget(self.__construct_button("Load Playlist", self.__load_playlist))
        return layout

    def __construct_volume_slider(self) -> QHBoxLayout:
        """Coonstruct volume slider."""
        layout: QHBoxLayout = QHBoxLayout()
        volume: QSlider = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 127)
        volume.setValue(100)
        volume.valueChanged.connect(self.__set_volume)
        volume.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #8D6E63;
                height: 8px;
                background: #1A1A1A;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2E7D32;
                border: 1px solid #C0A060;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #C0A060;
            }
            QSlider::sub-page:horizontal {
                background: #2E7D32;
                border-radius: 4px;
            }
        """)
        layout.addWidget(QLabel("Volume"))
        layout.addWidget(volume)
        return layout

    def __construct_track(self) -> QHBoxLayout:
        """Construct track section."""
        layout: QHBoxLayout = QHBoxLayout()
        self.__progressbar = QProgressBar(minimum=0, maximum=100,
                                          orientation=Qt.Orientation.Horizontal)
        self.__progressbar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #8D6E63;
                border-radius: 10px;
                text-align: center;
                height: 24px;
                background: #1A1A1A;
                color: #E0E0E0;
                font-weight: bold;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E7D32, stop:1 #C0A060
                );
            }

        """)
        layout.addWidget(self.__progressbar, stretch=1)
        layout.addLayout(self.__construct_volume_slider())
        return layout

    def __construct_controls(self) -> QHBoxLayout:
        """Construct player controls."""
        self.__play = self.__construct_button("Play (F10)", self.__play_on_click)
        layout: QHBoxLayout = QHBoxLayout()
        layout.addWidget(self.__construct_button("Previous (F9)", self.__previous_on_click))
        layout.addWidget(self.__play)
        layout.addWidget(self.__construct_button("Next (F11)", self.__next_on_click))
        return layout

    def __construct_layout(self) -> None:
        """Construct layout."""
        widget: QWidget = QWidget()
        self.setCentralWidget(widget)
        layout: QVBoxLayout = QVBoxLayout(widget)
        layout.addLayout(self.__construct_upper_section())
        layout.addWidget(self.__playlist)
        layout.addWidget(self.__current)
        layout.addLayout(self.__construct_track())
        layout.addLayout(self.__construct_controls())

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: Player = Player()
    window.show()
    sys.exit(app.exec())
