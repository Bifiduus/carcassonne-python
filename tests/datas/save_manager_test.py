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


class DummyGame:
    def __init__(self) -> None:
        self.config = {
            "verbose": True,
            "time": 30,
            "ai_mode": "random",
            "file_keybinds": {"save": "s", "quit": "q"},
        }
        game_data_type = type(
            "GameData",
            (),
            {
                "extract_tile_code": staticmethod(
                    lambda move: move.split("/", 1)[0]
                ),
            },
        )
        self.game_data = type(
            "DummyGameData",
            (game_data_type,),
            {
                "players": {
                    0: DummyPlayer(0, 12),
                    1: DummyPlayer(1, 5),
                    2: DummyPlayer(2, 9),
                },
                "players_order": [2, 0, 1],
                "seed": 4242,
                "current_hand": None,
            },
        )()
        self.set_config_calls: list[tuple[str, object]] = []
        self.set_ai_calls: list[int] = []
        self.start_load_calls = 0
        self.shuffle_calls: list[tuple[str, int]] = []
        self.played_moves: list[str] = []
        self.draw_mismatch = False

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

    assert handler.serialize_value({"a": 1, "b": {"c": True}}) == "[a: 1, b: [c: True]]"
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
                "verbose=true",
                "time=25",
                "ai_mode=minimax",
                "file_keybinds=[save: s, quit: q]",
                "contest_file=contest.txt # inline comment",
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
    assert ("file_keybinds", {"save": "s", "quit": "q"}) in game.set_config_calls
    assert game.set_ai_calls == [1]
    assert game.game_data.players_order == [2, 1, 0]
    assert game.game_data.players[0].score.score == 5
    assert game.game_data.players[1].score.score == 8
    assert game.game_data.players[2].score.score == 13
    assert game.game_data.seed == 1234
    assert game.shuffle_calls == [("fisher-yates", 1234)]
    assert game.played_moves == ["CFFF/0N0", "FFFF/m/1E0"]


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
    assert "The move doesn't match the seed !" in output
    assert "Warning: Not all sections were found in the file." in output
    assert "Warning: [Settings] section missing." in output
