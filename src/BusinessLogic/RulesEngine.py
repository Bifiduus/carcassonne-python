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
        assert isinstance(move, str), "the move needs to be a str\n"
        
        move_parts = move.split('/')
        assert 2 <= len(move_parts) <= 4, "the move is invalid, are you sure you computed it right?\n"
        assert move_parts[counter] in self.tiles_dict, "the tile you try to play doesn't exist, are you sure you computed it right?"
        
        counter += 1
        if (len(move_parts[counter]) == 1):
            assert move_parts[counter] in self.tiles_dict[move_parts[counter - 1]], "the tile you try to place doesn't have that center"
            counter += 1
        else :
            assert 'void' in self.tiles_dict[move_parts[counter - 1]], "the tile you try to place needs a center"
            
        #assert(move_parts[counter][0] < gamestate.current_turn, "the tile you try to attach yours to has a invalid number")
        assert move_parts[counter][1] in self.direction_list, "the tile's side you try to attach yours on must be N, S, W or E"
        assert 0 <= int(move_parts[counter][2]) <= 3, "the rotation you apply to your tile must be between 0 and 3"
        
        counter += 1
        if (len(move_parts) == counter - 1):
            assert move_parts[counter] in (self.direction_list + ['C']), "the tile's side you try to place a meeple on must be N, S, W, E or C"
        #assert(gamestate.isLegalMove(move), "the move isn't valid")
        #jouer le move dans les structures
    
    def getGameStates():
        pass
    
    def placeMeeple():
        pass
        
    def playAI():
        pass
    