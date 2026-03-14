import configparser
import os
import json

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".carcassonnerc")

DEFAULT_SETTINGS = {
    "verbose": False,
    "blitz": False,
    "timeout": 30,
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
        "app.hint": "h"
    }
}


class GameConfiguration:
    def __init__(self, overrides=None):
        self.settings = self.load_config()
        if overrides:
            self.settings.update(overrides)

    def create_default_config(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": "false",
            "blitz": "false",
            "timeout": "30",
            "contest_file": ""
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(DEFAULT_SETTINGS["file_keybinds"]),
            "game_keybinds": json.dumps(DEFAULT_SETTINGS["game_keybinds"])
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
            settings["timeout"] = config.getint("defaults", "timeout")
            # optional contest file
            if config.has_option("defaults", "contest_file"):
                settings["contest_file"] = config.get(
                    "defaults", "contest_file")

            if "keybinds" in config:
                if config.has_option("keybinds", "file_keybinds"):
                    settings["file_keybinds"] = json.loads(
                        config.get("keybinds", "file_keybinds"))
                if config.has_option("keybinds", "game_keybinds"):
                    settings["game_keybinds"] = json.loads(
                        config.get("keybinds", "game_keybinds"))

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
            "timeout": str(self.settings["timeout"]),
            "contest_file": str(self.settings.get("contest_file", ""))
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(self.settings["file_keybinds"]),
            "game_keybinds": json.dumps(self.settings["game_keybinds"])
        }

        with open(CONFIG_PATH, "w") as f:
            config.write(f)

    def show_config(self):
        print("Configuration actuelle du jeu:")
        for key, value in self.settings.items():
            print(f"  {key}: {value}")

    def get_setting(self):
        return self.settings.copy()
