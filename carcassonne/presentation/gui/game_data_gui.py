from carcassonne.presentation.gui import commands_handler_gui
from carcassonne.presentation.gui.tiles_view import TilesView
from carcassonne.i18n import gettext as _
from gi.repository import GLib


class GameDataGui:
    def __init__(self, game, client_service, server_service):
        self.game = game
        self.client = client_service
        self.server = server_service
        self.nb_tiles = 0  # used to give each drawn tile a unique id
        self.current_tile: TilesView | None = None
        self.current_orientation = 0
        self.board_view = None  # set later by Gui
        self.gui = None
        self.is_dragging = False
        self.hint_tile = None  # hint tile data for transparent display
        self.error = None
        self.highlight_contest_move = False  # highlight last move in contest mode
        self.contest_move_str = None  # store the contest move for display

    @staticmethod
    def _get_component_display_name(component_name: str) -> str:
        """Convert internal component names to user-friendly display names."""
        if component_name.startswith("F"):
            return _("field {name}").format(name=component_name)
        elif component_name.startswith("C"):
            return _("city {name}").format(name=component_name)
        elif component_name.startswith("R"):
            return _("road {name}").format(name=component_name)
        elif component_name.startswith("M"):
            return _("monastery {name}").format(name=component_name)
        else:
            return component_name

    def game_configuration(self):
        return self.game.get_game_configuration()

    def new_game(self, players_order, seed):
        """Helper that starts a new game and resets GUI state.
        ``players_order`` and ``seed`` are simply forwarded to the underlying
        game service (``Game.start_new_game``) so callers such as
        :class:`OptionsView` can influence how the match is initialised.
        """
        # Adjust the number of AI players based on current configuration
        # This respects the 3-tier architecture:
        # - Presentation reads config and calls business logic
        # - Business logic manages the adjustment
        # - Data layer stores the players
        config = self.game.get_game_configuration()
        num_ai = config.get("num_ai_players", 1)
        self.game.adjust_number_of_ai_players(num_ai)

        # the command handler already implements the basic behaviour but it
        # doesn't accept any of the extra keywords, so call the service
        # directly.  ``Game.start_new_game`` is idempotent with respect to
        # shuffling, so we don't need to double‑shuffle here.
        self.game.start_new_game(players_order, seed)
        self.reset()

    def run_contest_gui(self, contest_file: str) -> tuple[bool, str]:
        """Execute contest mode from GUI and return (success, result_or_error).

        Loads a game position from file and computes the AI move to play.
        Sets flags for the GUI to display the board with the move highlighted.
        Returns True with the move string on success, or False with an error
        message on failure.
        """
        try:
            # Load the position from file
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                result = self.game.load_game_from_file(contest_file)

            if result != 0:
                return False, _(
                    "Could not load contest file: {contest_file}"
                ).format(contest_file=contest_file)

            # Execute AI move and get the result
            move = self.game.game_mode_manager.run_contest()

            # Store the move and enable highlighting for GUI display
            self.contest_move_str = move
            self.highlight_contest_move = True

            return True, move
        except ValueError as exc:
            return False, str(exc)

    def undo(self):
        commands_handler_gui.on_undo(self.game)
        if self.board_view:
            self.board_view.refresh()
        if self.gui and hasattr(self.gui, "players_view"):
            self.gui.players_view.refresh()

    def redo(self):
        commands_handler_gui.on_redo(self.game)
        if self.board_view:
            self.board_view.refresh()
        if self.gui and hasattr(self.gui, "players_view"):
            self.gui.players_view.refresh()

    def save(self):
        pass

    def load(self):
        pass

    def play_move_gui(self):
        # Prevent moves in contest mode (display only)
        if self.highlight_contest_move:
            if self.gui is not None and hasattr(self.gui, "error_message"):
                self.gui.error_message.show_error(
                    _("Contest mode is read-only. View the AI move and use Back to return to menu."))
            return

        if self.current_tile is None:
            return

        final_move = self.current_tile.playable_tile()
        result = self.game.play_move(final_move)

        if not result:
            self.error = self._build_error_message(final_move)
            if self.gui is not None and hasattr(self.gui, "error_message"):
                self.gui.error_message.show_error(self.error)
        else:
            self.error = None
            while (
                self.game.get_current_player().is_ai_player()
                and not self.game.end_game()
            ):
                self.game.play_ai_turn(self.game)
                self._refresh_after_ai_turn()

        if not self.game.is_undo_history_empty():
            self.game.clear_undo_history()

        self.reset()

        if self.game.end_game() and self.gui is not None:
            self.gui.show_end_game_screen()

    def _refresh_after_ai_turn(self):
        """Force a visual refresh between two consecutive AI turns."""
        if self.board_view:
            self.board_view.refresh()
        if self.gui and hasattr(self.gui, "players_view"):
            self.gui.players_view.refresh()

        # Let GTK process pending redraw events before the next AI move.
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)

    def reset(self):
        self.current_tile = None
        self.current_orientation = 0
        self.hint_tile = None  # clear hint when resetting
        if self.board_view:
            self.board_view.refresh()

    def set_board_view(self, board):
        self.board_view = board

    def get_error(self):
        return self.error

    def _build_error_message(self, move: str) -> str:
        if not move:
            return _(
                "No tile has been selected. "
                "Please select a tile and try again."
            )

        if self.game.game_data.current_hand is None:
            return _(
                "You must draw a tile before you can play it."
            )

        try:
            parsed_move = self.game.parse_move(move)
        except ValueError:
            return _(
                "Invalid move format. Use the format <tile>/<position>"
                "<rotation> or <tile>/<center>/<position><rotation>."
            )

        current_player = self.game.get_current_player()
        if (
            self.game.game_data.players_order[
                self.game.game_data.current_player_order_list
            ]
            != current_player.get_id()
        ):
            return _(
                "It is not your turn. Wait for the next player to play."
            )

        if parsed_move.get("meeple") and current_player.get_meeples() <= 0:
            return _(
                "You cannot place a meeple: you have no more left."
            )

        tile_code = self.game.game_data.extract_tile_code(move)
        if (
            tile_code is not None
            and tile_code != self.game.game_data.current_hand
        ):
            return _(
                "You must play the tile in hand {current_tile} and "
                "not {played_tile}."
            ).format(
                current_tile=self.game.game_data.current_hand,
                played_tile=tile_code,
            )

        if (
            hasattr(self.game.game_data, "rules_manager")
            and hasattr(
                self.game.game_data.rules_manager,
                "explain_invalid_move",
            )
        ):
            invalid_reason = (
                self.game.game_data.rules_manager.explain_invalid_move(
                    move,
                    self.game.game_data.graph,
                    self.game.river_manager,
                    current_player_id=current_player.get_id(),
                )
            )
            translated_reason = self._translate_invalid_move_reason(
                invalid_reason
            )
            if translated_reason is not None:
                return translated_reason

        return _(
            "This move is not valid according to the placement rules. "
            "Check the rotation, meeple and adjacency of terrains."
        )

    def _translate_invalid_move_reason(self, reason: str) -> str | None:
        exact_translations = {
            "move must be a string": _(
                "The move must be a string."
            ),
            "move format is invalid": _(
                "Invalid move format. Use the format <tile>/<position>"
                "<rotation> or <tile>/<center>/<position><rotation>."
            ),
            "tile code is invalid": _(
                "The tile code is invalid."
            ),
            "tile center variant is invalid": _(
                "The tile center variant is invalid."
            ),
            "tile center variant is missing": _(
                "The tile center variant is missing."
            ),
            "move placement is missing": _(
                "The placement position is missing."
            ),
            "placement format is invalid": _(
                "The placement format is invalid."
            ),
            "target tile id does not exist": _(
                "The target tile does not exist."
            ),
            "target side is invalid": _(
                "The target side is invalid."
            ),
            "tile rotation is invalid": _(
                "The tile rotation is invalid."
            ),
            "meeple position is invalid": _(
                "The chosen meeple position is invalid."
            ),
            "target side is already occupied": _(
                "The target side is already occupied."
            ),
            "tile sides do not match neighboring tiles": _(
                "The tile sides do not match neighboring tiles."
            ),
            "river placement rules are violated": _(
                "River placement rules are violated."
            ),
            "target tile position is invalid": _(
                "The target tile position is invalid."
            ),
            "target tile could not be simulated": _(
                "Tile placement simulation failed."
            ),
            "meeples cannot be placed on river segments": _(
                "A meeple cannot be placed on a river segment."
            ),
            "selected meeple position does not belong to a valid component": _(
                "The chosen meeple position does not belong "
                "to a valid component."
            ),
            "selected meeple position does not map to a component": _(
                "The chosen meeple position does not correspond "
                "to any component."
            ),
            "meeple placement is invalid": _(
                "Meeple placement is invalid."
            ),
            "move is invalid": _(
                "This move is not valid according to the rules."
            ),
        }

        if reason in exact_translations:
            return exact_translations[reason]

        if reason.startswith("tile ") and reason.endswith(" is not available"):
            tile_identifier = reason[len("tile "): -len(" is not available")]
            return _(
                "The tile {tile} is not available."
            ).format(tile=tile_identifier)

        if reason.startswith("component ") and reason.endswith(
            " already contains a meeple"
        ):
            suffix = " already contains a meeple"
            component_name = reason[len("component "): -len(suffix)]
            display_name = self._get_component_display_name(component_name)
            return _(
                "A meeple is already present on {component}."
            ).format(component=display_name)

        return None

    def rotate_current_tile(self):
        if self.current_tile is None:
            return

        self.current_orientation = (self.current_orientation + 1) % 4

        if self.current_tile.move:
            self.current_tile.move = self.current_tile.move[:-1] + str(
                self.current_orientation
            )

        if self.board_view:
            self.board_view.refresh()

        if hasattr(self, "gui"):
            self.gui.tile_preview.update_rotation()

    def draw_tile(self):
        tile_name = self.game.draw_tile()
        if tile_name is None:
            self.current_tile = None
            self.current_orientation = 0
            return None
        self.nb_tiles += 1
        self.current_tile = TilesView(tile_name, tile_id=self.nb_tiles)
        self.current_orientation = 0
        if self.board_view:
            self.board_view.refresh()
        return tile_name

    def provide_hint(self):
        hint_move = self.game.provide_hint()
        if hint_move:
            # Parse the hint move to get tile and placement info
            parsed = self.game.parse_move(hint_move)
            tile_code = parsed["tile_sides"]
            if parsed.get("center"):
                tile_code = f"{tile_code}/{parsed['center']}"

            # Calculate position
            position = self.game.get_adjacent_position(
                vertex_id=parsed["target_id"],
                side=self.game.game_data.tiles_info.direction_dict[
                    parsed["target_side"]
                ],
            )
            if position:
                self.hint_tile = {
                    "id": -1,  # special id for hint
                    "x": position[0],
                    "y": position[1],
                    "name": parsed["tile_sides"],
                    "middle": parsed.get("center", ""),
                    "orientation": parsed["rotation"],
                    "meeple": parsed.get("meeple"),  # add meeple position
                }
                if self.board_view:
                    self.board_view.queue_draw()
        return hint_move
