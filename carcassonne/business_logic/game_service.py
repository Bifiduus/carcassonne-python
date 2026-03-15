"""Service layer wrapper around core game logic."""


class GameService:
    def __init__(self, game):
        self._game = game

    def place_tile(self, move):
        self._game.placeTile(move)

    def place_meeple(self, move):
        self._game.placeMeeple(move)

    def get_game_configuration(self):
        return self._game.getConfiguration()

    def play_ai(self):
        self._game.playAI()

    def get_board(self):
        return self._game.get_board()
