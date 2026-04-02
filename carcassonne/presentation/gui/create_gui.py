from carcassonne.presentation.gui.gui import GameGUI
from carcassonne.presentation.gui.game_data_gui import GameDataGui


class ClientMenuMessageVisitor:
    """Composite visitor delivering server events into menu widgets."""

    def __init__(self, server_menu, invitation_menu):
        self.server_menu = server_menu
        self.invitation_menu = invitation_menu

    def visit_server_message(self, message: str, server: str):
        if self.server_menu is not None:
            self.server_menu.visit_server_message(message, server)
        if self.invitation_menu is not None:
            self.invitation_menu.visit_server_message(message, server)


class CreateGui:
    def __init__(self, game, client_service, server_service) -> None:
        game_data = GameDataGui(game, client_service, server_service)

        game_gui = GameGUI(game_data)

        # register the client message visitor on the component menus (not game_data)
        if hasattr(client_service, "register_message_visitor"):
            visitor = ClientMenuMessageVisitor(
                game_gui.server_view,
                game_gui.invitation_view,
            )
            client_service.register_message_visitor(visitor)

        game_gui.run()
