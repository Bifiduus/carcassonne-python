from pathlib import Path
import pytest


from carcassonne.business_logic.save_handler import SaveHandler


class DummyScore:
    def __init__(self, score: int = 0) -> None:
        self.score = score

    def set_points(self, points: int) -> None:
        self.score = points


class DummyPlayer:
    def __init__(self, player_id: int, score: int = 0) -> None:
        self.player_id = player_id
        self.score = DummyScore(score)

    def get_id(self) -> int:
        return self.player_id

    def get_score(self) -> DummyScore:
        return self.score


class DummyGameData:
    def __init__(self):
        self.players = {
            0: DummyPlayer(0, 12),
            1: DummyPlayer(1, 5),
            2: DummyPlayer(2, 9),
        }
        self.players_order = [2, 0, 1]
        self.seed = 4242
        self.current_hand = None
        self.game_configuration = type('GameConfiguration', (), {
            'get_setting_value': lambda self, key: False
        })()

    def extract_tile_code(self, move):
        return move.split("/")[0]

    def initialize_starting_tile_based_on_config(self):
        pass


class DummyGame:
    def __init__(self) -> None:
        self.config = {
            "verbose": True,
            "time": 30,
            "ai_mode": "random",
            "file_keybinds": {"save": "s", "quit": "q"},
        }
        self.game_data = DummyGameData()
        self.set_config_calls: list[tuple[str, object]] = []
        self.set_ai_calls: list[int] = []
        self.start_load_calls = 0
        self.shuffle_calls: list[tuple[str, int]] = []
        self.played_moves: list[str] = []
        self.draw_mismatch = False
        self.river_manager = type('RiverManager', (), {
            'initialize_river': lambda: None
        })()

    def get_game_configuration(self):
        return dict(self.config)

    def get_number_of_ai_players(self) -> int:
        return 1

    def get_history(self):
        return ["0:CFFF/0N0;", "1:FFFF/m/1E0;"]

    def get_number_of_players(self) -> int:
        return len(self.game_data.players)

    def set_game_configuration(self, key: str, value) -> None:
        self.set_config_calls.append((key, value))

    def start_load_game(self) -> None:
        self.start_load_calls += 1

    def get_minimum_number_of_players(self) -> int:
        return 2

    def get_maximum_number_of_players(self) -> int:
        return 5

    def set_number_of_ai_players(self, ai_players: int) -> None:
        self.set_ai_calls.append(ai_players)

    def shuffle_deck(self, algo: str, seed: int) -> None:
        self.shuffle_calls.append((algo, seed))

    def draw_tile(self) -> str:
        if self.draw_mismatch:
            return "OTHER"
        return self.game_data.current_hand

    def play_move(self, move: str) -> None:
        self.played_moves.append(move)


def test_save_handler_serialize_and_invalid_filenames(capsys) -> None:
    game = DummyGame()
    handler = SaveHandler(game)

    assert handler.serialize_value(
        {"a": 1, "b": {"c": True}}) == "[a: 1, b: [c: True]]"
    assert handler.save_game_to_file("") == -1
    assert handler.load_game_from_file("") == -1
    assert handler.load_game_from_file("missing-file") == -1

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Error: Invalid filename." in output
    assert "Error: Could not open file missing-file.txt" in output


def test_save_game_to_file_writes_settings_state_and_history(tmp_path: Path) -> None:
    game = DummyGame()
    handler = SaveHandler(game)
    filename = tmp_path / "saved_game"

    assert handler.save_game_to_file(str(filename)) == 0

    content = (tmp_path / "saved_game.txt").read_text()

    assert "[Settings]" in content
    assert "verbose=True" in content
    assert "file_keybinds=[save: s, quit: q]" in content
    assert "[GameState]" in content
    assert "NumberOfPlayers: 2,1" in content
    assert "PlayersOrder: [2 , 0 , 1 ]" in content
    assert "GameScore: [0: 12 , 1: 5 , 2: 9 ]" in content
    assert "Seed: 4242" in content
    assert "[History]" in content
    assert "0:CFFF/0N0; 1:FFFF/m/1E0;" in content


