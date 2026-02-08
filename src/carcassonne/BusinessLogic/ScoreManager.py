class PlayerScore():
    score: int
    
    def __init__(self):
        self.score = 0
        
    def add_score(self, score: int) -> None:
        self.score += score

class ScoreManager():
    def __init__(self):
        pass
    
    def calculate_score(self, terrain_type: str, size: int) -> int:
        #TODO
        return 0
            
class EndGameScore():
    
    players_score: list[PlayerScore]
    
    def __init__(self, players_score: list[PlayerScore]):
        self.players_score = players_score
    
    def add_final_scores(self) -> None:
        for player_score in self.players_score:
            #TODO
            pass