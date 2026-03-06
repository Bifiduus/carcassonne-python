"""
Lists of commands that can be triggered from the GUI, and their handlers.
"""

"""
File menu commands:
"""

def on_new(game) -> None:
    game.start_new_game()
    game.shuffle_deck()



def on_load() -> None:
    print("to add load")

def on_save() -> None:
    print("to add save")

def on_config() -> None:
    print("to add config")

def on_info() -> None:
    print("to add info")

def on_quit(self) -> None:
    self.quit()


"""
Game menu commands:
"""

def on_undo(game) -> None:
    game.undo()
    print("to add undo")

def on_redo(game) -> None:
    game.redo()
    print("to add redo")

def on_pause() -> None:
    print("to add pause")

def on_hint() -> None:
    print("to add hint")