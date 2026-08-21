# Contributing

Thanks for considering a contribution to the WWM MIDI Player.

## Development setup

```bash
git clone https://github.com/SergeyVasilyan/wwm-midi-player.git
cd wwm-midi-player
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

Run the app from source:

```bash
python src/app.py
```

## Testing and linting

```bash
python -m pytest      # run the test suite
ruff check            # lint
ruff format           # format
pre-commit run --all-files
```

`pytest` covers the pure-logic modules under `src/utils/` (MIDI timing math,
playlist/track-event helpers, etc.) using small in-memory fixtures — no Qt
or filesystem mocking needed for those. There's deliberately no
Qt-widget-level testing; verify UI/GUI changes manually by running the app.

`ruff` is configured strictly in `pyproject.toml` (docstrings required on
every public function/class via pydocstyle's Google convention, plus
`flake8-use-pathlib`, `flake8-unused-arguments`, `flake8-commas`, and more).
Run `ruff check` before opening a PR — CI and `pre-commit` both enforce it.

## Making changes

1. Fork the repo and create a branch off `main`.
2. Keep pull requests focused on one feature or fix at a time.
3. Add or update tests for any change to `src/utils/`.
4. Run `python -m pytest` and `ruff check` locally before pushing.
5. Write commit messages in the form `type: Short description` (e.g.
   `feat: Add seek support to the progress bar`, `fix: Correct octave
   folding for WWM notes`) — common types are `feat`, `fix`, `refactor`,
   `chore`, and `style`.
6. Open a pull request describing what changed and why, and how you tested
   it (screen recording/screenshots are appreciated for UI changes, since
   there's no automated GUI test suite to lean on).

## Project layout

See [CLAUDE.md](CLAUDE.md) for a full breakdown of the codebase layout and
how playback works internally — useful context before making non-trivial
changes.

## Reporting bugs / requesting features

Open a GitHub issue with steps to reproduce (for bugs) or the use case
you're trying to solve (for feature requests). For security issues, see
[SECURITY.md](SECURITY.md) instead of opening a public issue.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By
participating, you're expected to uphold it.
