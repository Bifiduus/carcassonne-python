from carcassonne.presentation.gui.gui import GameGUI
from carcassonne.presentation.gui.game_data_gui import GameDataGui


class ClientMenuMessageVisitor:
    """Route server events to the appropriate menu widgets."""

    def __init__(self, game_gui):
        self._game_gui = game_gui

    def visit_server_message(self, message: str, server: str):
        """Route messages to the appropriate menu only."""
        # Player list messages go to invitation menu
        if "List of current players:" in message:
            invitation_menu = self._game_gui.invitation_view
            if invitation_menu is not None:
                invitation_menu.visit_server_message(message, server)
        # Status/invitation related responses go to invitation menu
        elif any(
            keyword in message.lower()
            for keyword in [
                "invitation",
                "accept",
                "decline",
                "cancel",
                "away",
                "idle",
                "status",
            ]
        ):
            invitation_menu = self._game_gui.invitation_view
            if invitation_menu is not None:
                invitation_menu.visit_server_message(message, server)
        # All other server messages go to server menu
        else:
            server_menu = self._game_gui.server_view
            if server_menu is not None:
                server_menu.visit_server_message(message, server)


class CreateGui:
    def __init__(self, game, client_service, server_service) -> None:
        game_data = GameDataGui(game, client_service, server_service)
        game_gui = GameGUI(game_data)

        # Pass full game_gui: views are resolved at call time.
        if hasattr(client_service, "register_message_visitor"):
            visitor = ClientMenuMessageVisitor(game_gui)
            client_service.register_message_visitor(visitor)

        game_gui.run()  # do_activate() creates server_view and invitation_view
