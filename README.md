# Carcassonne Python

Python implementation of the Carcassonne board game, with both a command-line
interface and a GTK4 graphical interface.

## Overview

This project provides a playable version of Carcassonne with several game and
runtime modes:

- CLI and GTK4 GUI frontends
- Configurable AI opponents: `random`, `minimax`, `iterative`, `mcts`
- Optional ML-assisted MCTS selection
- Blitz mode and river mode
- Save/load support for game states in `.txt` format
- Contest mode for automated move generation
- Client/server components for multiplayer-related workflows

## Requirements

- Python `>= 3.10`
- `pip`
- For GUI mode: GTK4 + PyGObject

Debian/Ubuntu example for GUI dependencies:

```bash
sudo apt install python3-gi gir1.2-gtk-4.0
```

If you only use CLI, tests, or contest mode, the GUI system packages are not
required.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

This installs the package defined in [pyproject.toml](pyproject.toml) together
with the Python dependencies currently declared by the project.

## Quick Start

Show CLI help:

```bash
python3 -m carcassonne --help
```

Start a local game in CLI mode:

```bash
python3 -m carcassonne
```

Start the GTK GUI:

```bash
python3 -m carcassonne --gui
```

Start a 4-player game with river mode enabled:

```bash
python3 -m carcassonne --players 4 --river
```

Use a specific AI strategy and time budget:

```bash
python3 -m carcassonne --ai-mode mcts --ai-time 10
```

Enable blitz mode with a 15-minute limit:

```bash
python3 -m carcassonne --blitz --time 15
```

Load a saved game:

```bash
python3 -m carcassonne --file save.txt
```

Run contest mode on a saved position:

```bash
python3 -m carcassonne --contest --file position.txt
```

Start the server in daemon mode:

```bash
python3 -m carcassonne --daemon
```

## Configuration

User configuration is stored in:

```text
~/.carcassonnerc
```

The configuration file is created automatically on first launch and stores
default options and keybindings.

## Development

Run the test suite:

```bash
python3 -m pytest
```

Run tests with coverage:

```bash
python3 -m pytest --cov=carcassonne --cov-report=html --cov-report=term
```

Generate the Sphinx documentation:

```bash
make -C docs html PYTHON=python3
```

Generated documentation will be written to:

```text
docs/build/html/
```

## Repository Structure

```text
carcassonne/
  business_logic/    Core game logic, AI, save/load, networking
  datas/             Data models, configuration, deck, persistence helpers
  presentation/cli/  Command-line interface
  presentation/gui/  GTK4 interface
tests/               Automated tests
docs/                Sphinx documentation
```

## Contributors

- Clément SIMON
- Maxence SALIN
- Loic THIN
- Anthony BEAUVIEUX
- Tony HUANG

## License

The package metadata currently declares `BSD-2-Clause` in
[pyproject.toml](pyproject.toml). The repository should keep
[LICENSE.md](LICENSE.md) aligned with that declaration.
