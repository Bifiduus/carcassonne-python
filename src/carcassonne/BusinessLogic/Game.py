"""from carcassonne.Datas import playHistory, undoHistory
from RulesEngine import currentPlayerIsHuman

def undo():
    if currentPlayerIsHuman():
        previousPlay = playHistory.pop()
        undoHistory.append(previousPlay)
        previousPlay = playHistory.pop()
        while isAIPlayer(previousPlay):
            undoHistory.append(previousPlay)
            previousPlay = playHistory.pop()
        playHistory.append(previousPlay)

def redo():
    if currentPlayerIsHuman():
        lastUnPlayedMove = undoHistory.pop()
        playHistory.append(lastUnPlayedMove)
        lastUnPlayedMove = undoHistory.pop()
        while isAIPlayer(lastUnPlayedMove):
            playHistory.append(lastUnPlayedMove)
            lastUnPlayedMove = undoHistory.pop()
        undoHistory.append(lastUnPlayedMove)

def printHistory():
    print('not implemented')
    printPlayHistory()
    printUndoHistory()
    # print all the history

def printPlayHistory():
    print('not implemented')

def printUndoHistory():
    print('not implemented')

def clearUndoHistory():
    undoHistory.clear()*"""