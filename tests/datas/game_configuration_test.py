import configparser
import json
import os

import pytest
from carcassonne.datas.game_configuration import GameConfiguration


class TestGameConfiguration:
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
            "app.hint": "h",
        },
    }

    def test_default_configuration_creation(self):
        config = GameConfiguration()
        config.create_default_config()
        config.save_config()
        print(config.settings)

    def test_load_config(self):
        config = GameConfiguration()
        config.create_default_config()
        config.save_config()
        settings = config.load_config()
        print(settings)
        assert settings == self.DEFAULT_SETTINGS, "The loaded config doesn't match the expected one."
        config = GameConfiguration({"verbose": True})
        config.save_config()
        settings = config.load_config()
        assert settings["verbose"] != self.DEFAULT_SETTINGS["verbose"], "The loaded settings should not match the default one."

    def test_save_config(self):
        config = GameConfiguration({"blitz": True})
        with open(self.CONFIG_PATH, "r") as f:
            f.read(len(config.get_setting()))
