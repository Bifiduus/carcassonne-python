from carcassonne.BusinessLogic.ScoreManager import PlayerScore


class Player():
     
    id : int
    name: str
    score : PlayerScore
    color: str
    meeples: int
    
    def __init__(self, id: int, name: str, color: str):
        self.id = id
        self.name = name
        self.color = color
        self.score = PlayerScore(id)
        self.meeples = 7

    def __str__(self):
        return f"{self.name} ({self.color}) - Score: {self.score}, Meeples: {self.meeples}"
    
    def remove_meeple(self) -> None:
        if self.meeples > 0:
            self.meeples -= 1
        else:
            print(f"{self.name} has no more meeples to place.")
            
    def add_meeple(self) -> None:
        self.meeples += 1