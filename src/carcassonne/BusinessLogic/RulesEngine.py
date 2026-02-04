from carcassonne.IGameService import IGameService


class RulesEngine(IGameService):
    
    def __init__(self):
        self.tiles_dict = {
            'FFFF': ['m'], 'FFFR': ['m'], 'CFFF': ['void'], 'FCFC': ['f'], 'CFCF': ['c', 'b'],
            'CCCC': ['b'], 'FFCC': ['void'], 'CCFF': ['void', 'b'], 'CCCF': ['void', 'b'], 'CCCR': ['void', 'b'], 'FRFR': ['void'],
            'FFRR': ['void'], 'CRFR': ['void'], 'CFRR': ['void'], 'CRRF': ['void'], 'CCRR': ['void', 'b'], 'FRRR': ['void'], 'CRRR': ['void'],
            'RRRR': ['void'], 'FSRS': ['m'], 'FFSF': ['void'], 'FSFS': ['void'], 'FFSS': ['void'], 'CSCS': ['void'], 'CCSS': ['void'],
            'CSRS': ['void'],'RSRS': ['void'], 'RRSS': ['void']
        }

        self.direction_list = ['N', 'S', 'W', 'E']
    
    def placeTile(self, move): #ça marche pas encore sachant qu'il faut d'autres trucs implémentés mais voilà l'idée
        counter = 0
        if not isinstance(move, str):
            print("the move needs to be a str\n")
            return
        
        move_parts = move.split('/')
        if not 2 <= len(move_parts) <= 4:
            print("the move is invalid, are you sure you computed it right?\n")
            return
        if move_parts[counter] not in self.tiles_dict:
            print("the tile you try to play doesn't exist, are you sure you computed it right?")
            return
        
        counter += 1
        if (len(move_parts[counter]) == 1):
            if move_parts[counter] not in self.tiles_dict[move_parts[counter - 1]]:
                print("the tile you try to place doesn't have that center")
                return  
            counter += 1
        else :
            if 'void' not in self.tiles_dict[move_parts[counter - 1]]:
                print("the tile you try to place needs a center")
                return
            
        #assert(move_parts[counter][0] < gamestate.current_turn, "the tile you try to attach yours to has a invalid number")
        if move_parts[counter][1] not in self.direction_list:   
            print("the tile's side you try to attach yours on must be N, S, W or E")
            return      
        if not (0 <= int(move_parts[counter][2]) <= 3): 
            print("the rotation you apply to your tile must be between 0 and 3")
            return  
        
        counter += 1
        if (len(move_parts) == counter - 1):
            if move_parts[counter] not in (self.direction_list + ['C']):
                print("the tile's side you try to place a meeple on must be N, S, W, E or C")
                return
        #assert(gamestate.isLegalMove(move), "the move isn't valid")
        #jouer le move dans les structures
        print(move + " placed successfully.")
    
    def getGameStates(self):
        pass
    
    def placeMeeple(self, move):
        pass
        
    def playAI(self):
        pass
    