def test_load_game_from_file_parses_sections_and_replays_moves(tmp_path: Path) -> None:
    game = DummyGame()
    handler = SaveHandler(game)
    save_file = tmp_path / "roundtrip.txt"
    save_file.write_text(
        "\n".join(
            [
                "[Settings]",
                "verbose=True",
                "time=25",
                "ai_mode=minimax",
                "file_keybinds=[save: s, quit: q]",
                "contest_file=contest.txt",
                "",
                "[GameState]",
                "NumberOfPlayers: 2,1",
                "PlayersOrder: [2, 1, 0]",
                "GameScore: [0: 5, 1: 8, 2: 13]",
                "Seed: 1234",
                "",
                "[History]",
                "0:CFFF/0N0; 1:FFFF/m/1E0;",
            ]
        )
    )

    assert handler.load_game_from_file(str(save_file)) == 0

    assert game.start_load_calls == 1
    assert ("verbose", True) in game.set_config_calls
    assert ("time", 25) in game.set_config_calls
    assert ("ai_mode", "minimax") in game.set_config_calls
    assert ("contest_file", "contest.txt") in game.set_config_calls
    assert ("file_keybinds", {"save": "s", "quit": "q"}
            ) in game.set_config_calls
    assert game.set_ai_calls == [1]
    assert game.game_data.players_order == [2, 1, 0]
    assert game.game_data.players[0].score.score == 5
    assert game.game_data.players[1].score.score == 8
    assert game.game_data.players[2].score.score == 13
    assert game.game_data.seed == 1234
    assert game.shuffle_calls == [("fisher-yates", 1234)]
    assert game.played_moves == ["CFFF/0N0", "FFFF/m/1E0"]


def test_load_game_from_file_accepts_legacy_colon_settings(tmp_path: Path) -> None:
    game = DummyGame()
    handler = SaveHandler(game)
    save_file = tmp_path / "legacy_settings.txt"
    save_file.write_text(
        "\n".join(
            [
                "[settings]",
                "verbose: True",
                "time: 25",
                "ai_mode: minimax",
                "file_keybinds: [save: s, quit: q]",
                "contest_file: contest.txt",
                "",
                "[GameState]",
                "NumberOfPlayers: 2,1",
                "PlayersOrder: [2, 1, 0]",
                "GameScore: [0: 5, 1: 8, 2: 13]",
                "Seed: 1234",
                "",
                "[History]",
                "0:CFFF/0N0; 1:FFFF/m/1E0;",
            ]
        )
    )

    assert handler.load_game_from_file(str(save_file)) == 0

    assert ("verbose", True) in game.set_config_calls
    assert ("time", 25) in game.set_config_calls
    assert ("ai_mode", "minimax") in game.set_config_calls
    assert ("contest_file", "contest.txt") in game.set_config_calls
    assert ("file_keybinds", {"save": "s", "quit": "q"}
            ) in game.set_config_calls


def test_load_game_from_file_warns_on_invalid_sections_and_seed_mismatch(
    tmp_path: Path, capsys
) -> None:
    game = DummyGame()
    game.draw_mismatch = True
    handler = SaveHandler(game)
    save_file = tmp_path / "warnings.txt"
    save_file.write_text(
        "\n".join(
            [
                "[GameState]",
                "NumberOfPlayers: 9,0",
                "PlayersOrder:",
                "GameScore: []",
                "Seed:",
                "[History]",
                "0:CFFF/0N0",
            ]
        )
    )

    assert handler.load_game_from_file(str(save_file)) == 0

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Warning: [Settings] section not found before [GameState]." in output
    assert "Warning: Number of players should be between 2 and 5." in output
    assert "Warning: Players order not specified." in output
    assert "Warning: No score yet." in output
    assert "Warning: No seed." in output
    assert "Warning: no game score found in [GameState] section." in output
    assert ("The move doesn't match the seed !" in output or "The move does not match the seed." in output)
    assert "Warning: Not all sections were found in the file." in output
    assert "Warning: [Settings] section missing." in output


