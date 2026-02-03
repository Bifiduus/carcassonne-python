from IGameService import IGameService

class GameService(IGameService):
    def placeTile(self, tile, position):
        print(f"Tuile {tile} placée en {position}")

    def placeMeeple(self, position):
        print(f"Meeple placé en {position}")

    def getGameStates(self):
        return {"turn": 5, "score": [12, 9]}

    def playAI(self):
        print("IA joue un coup")