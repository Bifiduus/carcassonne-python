import configparser
import os
import json
import sys

from carcassonne.i18n import gettext as _

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".carcassonnerc")

DEFAULT_SETTINGS = {
    "verbose": False,
    "debug": False,
    "blitz": False,
    "contest": False,
    "time": 30,
    "river": False,
    "num_ai_players": 1,
    "ai_time": 5,
    "ai_mode": "minimax",
    "ai_minimax_depth": 80,
    "ai_minimax_scoring": "baseline",
    "ai_mcts_selection": "UCT",
    "contest_file": "",
    "file_keybinds": {
        "app.new": "n",
        "app.load": "l",
        "app.save": "s",
        "app.config": "comma",
        "app.info": "i",
        "app.quit": "q",
    },
    "game_keybinds": {
        "app.undo": "u",
        "app.redo": "r",
        "app.pause": "p",
        "app.hint": "h",
    },
}


class GameConfiguration:
    def __init__(self, overrides=None):
        self.settings = self.load_config()
        if overrides:
            self.settings.update(overrides)
        self._normalize_time_key()

    def _normalize_time_key(self):
        if "time" not in self.settings and "timeout" in self.settings:
            self.settings["time"] = self.settings["timeout"]
        self.settings.pop("timeout", None)

    def _write_config(self, config: configparser.ConfigParser):
        with open(CONFIG_PATH, "w") as f:
            config.write(f, space_around_delimiters=False)

    def create_default_config(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": "false",
            "debug": "false",
            "blitz": "false",
            "time": "30",
            "river": "false",
            "num_ai_players": "1",
            "ai_time": 5,
            "ai_mode": "minimax",
            "ai_minimax_depth": 83,
            "ai_minimax_scoring": "baseline",
            "ai_mcts_selection": "UCT",
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(DEFAULT_SETTINGS["file_keybinds"]),
            "game_keybinds": json.dumps(DEFAULT_SETTINGS["game_keybinds"]),
        }

        self._write_config(config)

    def load_config(self):
        config = configparser.ConfigParser()
        settings = DEFAULT_SETTINGS.copy()

        # Case 1: missing file -> create it
        if not os.path.exists(CONFIG_PATH):
            self.create_default_config()
            return settings

        # Case 2/3: file exists
        try:
            config.read(CONFIG_PATH)

            if "defaults" not in config:
                raise ValueError("Missing [defaults] section")

            if config.has_option("defaults", "verbose"):
                settings["verbose"] = config.getboolean("defaults", "verbose")
            if config.has_option("defaults", "debug"):
                settings["debug"] = config.getboolean("defaults", "debug")
            if config.has_option("defaults", "blitz"):
                settings["blitz"] = config.getboolean("defaults", "blitz")
            if config.has_option("defaults", "river"):
                settings["river"] = config.getboolean("defaults", "river")

            if config.has_option("defaults", "time"):
                settings["time"] = config.getint("defaults", "time")
            elif config.has_option("defaults", "timeout"):
                # backward compatibility with previous setting name
                settings["time"] = config.getint("defaults", "timeout")
            if config.has_option("defaults", "num_ai_players"):
                settings["num_ai_players"] = config.getint(
                    "defaults", "num_ai_players"
                )
            if config.has_option("defaults", "ai_time"):
                settings["ai_time"] = config.getint("defaults", "ai_time")
            if config.has_option("defaults", "ai_mode"):
                settings["ai_mode"] = config.get("defaults", "ai_mode")
            if config.has_option("defaults", "ai_minimax_depth"):
                settings["ai_minimax_depth"] = config.getint(
                    "defaults", "ai_minimax_depth"
                )
            if config.has_option("defaults", "ai_minimax_scoring"):
                settings["ai_minimax_scoring"] = config.get(
                    "defaults", "ai_minimax_scoring"
                )
            if config.has_option("defaults", "ai_mcts_selection"):
                settings["ai_mcts_selection"] = config.get(
                    "defaults", "ai_mcts_selection"
                )
            # `contest_file` is intentionally runtime-only so a stale path
            # cannot silently reactivate contest mode on the next launch.
            if "keybinds" in config:
                if config.has_option("keybinds", "file_keybinds"):
                    settings["file_keybinds"] = json.loads(
                        config.get("keybinds", "file_keybinds")
                    )
                if config.has_option("keybinds", "game_keybinds"):
                    settings["game_keybinds"] = json.loads(
                        config.get("keybinds", "game_keybinds")
                    )

        except Exception as e:
            print(_("Warning: invalid configuration file."), file=sys.stderr)
            print(f"   ({e})", file=sys.stderr)
            print(_("Starting with default options."), file=sys.stderr)

        return settings

    def save_config(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": str(self.settings["verbose"]).lower(),
            "debug": str(self.settings.get("debug", False)).lower(),
            "blitz": str(self.settings["blitz"]).lower(),
            "time": str(self.settings["time"]),
            "river": str(self.settings.get("river")).lower(),
            "num_ai_players": str(self.settings.get("num_ai_players", 1)),
            "ai_time": str(self.settings["ai_time"]),
            "ai_mode": str(self.settings["ai_mode"]),
            "ai_minimax_depth": str(self.settings["ai_minimax_depth"]),
            "ai_minimax_scoring": str(
                self.settings["ai_minimax_scoring"]
            ),
            "ai_mcts_selection": str(self.settings["ai_mcts_selection"]),
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(self.settings["file_keybinds"]),
            "game_keybinds": json.dumps(self.settings["game_keybinds"]),
        }

        self._write_config(config)

    def show_config(self):
        print(_("Current game configuration:"))
        for key, value in self.settings.items():
            print(f"  {key}: {value}")

    def get_setting(self):
        return self.settings.copy()

    def get_setting_value(self, key):
        return self.settings.get(key)
