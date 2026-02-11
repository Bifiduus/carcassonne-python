import configparser
import os

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".carcassonnerc")

DEFAULT_SETTINGS = {
    "verbose": False,
    "blitz": False,
    "timeout": 30
}

class GameConfiguration:
    def __init__(self):
        self.settings = self.load_config()

    def create_default_config(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": "false",
            "blitz": "false",
            "timeout": "30"
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

        except Exception as e:
            print("⚠️  Avertissement : fichier de configuration invalide.")
            print(f"   ({e})")
            print("   Lancement avec les options par défaut.")
        
        return settings

    def show_config(self):
        print("Configuration actuelle du jeu:")
        for key, value in self.settings.items():
            print(f"  {key}: {value}")
