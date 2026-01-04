"""Simple PySide6 MIDI player."""

import os
import sys
import time
from collections.abc import Callable
from typing import override

import fluidsynth
import keyboard
import mido
from PySide6.QtCore import QRect, QSize, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QGuiApplication, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.ui.buttons.next import NextButton
from src.ui.buttons.play import PlayButton
from src.ui.buttons.previous import PreviousButton
from src.ui.playlist import PlayList
from src.ui.progressbar import ProgressBar
from src.ui.toggle_switch import ToggleSwitch
from src.ui.volume_slider import Volume
from src.utils.wwm_macro import play_chord


class Worker(QThread):
    """MIDI player worker."""

    duration_ready: Signal = Signal(float)

    def __init__(self, filename: str, soundfont: str, is_audio: bool=False) -> None:
        """Initialize worker."""
        super().__init__()
        self.__error: bool = False
        self.__is_audio: bool = is_audio
        self.__filename: str = filename
        self.__soundfont: str = soundfont
        self.__running: bool = True
        self.__paused: bool = False
        self.__volume: int = 100

    @property
    def paused(self) -> bool:
        """Return pause state."""
        return self.__paused

    @property
    def error(self) -> bool:
        """Return error state."""
        return self.__error

    def __build_tempo_map(self, midi: mido.MidiFile) -> list[tuple[int, int]]:
        """Return a list of (abs_tick, tempo_microsec_per_beat), sorted by abs_tick.

        Default tempo is 500_000 (120 BPM). Tempo messages are taken from all tracks,
        but commonly live in track 0.
        """
        tempo_map: list[tuple[int, int]] = [(0, 500_000)]
        for track in midi.tracks:
            abs_ticks: int = 0
            for msg in track:
                abs_ticks += msg.time
                if "set_tempo" == msg.type:
                    tempo_map.append((abs_ticks, msg.tempo))
        clean_tempo_map: dict[int, int] = {}
        for tick, tempo in tempo_map:
            clean_tempo_map[tick] = tempo
        return sorted(clean_tempo_map.items())

    def __find_max_end_tick(self, midi: mido.MidiFile) -> int:
        """Find max end tick value."""
        max_end_tick: int = 0
        for track in midi.tracks:
            abs_ticks: int = 0
            has_notes: bool = False
            for msg in track:
                abs_ticks += msg.time
                if msg.type in ("note_on", "note_off"):
                    has_notes = True
            if has_notes:
                max_end_tick = max(max_end_tick, abs_ticks)
        return max_end_tick

    def __ticks_to_seconds(self, midi: mido.MidiFile, max_end_tick: int,
                                 tempo_map: list[tuple[int, int]]) -> float:
        """Convert an absolute tick position to seconds by walking the tempo segments."""
        ticks_per_beat: int = midi.ticks_per_beat
        total_seconds: float = 0.0
        previous_tick, previous_tempo = tempo_map[0]
        for tick, tempo in tempo_map[1:]:
            segment_end: int = min(max_end_tick, tick)
            if segment_end > previous_tick:
                segment_ticks: int = segment_end - previous_tick
                total_seconds += mido.tick2second(segment_ticks, ticks_per_beat, previous_tempo)
                previous_tick = segment_end
            if max_end_tick <= tick:
                return total_seconds
            previous_tempo = tempo
        if max_end_tick > previous_tick:
            segment_ticks: int = max_end_tick - previous_tick
            total_seconds += mido.tick2second(segment_ticks, ticks_per_beat, previous_tempo)
        return total_seconds

    def __calculate_duration(self) -> None:
        """Calculate overall duration."""
        midi: mido.MidiFile = mido.MidiFile(self.__filename)
        tempo_map: list[tuple[int, int]] = self.__build_tempo_map(midi)
        max_end_tick: int = self.__find_max_end_tick(midi)
        self.duration_ready.emit(self.__ticks_to_seconds(midi, max_end_tick, tempo_map))

    def __add_note(self, synth: fluidsynth.Synth, msg: mido.Message, chord_notes: list[int],
                         velocities: list[int]) -> None:
        """Add note details."""
        if "note_on" == msg.type and 0 < msg.velocity:
            chord_notes.append(msg.note)
            velocities.append(msg.velocity)
        elif "note_off" == msg.type and self.__is_audio:
            synth.noteoff(0, msg.note)

    def __flush_tick_events(self, synth: fluidsynth.Synth, tick_events: list[mido.Message]) -> None:
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
                synth.cc(0, 7, self.__volume)
            else:
                play_chord(chord_notes)
        tick_events.clear()

    @override
    def run(self) -> None:
        """Worker body with proper chord grouping and tempo handling."""
        self.__error = False
        try:
            player: mido.MidiFile = mido.MidiFile(self.__filename)
        except mido.midifiles.meta.KeySignatureError:
            self.__error = True
            return
        synth: fluidsynth.Synth = fluidsynth.Synth()
        if self.__is_audio:
            synth.start(driver="dsound")
            synth.program_select(0, synth.sfload(self.__soundfont), 0, 0)
        tick_events: list[mido.Message] = []
        start_time: float = time.perf_counter()
        self.__calculate_duration()
        for msg in player.play():
            while self.__paused and self.__running:
                time.sleep(0.05)
            if not self.__running:
                break
            target: float = start_time + msg.time
            while True:
                now: float = time.perf_counter()
                if now >= target:
                    break
                time.sleep(min(0.001, target - now))
            if msg.type in ("note_on", "note_off"):
                tick_events.append(msg)
            self.__flush_tick_events(synth, tick_events)
            if self.__is_audio:
                synth.cc(0, 7, self.__volume)
        self.__flush_tick_events(synth, tick_events)
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
        self.__file: QLabel = QLabel("No files loaded")
        self.__playlist: PlayList = PlayList()
        self.__playlist.itemDoubleClicked.connect(self.__playlist_on_double_click)
        self.__play: PlayButton
        self.__progressbar: ProgressBar = ProgressBar()
        self.__mode_toggle: ToggleSwitch = ToggleSwitch()
        self.__current_time: QLabel = QLabel("00:00")
        self.__duration_time: QLabel = QLabel("00:00")
        self.__current: int = 0
        self.__duration: int = 0
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
        keyboard.add_hotkey("f10", self.__play_on_click)
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
        try:
            self.__progress_timer.stop()
        except AttributeError:
            ...
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

    def __start_playback(self) -> None:
        """Start playback."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.stop()
            self.__thread.wait()
        self.__play.setChecked(True)
        self.__playlist.setCurrentRow(self.__current_index)
        is_audio: bool = self.__mode_toggle.isChecked()
        self.__thread = Worker(self.__files[self.__current_index], self.__soundfont, is_audio)
        self.__thread.duration_ready.connect(self.__duration_ready)
        self.__thread.finished.connect(lambda: self.__play.setChecked(False))
        if not is_audio:
            time.sleep(1)
        self.__thread.start()
        if self.__thread.error:
            self.__file.setText("Invalid file. Please select another one.")
        else:
            self.__file.setText(self.__playlist.currentItem().text())

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
        self.__file.setText(f"Loaded playlist with {len(self.__files)} files.")

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
        self.__file.setText(f"Loaded {len(files)} files. Ready to play.")

    def __previous_on_click(self) -> None:
        """Previous button on click callback."""
        if self.__files and self.__current_index > 0:
            self.__current_index -= 1
            self.__start_playback()

    def __play_on_click(self) -> None:
        """Play button on click callback."""
        if -1 == self.__current_index or not self.__files:
            self.__file.setText("Please load MIDI files first!")
            self.__play.setChecked(False)
            return
        if self.__thread and self.__thread.isRunning():
            self.__play.setChecked(self.__thread.paused)
            self.__thread.toggle_pause()
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

    def __show_about(self):
        QMessageBox.information(self, "About",
                                "Windows MIDI Player for WWM\nBuilt with PySide6 + FluidSynth")

    def __construct_button(self, text: str, callback: Callable, key: str="") -> QVBoxLayout:
        """Construct button."""
        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        button: QPushButton
        if "Next" == text:
            button = NextButton()
        elif "Previous" == text:
            button = PreviousButton()
        elif "Play" == text:
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
        previous_action: QAction = QAction("Previous", self)
        play_action: QAction = QAction("Play/Pause", self)
        next_action: QAction = QAction("Next", self)
        previous_action.triggered.connect(self.__previous_on_click)
        play_action.triggered.connect(self.__play_on_click)
        next_action.triggered.connect(self.__next_on_click)
        menu.addAction(previous_action)
        menu.addAction(play_action)
        menu.addAction(next_action)

    def __construct_help_menu(self) -> None:
        """Construct help menu."""
        menu_bar: QMenuBar = self.menuBar()
        menu: QMenu = menu_bar.addMenu("&Help")
        about_action: QAction = QAction("About", self)
        about_action.triggered.connect(self.__show_about)
        menu.addAction(about_action)

    def __construct_menu_bar(self) -> None:
        """Construct menu bar."""
        self.__construct_file_menu()
        self.__construct_playback_menu()
        self.__construct_help_menu()

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

    def __construct_track(self) -> QHBoxLayout:
        """Construct track section."""
        layout: QHBoxLayout = QHBoxLayout()
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
        grid.addWidget(self.__file, 0, 0,
                        alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
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
        layout.addWidget(self.__playlist)
        layout.addLayout(self.__construct_track())
        layout.addLayout(self.__construct_controls())

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: Player = Player()
    window.show()
    sys.exit(app.exec())
