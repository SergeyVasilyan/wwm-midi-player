"""Simple PySide6 MIDI player."""

import contextlib
import sys
import time
from pathlib import Path
from typing import override

import keyboard
import mido
import tinysoundfont
import win32gui
from PySide6.QtCore import QEvent, QPoint, QRect, QSize, QThread, QTimer, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QGuiApplication,
    QIcon,
    QMouseEvent,
    Qt,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ui.buttons.play import PlayButton
from ui.now_playing_bar import NowPlayingBar
from ui.search_box import SearchBox
from ui.settings import SettingsDialog
from ui.song_delegate import ARTIST_ROLE, TITLE_ROLE
from ui.special import SpecialDialog
from ui.titlebar import TitleBar
from ui.toast import Toast
from ui.viewer import Viewer
from utils.common import RADIUS_SM, RESIZE_MARGIN, SPACING_MD, Colors, resource_path
from utils.midi_timing import calculate_duration
from utils.playlist import next_track_index
from utils.track_info import TrackInfo, parse_track_info
from utils.window_geometry import compute_resize_edges
from utils.wwm_macro import KeyManager, best_octave_shift


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
        self.__sent_volume: int|None = None
        self.__wwm_shift: int = 0

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
            else:
                shifted_notes: list[int] = [n + self.__wwm_shift for n in chord_notes]
                self.__key_manager.play_chord(handle, shifted_notes)
        tick_events.clear()

    def __compute_wwm_shift(self, player: mido.MidiFile) -> int:
        """Pick the whole-octave transposition that best avoids WWM key-mapping collisions.

        Pre-scans the file's simultaneous note groups (without playing anything)
        and picks the shift that minimizes distinct notes folding onto the same
        key - see utils.wwm_macro.best_octave_shift.
        """
        chords: list[list[int]] = []
        tick_notes: list[int] = []
        for msg in player:
            if msg.time > 0:
                if tick_notes:
                    chords.append(tick_notes)
                tick_notes = []
            if msg.type == "note_on" and msg.velocity > 0:
                tick_notes.append(msg.note)
        if tick_notes:
            chords.append(tick_notes)
        return best_octave_shift(chords)

    def __apply_volume(self, synth: tinysoundfont.Synth) -> None:
        """Send the current volume to the synth only when it has actually changed."""
        if self.__volume != self.__sent_volume:
            synth.control_change(0, 7, self.__volume)
            self.__sent_volume = self.__volume

    def __wait_until(self, start_time: float, target_song_time: float) -> None:
        """Sleep until target_song_time has elapsed since start_time.

        Sleeps in one coarse chunk down to a small margin, then finishes with
        short 1ms sleeps for accurate timing, instead of spin-sleeping in 1ms
        steps for the entire wait (which wastes CPU on long rests and is
        finer-grained than the OS timer can honor anyway).
        """
        fine_margin: float = 0.005
        while self.__running:
            remaining: float = target_song_time - (time.perf_counter() - start_time)
            if remaining <= 0:
                return
            time.sleep(remaining - fine_margin if remaining > fine_margin else 0.001)

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
            self.__wwm_shift = self.__compute_wwm_shift(player)
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
                if msg.time > 0:
                    # All messages accumulated so far share the tick that has
                    # already elapsed - flush them as one chord before waiting
                    # for the next tick.
                    self.__flush_tick_events(handle, synth, tick_events)
                    current_song_time += msg.time
                    self.__wait_until(start_time, current_song_time)
                if msg.type in ("note_on", "note_off"):
                    tick_events.append(msg)
                elif msg.type == "control_change" and self.__is_audio:
                    synth.control_change(0, msg.control, msg.value)
                if self.__is_audio:
                    self.__apply_volume(synth)
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
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        screen_size: QRect = QGuiApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(QSize(screen_size.width() // 2, screen_size.height() // 2))
        self.__resize_edges: Qt.Edge = Qt.Edge(0)
        self.__files: list[str] = []
        self.__current_index: int = -1
        self.__thread: Worker|None = None
        self.__repeat: bool = False
        self.__shuffle: bool = False
        self.__toast: Toast|None = None
        self.__soundfont: Path = resource_path("GeneralUser.sf2")
        self.__current: int = 0
        self.__duration: int = 0
        self.__search: QLineEdit
        self.__songs: Viewer
        self.__now_playing_bar: NowPlayingBar
        self.__repeat_action: QAction
        self.__shuffle_action: QAction
        self.__central_layout: QVBoxLayout
        self.__title_bar: TitleBar
        self.__menu_bar: QMenuBar
        self.__progress_timer: QTimer
        self.__construct_menu_bar()
        self.__construct_layout()
        self.__wire_now_playing_bar()
        self.__bind_shortcuts()

    def __bind_shortcuts(self) -> None:
        """Bind shortcuts."""
        keyboard.add_hotkey("f9", self.__previous_on_click)
        keyboard.add_hotkey("f10", self.__now_playing_bar.play_button.click)
        keyboard.add_hotkey("f11", self.__next_on_click)
        keyboard.add_hotkey("f8", self.__now_playing_bar.mode_toggle.toggle)

    @Slot(float)
    def __duration_ready(self, duration: float) -> None:
        """Set duration and start timer."""
        self.__current = 0
        self.__duration = int(duration)
        self.__now_playing_bar.set_duration(self.__duration)
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
        self.__now_playing_bar.set_current_time(self.__current)
        if self.__current >= self.__duration:
            self.__progress_timer.stop()
            return
        self.__current += 1

    @Slot()
    def __on_toast_dismissed(self) -> None:
        """Remove the toast from the layout once it's dismissed."""
        if self.__toast is None:
            return
        self.__central_layout.removeWidget(self.__toast)
        self.__toast.deleteLater()
        self.__toast = None

    @Slot(str)
    def __show_error(self, msg: str) -> None:
        """Show error message and stop counter."""
        with contextlib.suppress(AttributeError):
            self.__progress_timer.stop()
        self.__now_playing_bar.reset_progress()
        if self.__toast is not None:
            self.__on_toast_dismissed()
        self.__toast = Toast(msg, self)
        self.__toast.dismissed.connect(self.__on_toast_dismissed)
        self.__central_layout.insertWidget(0, self.__toast)

    def __start_playback(self) -> None:
        """Start playback."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.stop()
            self.__thread.wait()
        self.__now_playing_bar.play_button.change.emit(True)
        self.__songs.set_now_playing_row(self.__current_index)
        is_audio: bool = self.__now_playing_bar.mode_toggle.isChecked()
        self.__thread = Worker(self.__files[self.__current_index], self.__soundfont.as_posix(),
                               is_audio)
        self.__thread.duration_ready.connect(self.__duration_ready)
        self.__thread.error.connect(self.__show_error)
        self.__thread.track_ended.connect(self.__on_track_ended)
        play_button: PlayButton = self.__now_playing_bar.play_button
        self.__thread.finished.connect(lambda: play_button.change.emit(False))
        self.__thread.start()
        info: TrackInfo = parse_track_info(Path(self.__files[self.__current_index]).name)
        self.__now_playing_bar.set_header(info.title, info.artist)

    def __songs_on_double_click(self, item: QListWidgetItem) -> None:
        """Play track when double-clicked in song."""
        self.__current_index = self.__songs.widget.row(item)
        self.__start_playback()

    def __on_search_changed(self, text: str) -> None:
        """Filter songs by search text."""
        needle: str = text.lower()
        songs = self.__songs.widget
        songs.setUpdatesEnabled(False)
        try:
            for i in range(songs.count()):
                item: QListWidgetItem = songs.item(i)
                item.setHidden(needle not in item.text().lower())
        finally:
            songs.setUpdatesEnabled(True)

    def __save_playlist(self) -> None:
        """Save playlist to file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "Playlist (*.m3u)")
        if not filename:
            return
        with Path(filename).open("w", encoding="utf-8") as f:
            for path in self.__files:
                f.write(path + "\n")

    def __add_songs(self) -> None:
        """Rebuild the song list widget from self.__files."""
        if self.__current_index == -1:
            self.__current_index = 0
        self.__songs.widget.clear()
        self.__songs.set_now_playing_row(-1)
        for f in self.__files:
            file_name: str = Path(f).name
            info: TrackInfo = parse_track_info(file_name)
            item: QListWidgetItem = QListWidgetItem(file_name)
            item.setData(TITLE_ROLE, info.title)
            item.setData(ARTIST_ROLE, info.artist)
            self.__songs.widget.addItem(item)
        self.__on_search_changed(self.__search.text())

    def __clear_playlist(self) -> None:
        """Clear the playlist and reset playback state."""
        if self.__thread and self.__thread.isRunning():
            self.__thread.stop()
            self.__thread.wait()
        with contextlib.suppress(AttributeError):
            self.__progress_timer.stop()
        self.__files.clear()
        self.__current_index = -1
        self.__songs.set_now_playing_row(-1)
        self.__songs.widget.clear()
        self.__now_playing_bar.reset_progress()
        self.__now_playing_bar.set_header("No files loaded")

    def __load_playlist(self) -> None:
        """Load playlist from file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Playlist", "", "Playlist (*.m3u)")
        if not filename:
            return
        with Path(filename).open(encoding="utf-8") as f:
            self.__files = [line.strip() for line in f if line.strip()]
        self.__current_index = -1
        self.__add_songs()
        self.__now_playing_bar.set_header(f"Loaded playlist with {len(self.__files)} files.")

    def __browse_on_click(self) -> None:
        """Browse button on click callback: adds files to the current playlist."""
        files, _ = QFileDialog.getOpenFileNames(self, "Open MIDI Files", "",
                                                "MIDI Files (*.mid *.midi)")
        if not files:
            return
        self.__files.extend(files)
        self.__add_songs()
        self.__now_playing_bar.set_header(
            f"Added {len(files)} file(s). Playlist has {len(self.__files)} total.")

    def __previous_on_click(self) -> None:
        """Previous button on click callback."""
        if self.__files and self.__current_index > 0:
            self.__current_index -= 1
            self.__start_playback()

    def __play_on_click(self) -> None:
        """Play button on click callback."""
        if self.__current_index == -1 or not self.__files:
            self.__now_playing_bar.set_header("Please load MIDI files first!")
            self.__now_playing_bar.play_button.change.emit(False)
            return
        if self.__thread and self.__thread.isRunning():
            self.__now_playing_bar.play_button.change.emit(self.__thread.paused)
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

    def __wire_now_playing_bar(self) -> None:
        """Connect the Now Playing bar's buttons/controls to their callbacks."""
        bar: NowPlayingBar = self.__now_playing_bar
        bar.previous_button.clicked.connect(self.__previous_on_click)
        bar.play_button.clicked.connect(self.__play_on_click)
        bar.next_button.clicked.connect(self.__next_on_click)
        bar.shuffle_button.toggled.connect(self.__set_shuffle)
        bar.repeat_button.toggled.connect(self.__set_repeat)
        bar.volume.valueChanged.connect(self.__set_volume)
        self.__wire_repeat_shuffle_sync()

    def __construct_file_menu(self) -> None:
        """Construct file menu."""
        menu_bar: QMenuBar = self.__menu_bar
        menu: QMenu = menu_bar.addMenu("&File")
        open_action: QAction = QAction("Open MIDI file", self)
        save_action: QAction = QAction("Save Playlist", self)
        load_action: QAction = QAction("Load Playlist", self)
        clear_action: QAction = QAction("Clear Playlist", self)
        exit_action: QAction = QAction("Exit", self)
        open_action.triggered.connect(self.__browse_on_click)
        save_action.triggered.connect(self.__save_playlist)
        load_action.triggered.connect(self.__load_playlist)
        clear_action.triggered.connect(self.__clear_playlist)
        exit_action.triggered.connect(self.close)
        menu.addAction(open_action)
        menu.addAction(save_action)
        menu.addAction(load_action)
        menu.addAction(clear_action)
        menu.addSeparator()
        menu.addAction(exit_action)

    def __construct_playback_menu(self) -> None:
        """Construct playback menu."""
        menu_bar: QMenuBar = self.__menu_bar
        menu: QMenu = menu_bar.addMenu("&Playback")
        previous_action: QAction = QAction("Previous", parent=self)
        play_action: QAction = QAction("Play/Pause", self)
        next_action: QAction = QAction("Next", self)
        self.__repeat_action = QAction("Repeat", self, checkable=True)
        self.__shuffle_action = QAction("Shuffle", self, checkable=True)
        previous_action.triggered.connect(self.__previous_on_click)
        play_action.triggered.connect(self.__play_on_click)
        next_action.triggered.connect(self.__next_on_click)
        menu.addAction(previous_action)
        menu.addAction(play_action)
        menu.addAction(next_action)
        menu.addSeparator()
        menu.addAction(self.__repeat_action)
        menu.addAction(self.__shuffle_action)

    def __wire_repeat_shuffle_sync(self) -> None:
        """Keep the Repeat/Shuffle transport buttons and menu actions in sync."""
        bar: NowPlayingBar = self.__now_playing_bar
        self.__repeat_action.toggled.connect(bar.repeat_button.setChecked)
        bar.repeat_button.toggled.connect(self.__repeat_action.setChecked)
        self.__shuffle_action.toggled.connect(bar.shuffle_button.setChecked)
        bar.shuffle_button.toggled.connect(self.__shuffle_action.setChecked)

    def __construct_setting_menu(self) -> None:
        """Construct settings menu."""
        menu_bar: QMenuBar = self.__menu_bar
        menu: QMenu = menu_bar.addMenu("&Settings")
        settings_action: QAction = QAction("Settings", self)
        settings_action.triggered.connect(self.__show_settings)
        menu.addAction(settings_action)

    def __construct_help_menu(self) -> None:
        """Construct help menu."""
        menu_bar: QMenuBar = self.__menu_bar
        menu: QMenu = menu_bar.addMenu("&Help")
        about_action: QAction = QAction("About", self)
        about_action.triggered.connect(self.__show_about)
        menu.addAction(about_action)

    def __construct_special_menu(self) -> None:
        """Construct special menu."""
        menu_bar: QMenuBar = self.__menu_bar
        menu: QMenu = menu_bar.addMenu("&Special")
        action: QAction = QAction("Thanks", self)
        action.triggered.connect(self.__show_special)
        menu.addAction(action)

    def __construct_menu_bar(self) -> None:
        """Construct menu bar."""
        self.__menu_bar = QMenuBar()
        self.__construct_file_menu()
        self.__construct_playback_menu()
        self.__construct_setting_menu()
        self.__construct_help_menu()
        self.__construct_special_menu()
        self.__menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {Colors.BACKGROUND.value.hex};
                color: {Colors.WHITE.value.hex};
                padding: 2px 4px;
                border: none;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 10px;
                border-radius: {RADIUS_SM}px;
            }}
            QMenuBar::item:selected {{ background-color: {Colors.BACKGROUND_2.value.hex}; }}
            QMenuBar::item:pressed {{ background-color: {Colors.ACCENT_1.value.hex}; }}
            QMenu {{
                background-color: {Colors.BACKGROUND_1.value.hex};
                color: {Colors.WHITE.value.hex};
                border: 1px solid {Colors.BACKGROUND_2.value.hex};
                border-radius: {RADIUS_SM}px;
                padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: {RADIUS_SM}px; }}
            QMenu::item:selected {{ background-color: {Colors.ACCENT_1.value.hex}; }}
            QMenu::separator {{
                height: 1px;
                background-color: {Colors.BACKGROUND_2.value.hex};
                margin: 4px 8px;
            }}
        """)

    def __construct_songs_section(self) -> Viewer:
        """Construct Songs section."""
        self.__songs = Viewer()
        self.__songs.widget.itemDoubleClicked.connect(self.__songs_on_double_click)
        return self.__songs

    def __construct_search(self) -> QLineEdit:
        """Construct the song search box."""
        self.__search = SearchBox()
        self.__search.textChanged.connect(self.__on_search_changed)
        return self.__search

    def __construct_playlist(self) -> QVBoxLayout:
        """Construct playlist section."""
        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__construct_search())
        layout.addWidget(self.__construct_songs_section(), stretch=1)
        return layout

    def __construct_layout(self) -> None:
        """Construct layout."""
        root: QWidget = QWidget()
        self.setCentralWidget(root)
        root_layout: QVBoxLayout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        icon: QIcon = QIcon(resource_path("src/input/logo.ico").as_posix())
        self.__title_bar = TitleBar(self, "WWM MIDI Player", icon)
        root_layout.addWidget(self.__title_bar)
        root_layout.addWidget(self.__menu_bar)
        content: QWidget = QWidget()
        self.__central_layout = QVBoxLayout(content)
        self.__central_layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        self.__central_layout.setSpacing(SPACING_MD)
        self.__central_layout.addLayout(self.__construct_playlist())
        root_layout.addWidget(content, stretch=1)
        self.__now_playing_bar = NowPlayingBar()
        root_layout.addWidget(self.__now_playing_bar)

    def __cursor_for_edges(self, edges: Qt.Edge) -> Qt.CursorShape:
        """Map a resize-edge combination to the appropriate resize cursor shape."""
        if edges in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeHorCursor
        if edges in (Qt.Edge.TopEdge, Qt.Edge.BottomEdge):
            return Qt.CursorShape.SizeVerCursor
        if edges in (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge):
            return Qt.CursorShape.SizeFDiagCursor
        if edges in (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.Edge.LeftEdge | Qt.Edge.BottomEdge):
            return Qt.CursorShape.SizeBDiagCursor
        return Qt.CursorShape.ArrowCursor

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update cursor shape and pending resize edges based on proximity to window edges."""
        if self.isMaximized():
            self.__resize_edges = Qt.Edge(0)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            super().mouseMoveEvent(event)
            return
        pos: QPoint = event.position().toPoint()
        self.__resize_edges = compute_resize_edges((pos.x(), pos.y()),
                                                    (self.width(), self.height()), RESIZE_MARGIN)
        self.setCursor(self.__cursor_for_edges(self.__resize_edges))
        super().mouseMoveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start an OS-native resize if the press is near a window edge."""
        if self.__resize_edges != Qt.Edge(0) and event.button() == Qt.MouseButton.LeftButton:
            handle = self.windowHandle()
            if handle is not None:
                handle.startSystemResize(self.__resize_edges)
                return
        super().mousePressEvent(event)

    @override
    def changeEvent(self, event: QEvent) -> None:
        """Sync the title bar's maximize button with the actual window state."""
        if event.type() == QEvent.Type.WindowStateChange:
            self.__title_bar.set_maximized(self.isMaximized())
        super().changeEvent(event)

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
