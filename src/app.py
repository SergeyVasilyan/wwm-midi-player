"""Simple PySide6 MIDI player."""

import contextlib
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import override

import keyboard
import mido
import tinysoundfont
import win32gui
from PySide6.QtCore import QRect, QSize, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QGuiApplication, QIcon, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.buttons.next import NextButton
from ui.buttons.play import PlayButton
from ui.buttons.previous import PreviousButton
from ui.progressbar import ProgressBar
from ui.settings import SettingsDialog
from ui.special import SpecialDialog
from ui.toggle_switch import ToggleSwitch
from ui.viewer import Viewer
from ui.volume_slider import Volume
from utils.common import Colors, resource_path
from utils.midi_timing import calculate_duration
from utils.playlist import next_track_index
from utils.wwm_macro import KeyManager


class Worker(QThread):
    """MIDI player worker."""

    duration_ready: Signal = Signal(float)
    error: Signal = Signal(str)
    track_ended: Signal = Signal()

    def __init__(self, filename: str, soundfont: str, is_audio: bool=False) -> None:
        """Initialize worker."""
        super().__init__()
        self.__is_audio: bool = is_audio
        self.__filename: str = filename
        self.__soundfont: str = soundfont
        self.__key_manager: KeyManager = KeyManager()
        self.__running: bool = True
        self.__paused: bool = False
        self.__volume: int = 100

    @property
    def paused(self) -> bool:
        """Return pause state."""
        return self.__paused

    def __calculate_duration(self, midi: mido.MidiFile) -> None:
        """Calculate overall duration."""
        self.duration_ready.emit(calculate_duration(midi))

    def __add_note(self, synth: tinysoundfont.Synth, msg: mido.Message, chord_notes: list[int],
                         velocities: list[int]) -> None:
        """Add note details."""
        if msg.type == "note_on" and msg.velocity > 0:
            chord_notes.append(msg.note)
            velocities.append(msg.velocity)
        elif msg.type == "note_off" and self.__is_audio:
            synth.noteoff(0, msg.note)

    def __flush_tick_events(self, handle: int, synth: tinysoundfont.Synth,
                                  tick_events: list[mido.Message]) -> None:
        """Flush tick events."""
        if not tick_events:
            return
        chord_notes: list[int] = []
        velocities: list[int] = []
        for msg in tick_events:
            self.__add_note(synth, msg, chord_notes, velocities)
        if chord_notes:
            if self.__is_audio:
                chord_velocity: int = max(velocities) if velocities else 64
                for n in chord_notes:
                    synth.noteon(0, n, chord_velocity)
                synth.control_change(0, 7, self.__volume)
            else:
                self.__key_manager.play_chord(handle, chord_notes)
        tick_events.clear()

    @override
    def run(self) -> None:
        """Worker body with proper chord grouping and tempo handling."""
        try:
            player: mido.MidiFile = mido.MidiFile(self.__filename)
        except mido.midifiles.meta.KeySignatureError:
            self.error.emit("Invalid MIDI File.\nPlease select valid MIDI file.")
            return
        except Exception as exc:  # noqa: BLE001 - surface any parse failure to the UI
            self.error.emit(f"Failed to load MIDI file.\n{exc}")
            return
        synth: tinysoundfont.Synth = tinysoundfont.Synth()
        handle: int = 0
        if self.__is_audio:
            synth.start()
            synth.program_select(0, synth.sfload(self.__soundfont), 0, 0)
        else:
            handle = win32gui.FindWindow(None, "Where Winds Meet")
            if not handle:
                self.error.emit("Where Winds Meet is not running.\n"
                                "Please run the game then try again.")
                return
        tick_events: list[mido.Message] = []
        natural_end: bool = True
        try:
            self.__calculate_duration(player)
            current_song_time: float = .0
            start_time: float = time.perf_counter()
            for msg in player:
                if not self.__running:
                    natural_end = False
                    break
                if self.__paused:
                    if self.__is_audio:
                        for i in range(16):
                            synth.control_change(i, 123, 0)
                    pause_start: float = time.perf_counter()
                    while self.__paused and self.__running:
                        time.sleep(0.05)
                    start_time += (time.perf_counter() - pause_start)
                current_song_time += msg.time
                while self.__running:
                    elapsed: float = (time.perf_counter() - start_time)
                    if elapsed >= current_song_time:
                        break
                    time.sleep(min(0.001, current_song_time - elapsed))
                if msg.type in ("note_on", "note_off"):
                    tick_events = [msg]
                    self.__flush_tick_events(handle, synth, tick_events)
                elif msg.type == "control_change" and self.__is_audio:
                    synth.control_change(0, msg.control, msg.value)
                if self.__is_audio:
                    synth.control_change(0, 7, self.__volume)
            self.__flush_tick_events(handle, synth, tick_events)
        except Exception as exc:  # noqa: BLE001 - surface any playback failure to the UI
            natural_end = False
            self.error.emit(f"Playback error.\n{exc}")
        finally:
            synth.stop()
        if natural_end:
            self.track_ended.emit()

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
        screen_size: QRect = QGuiApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(QSize(screen_size.width() // 2, screen_size.height() // 2))
        self.__files: list[str] = []
        self.__current_index: int = -1
        self.__thread: Worker|None = None
        self.__repeat: bool = False
        self.__shuffle: bool = False
        self.__soundfont: Path = resource_path("GeneralUser.sf2")
        self.__file: QLabel = QLabel("No files loaded")
        self.__file.setStyleSheet("font-weight: bold;")
        self.__progressbar: ProgressBar = ProgressBar()
        self.__mode_toggle: ToggleSwitch = ToggleSwitch()
        self.__current_time: QLabel = QLabel("00:00")
        self.__duration_time: QLabel = QLabel("00:00")
        self.__current_time.setStyleSheet("font-weight: bold;")
        self.__duration_time.setStyleSheet("font-weight: bold;")
        self.__current: int = 0
        self.__duration: int = 0
        self.__artists: Viewer
        self.__songs: Viewer
        self.__play: PlayButton
        self.__progress_timer: QTimer
        self.__construct_menu_bar()
        self.__construct_layout()
        self.__bind_shortcuts()

    @staticmethod
    def __convert_to_mm_ss(seconds: int) -> tuple[int, int]:
        """Convert seconds to humane format MM:SS."""
        return divmod(seconds, 60)

    def __bind_shortcuts(self) -> None:
        """Bind shortcuts."""
        keyboard.add_hotkey("f9", self.__previous_on_click)
        keyboard.add_hotkey("f10", self.__play.click)
        keyboard.add_hotkey("f11", self.__next_on_click)
        keyboard.add_hotkey("f8", self.__mode_toggle.toggle)

    @Slot(float)
    def __duration_ready(self, duration: float) -> None:
        """Set duration and start timer."""
        self.__current = 0
        self.__duration = int(duration)
        minutes, seconds = self.__convert_to_mm_ss(self.__duration)
        self.__duration_time.setText(f"{minutes}:{seconds:02d}")
        self.__progressbar.setMaximum(self.__duration)
        with contextlib.suppress(AttributeError):
            self.__progress_timer.stop()
        self.__progress_timer = QTimer(self)
        self.__progress_timer.timeout.connect(self.__update_progress)
        self.__progress_timer.start(1_000)

    @Slot()
    def __update_progress(self) -> None:
        """Update progress."""
        if self.__thread and self.__thread.paused:
            return
        self.__progressbar.setValue(self.__current)
        minutes, seconds = self.__convert_to_mm_ss(self.__current)
        self.__current_time.setText(f"{minutes}:{seconds:02d}")
        if self.__current >= self.__duration:
            self.__progress_timer.stop()
            return
        self.__current += 1

    @Slot(str)
    def __show_error(self, msg: str) -> None:
        """Show error message and stop counter."""
        with contextlib.suppress(AttributeError):
            self.__progress_timer.stop()
        self.__progressbar.setValue(0)
        self.__current_time.setText("00:00")
        QMessageBox.critical(self, "Error", msg)

    def __start_playback(self) -> None:
        """Start playback."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.stop()
            self.__thread.wait()
        self.__play.change.emit(True)
        self.__songs.widget.setCurrentRow(self.__current_index)
        is_audio: bool = self.__mode_toggle.isChecked()
        self.__thread = Worker(self.__files[self.__current_index], self.__soundfont.as_posix(),
                               is_audio)
        self.__thread.duration_ready.connect(self.__duration_ready)
        self.__thread.error.connect(self.__show_error)
        self.__thread.track_ended.connect(self.__on_track_ended)
        self.__thread.finished.connect(lambda: self.__play.change.emit(False))
        self.__thread.start()
        self.__file.setText(self.__songs.widget.currentItem().text().split(".")[0])

    def __songs_on_double_click(self, item: QListWidgetItem) -> None:
        """Play track when double-clicked in song."""
        self.__current_index = self.__songs.widget.row(item)
        self.__start_playback()

    def __artists_on_double_click(self, item: QListWidgetItem) -> None:
        """Filter songs by double-clicked artist."""
        artist: str = item.text()
        songs: QListWidget = self.__songs.widget
        for i in range(songs.count()):
            song_item: QListWidgetItem = songs.item(i)
            if artist == "ALL" or artist in song_item.text():
                song_item.setHidden(False)
            else:
                song_item.setHidden(True)

    def __save_playlist(self) -> None:
        """Save playlist to file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "Playlist (*.m3u)")
        if not filename:
            return
        with Path(filename).open("w", encoding="utf-8") as f:
            for path in self.__files:
                f.write(path + "\n")

    def __add_songs(self) -> None:
        """Add songs."""
        self.__current_index = 0
        self.__artists.widget.clear()
        self.__songs.widget.clear()
        artists: set[str] = set()
        for f in self.__files:
            file_name: str = Path(f).name
            self.__songs.widget.addItem(file_name)
            artist: str = "Unknown"
            if " - " in file_name:
                artist = file_name.split(" - ")[0]
            for group in re.split(r",| feat | ft | feat. | ft. |&", artist):
                artists.add(group.strip())
        self.__artists.widget.addItems(["ALL", *sorted(artists)])
        self.__artists.widget.setCurrentRow(0)

    def __load_playlist(self) -> None:
        """Load playlist from file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Playlist", "", "Playlist (*.m3u)")
        if not filename:
            return
        with Path(filename).open(encoding="utf-8") as f:
            self.__files = [line.strip() for line in f if line.strip()]
        self.__add_songs()
        self.__file.setText(f"Loaded playlist with {len(self.__files)} files.")

    def __browse_on_click(self) -> None:
        """Browse button on click callback."""
        files, _ = QFileDialog.getOpenFileNames(self, "Open MIDI Files", "",
                                                "MIDI Files (*.mid *.midi)")
        if not files:
            return
        self.__files = files
        self.__add_songs()
        self.__file.setText(f"Loaded {len(files)} files. Ready to play.")

    def __previous_on_click(self) -> None:
        """Previous button on click callback."""
        if self.__files and self.__current_index > 0:
            self.__current_index -= 1
            self.__start_playback()

    def __play_on_click(self) -> None:
        """Play button on click callback."""
        if self.__current_index == -1 or not self.__files:
            self.__file.setText("Please load MIDI files first!")
            self.__play.change.emit(False)
            return
        if self.__thread and self.__thread.isRunning():
            self.__play.change.emit(self.__thread.paused)
            self.__thread.toggle_pause()
        else:
            self.__start_playback()

    def __next_index(self) -> int|None:
        """Return the index to advance to, honoring shuffle/repeat, or None to stop."""
        return next_track_index(self.__current_index, len(self.__files),
                                 shuffle=self.__shuffle, repeat=self.__repeat)

    def __next_on_click(self) -> None:
        """Next button on click callback."""
        index: int|None = self.__next_index()
        if index is not None:
            self.__current_index = index
            self.__start_playback()

    @Slot()
    def __on_track_ended(self) -> None:
        """Advance to the next track when the current one finishes on its own."""
        self.__next_on_click()

    def __set_repeat(self, checked: bool) -> None:
        """Toggle repeat-playlist mode."""
        self.__repeat = checked

    def __set_shuffle(self, checked: bool) -> None:
        """Toggle shuffle mode."""
        self.__shuffle = checked

    def __set_volume(self, value: int) -> None:
        """Adjust FluidSynth volume gain."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.set_volume(value)

    def __show_settings(self) -> None:
        """Open Settings dialog."""
        dialog: SettingsDialog = SettingsDialog(self)
        dialog.exec()

    def __show_about(self) -> None:
        """Show about message."""
        QMessageBox.information(self, "About",
                                "MIDI Player for WWM\nBuilt with PySide6 + TinySoundFont")

    def __show_special(self) -> None:
        """Open Special dialog."""
        dialog: SpecialDialog = SpecialDialog(self)
        dialog.exec()

    def __construct_button(self, text: str, callback: Callable, key: str="") -> QVBoxLayout:
        """Construct button."""
        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        button: QPushButton
        if text == "Next":
            button = NextButton()
        elif text == "Previous":
            button = PreviousButton()
        elif text == "Play":
            button = PlayButton()
            self.__play = button
        else:
           button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        if key:
            layout.addWidget(QLabel(f"[{key}]"), alignment=Qt.AlignmentFlag.AlignCenter)
        return layout

    def __construct_file_menu(self) -> None:
        """Construct file menu."""
        menu_bar: QMenuBar = self.menuBar()
        menu: QMenu = menu_bar.addMenu("&File")
        open_action: QAction = QAction("Open MIDI file", self)
        save_action: QAction = QAction("Save Playlist", self)
        load_action: QAction = QAction("Load Playlist", self)
        exit_action: QAction = QAction("Exit", self)
        open_action.triggered.connect(self.__browse_on_click)
        save_action.triggered.connect(self.__save_playlist)
        load_action.triggered.connect(self.__load_playlist)
        exit_action.triggered.connect(self.close)
        menu.addAction(open_action)
        menu.addAction(save_action)
        menu.addAction(load_action)
        menu.addAction(exit_action)

    def __construct_playback_menu(self) -> None:
        """Construct playback menu."""
        menu_bar: QMenuBar = self.menuBar()
        menu: QMenu = menu_bar.addMenu("&Playback")
        previous_action: QAction = QAction("Previous", parent=self)
        play_action: QAction = QAction("Play/Pause", self)
        next_action: QAction = QAction("Next", self)
        repeat_action: QAction = QAction("Repeat", self, checkable=True)
        shuffle_action: QAction = QAction("Shuffle", self, checkable=True)
        previous_action.triggered.connect(self.__previous_on_click)
        play_action.triggered.connect(self.__play_on_click)
        next_action.triggered.connect(self.__next_on_click)
        repeat_action.toggled.connect(self.__set_repeat)
        shuffle_action.toggled.connect(self.__set_shuffle)
        menu.addAction(previous_action)
        menu.addAction(play_action)
        menu.addAction(next_action)
        menu.addSeparator()
        menu.addAction(repeat_action)
        menu.addAction(shuffle_action)

    def __construct_setting_menu(self) -> None:
        """Construct settings menu."""
        menu_bar: QMenuBar = self.menuBar()
        menu: QMenu = menu_bar.addMenu("&Settings")
        settings_action: QAction = QAction("Settings", self)
        settings_action.triggered.connect(self.__show_settings)
        menu.addAction(settings_action)

    def __construct_help_menu(self) -> None:
        """Construct help menu."""
        menu_bar: QMenuBar = self.menuBar()
        menu: QMenu = menu_bar.addMenu("&Help")
        about_action: QAction = QAction("About", self)
        about_action.triggered.connect(self.__show_about)
        menu.addAction(about_action)

    def __construct_special_menu(self) -> None:
        """Construct special menu."""
        menu_bar: QMenuBar = self.menuBar()
        menu: QMenu = menu_bar.addMenu("&Special")
        action: QAction = QAction("Thanks", self)
        action.triggered.connect(self.__show_special)
        menu.addAction(action)

    def __construct_menu_bar(self) -> None:
        """Construct menu bar."""
        self.__construct_file_menu()
        self.__construct_playback_menu()
        self.__construct_setting_menu()
        self.__construct_help_menu()
        self.__construct_special_menu()

    def __construct_volume_slider(self) -> QHBoxLayout:
        """Construct volume slider."""
        layout: QHBoxLayout = QHBoxLayout()
        volume: Volume = Volume()
        volume.valueChanged.connect(self.__set_volume)
        layout.addWidget(QLabel("Volume"))
        layout.addWidget(volume)
        return layout

    def __construct_mode_toggle(self) -> QHBoxLayout:
        """Construct mode toggle."""
        layout: QHBoxLayout = QHBoxLayout()
        layout.addWidget(QLabel("WWM"))
        layout.addWidget(self.__mode_toggle, stretch=1)
        layout.addWidget(QLabel("Audio"))
        return layout

    def __construct_helpers(self) -> QWidget:
        """Construct helper widgets."""
        widget: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.__construct_volume_slider())
        layout.addLayout(self.__construct_mode_toggle())
        return widget

    def __construct_artists_section(self) -> Viewer:
        """Construct Artists section."""
        self.__artists = Viewer(accent=Colors.ACCENT_2)
        self.__artists.widget.itemDoubleClicked.connect(self.__artists_on_double_click)
        return self.__artists

    def __construct_songs_section(self) -> Viewer:
        """Construct Songs section."""
        self.__songs = Viewer()
        self.__songs.widget.itemDoubleClicked.connect(self.__songs_on_double_click)
        return self.__songs

    def __construct_playlist(self) -> QHBoxLayout:
        """Construct track section."""
        layout: QHBoxLayout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__construct_artists_section(), stretch=1)
        layout.addWidget(self.__construct_songs_section(), stretch=3)
        return layout

    def __construct_track(self) -> QHBoxLayout:
        """Construct track section."""
        layout: QHBoxLayout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.__file, stretch=0)
        layout.addWidget(self.__progressbar, stretch=1)
        layout.addWidget(self.__current_time, stretch=0)
        layout.addWidget(QLabel("/"), stretch=0)
        layout.addWidget(self.__duration_time, stretch=0)
        return layout

    def __construct_controls(self) -> QGridLayout:
        """Construct player controls."""
        grid: QGridLayout = QGridLayout()
        widget: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.__construct_button("Previous", self.__previous_on_click, key="F9"))
        layout.addLayout(self.__construct_button("Play", self.__play_on_click, key="F10"))
        layout.addLayout(self.__construct_button("Next", self.__next_on_click, key="F11"))
        grid.addWidget(widget, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.__construct_helpers(), 0, 2, alignment=Qt.AlignmentFlag.AlignRight)
        columns_count: int = grid.columnCount()
        column_width: int = self.width() // columns_count
        for column in range(columns_count):
            grid.setColumnMinimumWidth(column, column_width)
        return grid

    def __construct_layout(self) -> None:
        """Construct layout."""
        widget: QWidget = QWidget()
        self.setCentralWidget(widget)
        layout: QVBoxLayout = QVBoxLayout(widget)
        layout.addLayout(self.__construct_playlist())
        layout.addLayout(self.__construct_track())
        layout.addLayout(self.__construct_controls())

    @override
    def closeEvent(self, event: QCloseEvent, /) -> None:
        """Override close event."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.stop()
            self.__thread.wait()
        return super().closeEvent(event)

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("WWM MIDI Player")
    icon: Path = resource_path("src/input/logo.ico")
    app.setWindowIcon(QIcon(icon.as_posix()))
    window: Player = Player()
    window.show()
    sys.exit(app.exec())
