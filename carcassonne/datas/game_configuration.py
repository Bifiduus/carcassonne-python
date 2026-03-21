import configparser
import os
import json

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".carcassonnerc")

DEFAULT_SETTINGS = {
    "verbose": False,
    "blitz": False,
    "time": 30,
    "num_ai_players": 1,
    "ai_time": 5,
    "ai_mode": "minimax",
    "ai_minimax_depth": 80,
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

    def create_default_config(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": "false",
            "blitz": "false",
            "time": "30",
            "num_ai_players": "1",
            "ai_time": 5,
            "ai_mode": "minimax",
            "ai_minimax_depth": 83,
            "ai_mcts_selection": "UCT",
            "contest_file": ""
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(DEFAULT_SETTINGS["file_keybinds"]),
            "game_keybinds": json.dumps(DEFAULT_SETTINGS["game_keybinds"]),
        }

        with open(CONFIG_PATH, "w") as f:
            config.write(f)

    def load_config(self):
        config = configparser.ConfigParser()
        settings = DEFAULT_SETTINGS.copy()

        # Cas 1 : fichier absent → création
        if not os.path.exists(CONFIG_PATH):
            self.create_default_config()
            return settings

        # Cas 2 / 3 : fichier présent
        try:
            config.read(CONFIG_PATH)

            if "defaults" not in config:
                raise ValueError("Section [defaults] manquante")

            settings["verbose"] = config.getboolean("defaults", "verbose")
            settings["blitz"] = config.getboolean("defaults", "blitz")
            if config.has_option("defaults", "time"):
                settings["time"] = config.getint("defaults", "time")
            elif config.has_option("defaults", "timeout"):
                # backward compatibility with previous setting name
                settings["time"] = config.getint("defaults", "timeout")
            if config.has_option("defaults", "num_ai_players"):
                settings["num_ai_players"] = config.getint(
                    "defaults", "num_ai_players"
                )
            # optional contest file
            if config.has_option("defaults", "contest_file"):
                settings["contest_file"] = config.get(
                    "defaults", "contest_file"
                )

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
            print("⚠️  Avertissement : fichier de configuration invalide.")
            print(f"   ({e})")
            print("   Lancement avec les options par défaut.")

        return settings

    def save_config(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": str(self.settings["verbose"]).lower(),
            "blitz": str(self.settings["blitz"]).lower(),
            "time": str(self.settings["time"]),
            "num_ai_players": str(self.settings.get("num_ai_players", 1)),
            "ai_time": str(self.settings["ai_time"]),
            "ai_mode": str(self.settings["ai_mode"]),
            "ai_minimax_depth": str(self.settings["ai_minimax_depth"]),
            "ai_mcts_selection": str(self.settings["ai_mcts_selection"]),
            "contest_file": str(self.settings.get("contest_file", "")),
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(self.settings["file_keybinds"]),
            "game_keybinds": json.dumps(self.settings["game_keybinds"]),
        }

        with open(CONFIG_PATH, "w") as f:
            config.write(f)

    def show_config(self):
        print("Configuration actuelle du jeu:")
        for key, value in self.settings.items():
            print(f"  {key}: {value}")

    def get_setting(self):
        return self.settings.copy()
