"""
Lists of commands that can be triggered from the GUI, and their handlers.
"""

"""
File menu commands:
"""

def on_new(game):
    game.start_new_game()
    game.shuffle_deck()



def on_load():
    print("to add load")

def on_save():
    print("to add save")

def on_config():
    print("to add config")

def on_info():
    print("to add info")

def on_quit(self):
    self.quit()


"""
Game menu commands:
"""

def on_undo(game):
    game.undo()
    print("to add undo")

def on_redo(game):
    game.redo()
    print("to add redo")

def on_pause():
    print("to add pause")

def on_hint():
    print("to add hint")