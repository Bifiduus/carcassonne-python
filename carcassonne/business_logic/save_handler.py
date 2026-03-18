from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.business_logic.game import Game


class SaveHandler:
    def __init__(self, game: "Game"):
        self.game = game

    def save_game_to_file(self, filename: str) -> int:
        if filename is None or filename.strip() == "":
            print("Error: Invalid filename.")
            return -1
        if not filename.endswith(".txt"):
            filename += ".txt"
        file = open(filename, "w")

        file.write("[Settings]\n")
        for key, value in self.game.get_game_configuration().items():
            file.write(f"{key}: {value}\n")

        file.write("\n")
        file.write("[GameState]\n")
        # + who is the current player, scores, etc.
        number_of_ai_players = self.game.get_number_of_ai_players()
        file.write(
            "NumberOfPlayers: "
            + str(len(self.game.players) - number_of_ai_players)
            + ","
            + str(number_of_ai_players)
            + "\n"
        )
        file.write(
            "PlayersOrder: ["
            + ", ".join(
                [f"{player_id} " for player_id in self.game.players_order]
            )
            + "]\n"
        )
        file.write(
            "GameScore: ["
            + ", ".join(
                [
                    f"{player.get_id()}: {player.get_score().score} "
                    for player in self.game.players.values()
                ]
            )
            + "]\n"
        )
        file.write("Seed: " + str(self.game.seed) + "\n")
        file.write("\n")
        file.write("[History]\n")
        moves_history = self.game.get_history()
        while moves_history is not None and len(moves_history) > 0:
            for player in range(self.game.get_number_of_players()):
                if moves_history:
                    move = moves_history.pop()
                    file.write(move + " ")
        file.write("\n")
        file.close()
        return 0

    def load_game_from_file(self, filename: str) -> int:
        if filename is None or filename.strip() == "":
            print("Error: Invalid filename.")
            return -1
        if not filename.endswith(".txt"):
            filename += ".txt"
        try:
            file = open(filename, "r")
        except OSError:
            print(f"Error: Could not open file {filename}")
            return -1
        # Clear current game state before loading a new one.
        self.game.start_load_game()

        lines = file.readlines()
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
            # Strip whitespace and remove inline comments (after '#').
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].rstrip()
            if not line:
                continue

            if line == "[Settings]":
                sections_parsed += 1
                settings_section = True
                game_state_section = False
                history_section = False
                settings_parsed = True
                continue
            elif line == "[GameState]":
                if not settings_section:
                    print(
                        "Warning: [Settings] section not found before "
                        "[GameState]."
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
                        "Warning: [GameState] section not found before "
                        "[History]."
                    )
                sections_parsed += 1
                settings_section = False
                game_state_section = False
                history_section = True
                history_parsed = True
                continue
            elif line == "":
                continue  # Skip empty lines
            print(line)
            if settings_section:
                # Parse settings and configure the game accordingly.
                # This is a placeholder for demonstration purposes.
                # Configuration of the game, shuffle algorithm and seed.
                print("Parsing settings: ", line)
            elif game_state_section:
                # Here you would parse the game state.
                # This is a placeholder for demonstration purposes.
                # Game scores and player order.
                print("Parsing game state: ", line)

                if line.startswith("NumberOfPlayers:"):
                    line = line.split("NumberOfPlayers:")[1].strip()
                    if line == "":
                        print("Warning: Number of players not specified.")
                        continue
                    number_of_players, number_of_ai_players = (
                        line.split(",") if "," in line else (line, "0")
                    )
                    human_players = int(number_of_players.strip())
                    ai_players = int(number_of_ai_players.strip())
                    total_players = human_players + ai_players
                    print(
                        "Total number of players specified: "
                        f"{total_players}."
                    )
                    min_players = self.game.get_minimum_number_of_players()
                    max_players = self.game.get_maximum_number_of_players()
                    if total_players > max_players:
                        print(
                            "Warning: Number of players should be between "
                            f"{min_players} and {max_players}."
                        )
                        continue
                    self.game.set_number_of_ai_players(ai_players)
                    print(f"Number of players set to {total_players}.")

                if line.startswith("PlayersOrder:"):
                    line = line.split("PlayersOrder:")[1].strip()
                    if line == "":
                        print("Warning: Players order not specified.")
                        continue
                    self.game.players_order = [
                        int(player_id.strip())
                        for player_id in line.strip("[]").split(",")
                    ]
                    print(f"Players order set to {self.game.players_order}.")

                if line.startswith("GameScore:"):
                    # Assuming the format is "GameScore: [Player1ID: 10,
                    # Player2ID: 20]"
                    line = line.split("GameScore:")[1].strip()
                    if line == "" or line == "[]":
                        print("Warning: No score yet.")
                        continue
                    line = line.split("[")[1].strip("]")
                    scores = line.split(",")
                    if len(scores) > len(self.game.players):
                        print("Warning: More scores than players.")
                    for score in scores:
                        playerID, points = score.split(":")
                        for player in self.game.players.values():
                            if player.get_id() == int(playerID.strip()):
                                player.score.set_points(int(points.strip()))
                                player_number = self.game.players_order.index(
                                    player.get_id()
                                )
                                print(
                                    f"Player number "
                                    f"{player_number} "
                                    f"({player.get_username().strip()}) has "
                                    f"{player.score.score} points."
                                )
                    game_score = True
                if line.startswith("Seed:"):
                    # Assuming the format is "Seed: the seed"
                    line = line.split("Seed:")[1].strip()
                    if line == "":
                        print("Warning: No seed.")
                        continue
                    self.game.seed = int(line)
                    self.game.shuffle_deck("fisher-yates", self.game.seed)
                    print(self.game.deck.tiles)

            elif history_section:
                if not game_score:
                    print(
                        "Warning: no game score found in [GameState] section."
                    )
                for player_move in reversed(line.strip(" ").split(" ")):
                    move = (
                        player_move.split(":")[1]
                        if ":" in player_move
                        else player_move
                    )
                    self.game.current_hand = move
                    if move != self.game.draw_tile():
                        print("The mode doesn't match the seed !")
                    # Assuming line is in the format "player_id:details"
                    self.game.play_move(move)

        if sections_parsed < 3:
            print("Warning: Not all sections were found in the file.")
            if not settings_parsed:
                print("Warning: [Settings] section missing.")
            if not game_state_parsed:
                print("Warning: [GameState] section missing.")
            if not history_parsed:
                print("Warning: [History] section missing.")
        file.close()
        return 0
