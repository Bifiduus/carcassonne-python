

class GameService():
    def __init__(self, game):
        self._game = game

    def placeTile(self, move):
        self._game.placeTile(move)

    def placeMeeple(self, move):
        self._game.placeMeeple(move)

    def getGameConfiguration(self):
        return self._game.getConfiguration()

    def playAI(self):
        self._game.playAI()

    def get_board(self):
        return self._game.get_board()
