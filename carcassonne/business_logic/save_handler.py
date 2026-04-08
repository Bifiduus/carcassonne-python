from __future__ import annotations
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from carcassonne.i18n import gettext as _

if TYPE_CHECKING:
    from carcassonne.business_logic.game.game import Game


class SaveHandler:
    boolean_settings = [
        "verbose",
        "blitz",
        "contest",
        "river",
    ]
    integer_settings = [
        "time",
        "num_ai",
        "num_ai_players",
        "ai_time",
        "ai_minimax_depth",
    ]
    string_settings = [
        "ai_mode",
        "ai_minimax_scoring",
        "ai_mcts_selection",
        "contest_file",
    ]
    keybinds_settings = [
        "file_keybinds",
        "game_keybinds",
    ]

    def __init__(self, game: "Game"):
        self.game = game

    def serialize_value(self, value: Any) -> str:
        # This function would convert the current game state into a string
        # representation that can be saved to a file. This is a placeholder
        # implementation and should be expanded based on the actual game state
        # structure.
        if isinstance(value, dict):
            return "[" + ", ".join(
                f"{k}: {self.serialize_value(v)}" for k, v in value.items()
            ) + "]"
        return str(value)

    def save_game_to_file(self, filename: str) -> int:
        if filename is None or filename.strip() == "":
            print(_("Error: Invalid filename."), file=sys.stderr)
            return -1

        path = Path(filename)
        if path.name == "" or path.name in [".", ".."]:
            print(_("Error: Invalid filename."), file=sys.stderr)
            return -1
        if path.suffix != ".txt":
            path = path.with_suffix(".txt")
        parent = path.parent
        if parent and not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                print(
                    _("Error: Could not create directory {path}").format(
                        path=parent
                    ),
                    file=sys.stderr,
                )
                return -1
        try:
            with open(path, "w") as file:

                file.write("[Settings]\n")
                for key, value in self.game.get_game_configuration().items():
                    serialized_value = self.serialize_value(value)
                    file.write(f"{key}={serialized_value}\n")

                file.write("\n")
                file.write("[GameState]\n")
                # + who is the current player, scores, etc.
                number_of_ai_players = self.game.get_number_of_ai_players()
                file.write(
                    "NumberOfPlayers: "
                    + str(
                        len(self.game.game_data.players)
                        - number_of_ai_players
                    )
                    + ","
                    + str(number_of_ai_players)
                    + "\n"
                )
                file.write(
                    "PlayersOrder: ["
                    + ", ".join(
                        [
                            f"{player_id} "
                            for player_id in self.game.game_data.players_order
                        ]
                    )
                    + "]\n"
                )
                file.write(
                    "GameScore: ["
                    + ", ".join(
                        [
                            f"{player.get_id()}: {player.get_score().score} "
                            for player in self.game.game_data.players.values()
                        ]
                    )
                    + "]\n"
                )
                file.write("Seed: " + str(self.game.game_data.seed) + "\n")
                file.write("\n")
                file.write("[History]\n")
                moves_history = self.game.get_history()
                moves_history.reverse()
                while moves_history is not None and len(moves_history) > 0:
                    for player in range(self.game.get_number_of_players()):
                        if len(moves_history) == 0:
                            break
                        move = moves_history.pop()
                        file.write(move + " ")
                file.write("\n")
                file.close()
        except OSError:
            print(
                _("Error: Could not write to file {path}").format(path=path),
                file=sys.stderr,
            )
            return -1
        return 0

    def handle_keybinds_load(self, line: str, section: str):
        keybinds = line.split(
            "[")[1].strip("]")
        keybinds_dict = {}
        for keybind in keybinds.split(","):
            if ":" in keybind:
                action, key = keybind.split(":")
                keybinds_dict[action.strip()] = key.strip()
        self.game.set_game_configuration(section, keybinds_dict)

    def split_setting_line(self, line: str) -> tuple[str, str]:
        if "=" in line:
            return line.split("=", 1)
        if ":" in line:
            return line.split(":", 1)
        raise ValueError(f"Invalid setting line: {line}")

    def load_game_from_file(self, filename: str) -> int:
        if filename is None or filename.strip() == "":
            print(_("Error: Invalid filename."), file=sys.stderr)
            return -1

        path = Path(filename)
        if path.name == "" or path.name in {".", ".."}:
            print(_("Error: Invalid filename."), file=sys.stderr)
            return -1

        if path.suffix != ".txt":
            path = path.with_suffix(".txt")

        if path.is_dir():
            print(
                _("Error: {path} is a directory, not a file.").format(
                    path=path
                ),
                file=sys.stderr,
            )
            return -1

        try:
            with path.open("r") as file:
                lines = file.readlines()
        except OSError:
            print(
                _("Error: Could not open file {path}").format(path=path),
                file=sys.stderr,
            )
            return -1

        # Clear current game state before loading a new one.
        self.game.start_load_game()
        settings_section = False
        game_state_section = False
        history_section = False
        commentary = False
        settings_parsed = False
        game_state_parsed = False
        history_parsed = False
        commentary = False
        game_score = False
        sections_parsed = 0
        for line in lines:
            # Remove comments and strip whitespace
            line = line.strip().split("#")[0]

            # Handle cases where comments are inline with data
            if line.find("{") != -1 and line.find("}") == -1:
                line1 = line.split("{")[0]
                line2 = line.split("{")[1]
                line = line1 + line2

            if line.find("{") != -1:
                line = line.split("{")[0]
                commentary = True
                continue
            if line.find("}") != -1:
                line = line.split("}")[1]
                commentary = False
            if commentary:
                continue

            if line.lower() == "[settings]":
                sections_parsed += 1
                settings_section = True
                game_state_section = False
                history_section = False
                settings_parsed = True
                continue
            elif line == "[GameState]":
                if not settings_section:
                    print(
                        _(
                            "Warning: [Settings] section not found before "
                            "[GameState]."
                        )
                    )
                sections_parsed += 1
                settings_section = False
                game_state_section = True
                history_section = False
                game_state_parsed = True
                continue
            elif line == "[History]":
                if not game_state_section:
                    print(
                        _(
                            "Warning: [GameState] section not found before "
                            "[History]."
                        )
                    )
                sections_parsed += 1
                settings_section = False
                game_state_section = False
                history_section = True
                history_parsed = True
                continue
            elif line == "":
                continue  # Skip empty lines
            if settings_section:
                # Parse settings and configure the game accordingly.
                # This is a placeholder for demonstration purposes.
                # Configuration of the game, shuffle algorithm and seed.
                try:
                    setting, value = self.split_setting_line(line)
                except ValueError:
                    print(
                        _("Warning: Invalid setting line '{line}'.").format(
                            line=line
                        )
                    )
                    continue
                if setting.strip() in self.keybinds_settings:
                    self.handle_keybinds_load(value, setting.strip())
                elif setting.strip() in self.boolean_settings:
                    self.game.set_game_configuration(
                        setting.strip(), value.strip().lower() == "true"
                    )
                elif setting.strip() in self.integer_settings:
                    self.game.set_game_configuration(
                        setting.strip(), int(value.strip())
                    )
                elif setting.strip() in self.string_settings:
                    self.game.set_game_configuration(
                        setting.strip(), value.strip()
                    )
            elif game_state_section:
                # Here you would parse the game state.
                # This is a placeholder for demonstration purposes.
                # Game scores and player order.

                if line.startswith("NumberOfPlayers:"):
                    line = line.split("NumberOfPlayers:")[1].strip()
                    if line == "":
                        print(
                            _("Warning: Number of players not specified."),
                            file=sys.stderr,
                        )
                        continue
                    number_of_players, number_of_ai_players = (
                        line.split(",") if "," in line else (line, "0")
                    )
                    human_players = int(number_of_players.strip())
                    ai_players = int(number_of_ai_players.strip())
                    total_players = human_players + ai_players
                    min_players = self.game.get_minimum_number_of_players()
                    max_players = self.game.get_maximum_number_of_players()
                    if total_players > max_players:
                        print(
                            _(
                                "Warning: Number of players should be "
                                "between {min_players} and {max_players}."
                            ).format(
                                min_players=min_players,
                                max_players=max_players,
                            ),
                            file=sys.stderr,
                        )
                        continue
                    self.game.set_number_of_ai_players(ai_players)

                if line.startswith("PlayersOrder:"):
                    line = line.split("PlayersOrder:")[1].strip()
                    if line == "":
                        print(
                            _("Warning: Players order not specified."),
                            file=sys.stderr,
                        )
                        continue
                    self.game.game_data.players_order = [
                        int(player_id.strip())
                        for player_id in line.strip("[]").split(",")
                    ]

                if line.startswith("GameScore:"):
                    # Assuming the format is "GameScore: [Player1ID: 10,
                    # Player2ID: 20]"
                    line = line.split("GameScore:")[1].strip()
                    if line == "" or line == "[]":
                        print(_("Warning: No score yet."), file=sys.stderr)
                        continue
                    line = line.split("[")[1].strip("]")
                    scores = line.split(",")
                    if len(scores) > len(self.game.game_data.players):
                        print(
                            _("Warning: More scores than players."),
                            file=sys.stderr,
                        )
                    for score in scores:
                        playerID, points = score.split(":")
                        for player in self.game.game_data.players.values():
                            if player.get_id() == int(playerID.strip()):
                                player.score.set_points(int(points.strip()))
                    game_score = True
                if line.startswith("Seed:"):
                    # Assuming the format is "Seed: the seed"
                    line = line.split("Seed:")[1].strip()
                    game_data = self.game.game_data
                    if line == "" or line.lower() == "none":
                        print(_("Warning: No seed."), file=sys.stderr)
                        game_data.seed = None
                        game_data.initialize_starting_tile_based_on_config()
                        continue
                    game_data.seed = int(line)
                    game_data.initialize_starting_tile_based_on_config()
                    self.game.shuffle_deck("fisher-yates", game_data.seed)
                    if game_data.game_configuration.get_setting_value("river"):
                        self.game.river_manager.initialize_river()

            elif history_section:
                if not game_score:
                    print(
                        _(
                            "Warning: no game score found in [GameState] "
                            "section."
                        ),
                        file=sys.stderr,
                    )
                for player_move in line.strip(" ").split(" "):
                    move = (
                        player_move.split(":")[1]
                        if ":" in player_move
                        else player_move
                    ).removesuffix(";")
                    tile = self.game.game_data.extract_tile_code(move)
                    self.game.game_data.current_hand = tile
                    if tile != self.game.draw_tile():
                        print(
                            _("The move does not match the seed."),
                            file=sys.stderr,
                        )
                    # Assuming line is in the format "player_id:details"
                    if not self.game.play_move(move):
                        print(
                            _("Failed to play move: {move}").format(
                                move=move
                            ),
                            file=sys.stderr,
                        )

        if sections_parsed < 3:
            print(
                _("Warning: Not all sections were found in the file."),
                file=sys.stderr,
            )
            if not settings_parsed:
                print(
                    _("Warning: [Settings] section missing."),
                    file=sys.stderr,
                )
            if not game_state_parsed:
                print(
                    _("Warning: [GameState] section missing."),
                    file=sys.stderr,
                )
            if not history_parsed:
                print(
                    _("Warning: [History] section missing."),
                    file=sys.stderr,
                )
        file.close()
        return 0
