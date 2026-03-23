class CommandsGame():
    def __init__(self, game):
        self.game = game

    def place_tile(self, tile, position):
        # Logic to place a tile on the board
        pass

    def place_meeple(self, meeple, position):
        # Logic to place a meeple on the board
        pass

    def end_turn(self):
        # Logic to end the current player's turn
        pass

    def provide_hint(self) -> str:
        from .ai_model import RandomPlayer
        from .ai_model import ExpectimaxPlayer

        timed_out_now = self.tick_blitz()
        if timed_out_now:
            return ""
        if not self._ensure_current_player_playable():
            return ""

        ai_player = self.get_current_player()
        print(f"AI Player {ai_player.get_username()} is thinking...")
        self.draw_tile()
        if self.current_hand is None:
            return ""
        model = None
        move = ""
        if self.ai_model == "random":
            model = RandomPlayer()
            move = model.random_move(self.current_hand, self)
            print(f"AI Player {ai_player.get_username()} chooses move: {move}")
        elif self.ai_model == "expectimax":
            model = ExpectimaxPlayer(self)
            eval, move = model.search(
                self,
                depth=model.depth_max,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
            print(
                f"AI Player {ai_player.get_username()} chooses move: {move} "
                f"with evaluation score: {eval}"
            )
        # print("main avant de jouer le coup" + self.current_hand)
        return move

    def shuffle_players_order(self) -> None:
        others = [player for player in self.players if player != 0]
        r.shuffle(others)
        self.players_order = [0] + others