def test_load_game_from_file_accepts_none_seed(tmp_path: Path) -> None:
    game = DummyGame()
    handler = SaveHandler(game)
    save_file = tmp_path / "none_seed.txt"
    save_file.write_text(
        "\n".join(
            [
                "[Settings]",
                "verbose=True",
                "",
                "[GameState]",
                "NumberOfPlayers: 2,1",
                "PlayersOrder: [2, 1, 0]",
                "GameScore: [0: 5, 1: 8, 2: 13]",
                "Seed: None",
                "",
                "[History]",
            ]
        )
    )

    assert handler.load_game_from_file(str(save_file)) == 0
    assert game.game_data.seed is None
    assert game.shuffle_calls == []


def test_split_setting_line_supports_equal_and_colon_and_rejects_invalid() -> None:
    handler = SaveHandler(DummyGame())

    assert handler.split_setting_line("time=30") == ["time", "30"]
    assert handler.split_setting_line("time:30") == ["time", "30"]

    with pytest.raises(ValueError):
        handler.split_setting_line("invalid-setting-line")


@pytest.mark.parametrize(
    ("value", "setting", "expected_ok"),
    [
        (-1, "time", False),
        (61, "time", False),
        (5, "num_ai_players", False),
        (11, "ai_time", False),
        (10, "time", True),
        (4, "num_ai_players", True),
        (10, "ai_time", True),
    ],
)
def test_check_integer_limits_validates_ranges(
    value: int,
    setting: str,
    expected_ok: bool,
    capsys,
) -> None:
    handler = SaveHandler(DummyGame())

    assert handler.check_integer_limits(value, setting) is expected_ok

    captured = capsys.readouterr()
    output = captured.out + captured.err
    if expected_ok:
        assert "Error:" not in output
    else:
        assert "Error:" in output


def test_print_missing_settings_only_outputs_when_non_empty(capsys) -> None:
    handler = SaveHandler(DummyGame())

    handler._print_missing_settings("boolean", set())
    assert capsys.readouterr().err == ""

    handler._print_missing_settings("integer", {"time"})
    assert "Missing integer settings" in capsys.readouterr().err


def test_load_game_from_file_rejects_directory_path(tmp_path: Path, capsys) -> None:
    handler = SaveHandler(DummyGame())
    directory_path = tmp_path / "as_directory.txt"
    directory_path.mkdir()

    result = handler.load_game_from_file(str(directory_path))

    assert result == -1
    assert "is a directory, not a file" in (capsys.readouterr().err)


def test_load_game_from_file_reports_setting_parse_and_validation_errors(
    tmp_path: Path,
    capsys,
) -> None:
    class StrictGame(DummyGame):
        def set_game_configuration(self, key: str, value) -> None:
            if key == "blitz":
                raise RuntimeError("boom")
            super().set_game_configuration(key, value)

    game = StrictGame()
    handler = SaveHandler(game)
    save_file = tmp_path / "settings_errors.txt"
    save_file.write_text(
        "\n".join(
            [
                "[Settings]",
                "bad_line_without_separator",
                "file_keybinds=[broken-format",
                "blitz=True",
                "time=abc",
                "ai_mode=",
                "unknown_setting=42",
                "",
                "[GameState]",
                "NumberOfPlayers: 2,1",
                "PlayersOrder: [0, 1, 2]",
                "GameScore: [0: 1, 1: 2, 2: 3]",
                "Seed: 0",
                "",
                "[History]",
            ]
        )
    )

    assert handler.load_game_from_file(str(save_file)) == 0
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Warning: Invalid setting line" in output
    assert "Error: Missing required keybinds in file_keybinds" in output
    assert "Error: Invalid boolean value for blitz" in output
    assert "Error: Invalid integer value for time" in output
    assert "Error: Empty string value for ai_mode" in output
    assert "Warning: Unknown setting 'unknown_setting'." in output
