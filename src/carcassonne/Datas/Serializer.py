"""This module defines the Serializer class, which provides methods for parsing move strings and building move strings from move records in the Carcassonne game. 
The Serializer class includes the parse_move function, which takes a move string and extracts the relevant information such as tile sides, target vertex, rotation, and meeple placement. 
It also includes the build_str function, which takes a MoveRecord object and constructs a move string that can be used to represent the move in the game history.
"""


def build_str(record):
    return f"{record.player_id}:{record.move_str};"
