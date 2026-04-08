import configparser

from carcassonne.datas.game_configuration import (
    DEFAULT_SETTINGS,
    GameConfiguration,
)


def test_configuration_normalizes_legacy_timeout_key(monkeypatch) -> None:
    monkeypatch.setattr(
        GameConfiguration,
        "load_config",
        lambda self: {"timeout": 12, "verbose": True},
    )

    config = GameConfiguration()

    assert config.get_setting_value("time") == 12
    assert "timeout" not in config.settings
    assert config.get_setting_value("verbose") is True


def test_configuration_creates_default_file_when_missing(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / ".carcassonnerc"
    monkeypatch.setattr(
        "carcassonne.datas.game_configuration.CONFIG_PATH",
        str(config_path),
    )

    config = GameConfiguration()

    assert config_path.exists()
    assert "verbose=false" in config_path.read_text()
    assert config.get_setting_value("time") == DEFAULT_SETTINGS["time"]
    assert config.get_setting(
    )["file_keybinds"] == DEFAULT_SETTINGS["file_keybinds"]


def test_configuration_loads_existing_values_and_keybinds(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / ".carcassonnerc"
    monkeypatch.setattr(
        "carcassonne.datas.game_configuration.CONFIG_PATH",
        str(config_path),
    )

    parser = configparser.ConfigParser()
    parser["defaults"] = {
        "verbose": "true",
        "blitz": "true",
        "timeout": "9",
        "river": "true",
        "num_ai_players": "2",
        "ai_time": "11",
        "ai_mode": "random",
        "ai_minimax_depth": "4",
        "ai_minimax_scoring": "short_term",
        "ai_mcts_selection": "ML",
        "contest_file": "contest.txt",
    }
    parser["keybinds"] = {
        "file_keybinds": "{\"app.new\": \"x\"}",
        "game_keybinds": "{\"app.undo\": \"z\"}",
    }
    with config_path.open("w") as handle:
        parser.write(handle)

    config = GameConfiguration()

    assert config.get_setting_value("verbose") is True
    assert config.get_setting_value("blitz") is True
    assert config.get_setting_value("time") == 9
    assert config.get_setting_value("river") is True
    assert config.get_setting_value("num_ai_players") == 2
    assert config.get_setting_value("ai_time") == 11
    assert config.get_setting_value("ai_mode") == "random"
    assert config.get_setting_value("ai_minimax_depth") == 4
    assert config.get_setting_value("ai_minimax_scoring") == "short_term"
    assert config.get_setting_value("ai_mcts_selection") == "ML"
    assert config.get_setting_value("contest_file") == ""
    assert config.get_setting_value("file_keybinds") == {"app.new": "x"}
    assert config.get_setting_value("game_keybinds") == {"app.undo": "z"}


def test_configuration_falls_back_to_defaults_on_invalid_file(monkeypatch, tmp_path, capsys) -> None:
    config_path = tmp_path / ".carcassonnerc"
    monkeypatch.setattr(
        "carcassonne.datas.game_configuration.CONFIG_PATH",
        str(config_path),
    )
    config_path.write_text("[broken]\nvalue = yes\n")

    config = GameConfiguration()

    assert config.get_setting_value("time") == DEFAULT_SETTINGS["time"]
    assert "Warning" in capsys.readouterr().err


def test_configuration_save_show_and_getters_use_current_settings(monkeypatch, tmp_path, capsys) -> None:
    config_path = tmp_path / ".carcassonnerc"
    monkeypatch.setattr(
        "carcassonne.datas.game_configuration.CONFIG_PATH",
        str(config_path),
    )
    config = GameConfiguration(
        {
            "verbose": True,
            "blitz": True,
            "time": 15,
            "river": True,
            "num_ai_players": 3,
            "ai_time": 9,
            "ai_mode": "iterative",
            "ai_minimax_depth": 6,
            "ai_minimax_scoring": "disruption",
            "ai_mcts_selection": "ML",
            "contest_file": "position.txt",
        }
    )

    snapshot = config.get_setting()
    snapshot["time"] = 999

    config.save_config()
    config.show_config()

    assert config.get_setting_value("time") == 15
    output = capsys.readouterr().out
    assert ("Configuration actuelle du jeu" in output or "Current game configuration:" in output)

    parser = configparser.ConfigParser()
    parser.read(config_path)
    saved_text = config_path.read_text()
    assert "verbose=true" in saved_text
    assert "verbose = true" not in saved_text
    assert "num_ai_players=3" in saved_text
    assert parser.getboolean("defaults", "verbose") is True
    assert parser.getboolean("defaults", "blitz") is True
    assert parser.getint("defaults", "time") == 15
    assert parser.getboolean("defaults", "river") is True
    assert parser.getint("defaults", "num_ai_players") == 3
    assert parser.get("defaults", "ai_mode") == "iterative"
    assert not parser.has_option("defaults", "contest_file")
