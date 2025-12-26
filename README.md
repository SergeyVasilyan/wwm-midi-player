# Windows MIDI Player (FluidSynth + PySide6)

A modern, themed MIDI player built with **PySide6** and **FluidSynth**, featuring:
- 🎼 Playlist support with interactive view
- 🎚️ Volume control via styled slider
- 📊 Progress bar with modern styling
- 🎹 Keyboard shortcuts (F9 = Previous, F10 = Play/Pause, F11 = Next)
- 🌌 Customizable UI themes (e.g. Where Winds Meet palette)

## Features
- Load multiple `.mid` / `.midi` files into a playlist
- Play, pause, resume, and skip tracks
- Real‑time progress tracking
- Styled UI with Qt stylesheets
- Save and load playlists (`.m3u` format)

## Requirements
- Python 3.10+
- [PySide6](https://pypi.org/project/PySide6/)
- [mido](https://pypi.org/project/mido/)
- [pyFluidSynth](https://pypi.org/project/pyFluidSynth/)
- A SoundFont file (e.g. [GeneralUser GS.sf2](https://schristiancollins.com/generaluser.php))

## Installation
```bash
pip install PySide6 mido pyFluidSynth
```

Place your SoundFont (`GeneralUser.sf2`) in the project directory.

## Usage

```bash
python app.py
```

Controls:

- F9 → Previous track
- F10 → Play/Pause
- F11 → Next track
- Volume slider adjusts playback volume

## LICENSE

GPL-3.0 License
