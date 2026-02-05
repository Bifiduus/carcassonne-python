from carcassonne.Datas.GameRepository import GameRepository
game_repository = GameRepository()
play_history = game_repository.playHistory
undo_history = game_repository.undoHistory
from .AIModel import is_ai_player

def undo(engine):
    if engine.current_player_is_human() and play_history:
        previousPlay = play_history.pop()
        undo_history.append(previousPlay)
        while play_history and is_ai_player(play_history[-1]):
            previousPlay = play_history.pop()
            undo_history.append(previousPlay)

def redo(engine):
    if engine.current_player_is_human() and undo_history:
        lastUnPlayedMove = undo_history.pop()
        play_history.append(lastUnPlayedMove)
        while undo_history and is_ai_player(undo_history[-1]):
            lastUnPlayedMove = undo_history.pop()
            play_history.append(lastUnPlayedMove)

def print_history():
    print('not implemented')
    print_play_history()
    print_undo_history()
    # print all the history

def print_play_history():
    print("Play history:")
    print(play_history)

def print_undo_history():
    print("Undo history:")
    print(undo_history)

def clear_undo_history():
    undo_history.clear()
