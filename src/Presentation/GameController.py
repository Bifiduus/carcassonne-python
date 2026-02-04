from carcassonne.IGameService import IGameService

class GameLoop():
    
    def __init__(self, game_service):
        self.game_service = game_service
        self.loop()
        
    def loop(self):
        while(True):
            cmd = input(">> ")

            cmd_parts = cmd.split(' ')
            if cmd_parts[0] == "play":
                self.game_service.placeTile(cmd_parts[1])
                
            