import gi

from gi.repository import Gio, Gtk


class WindowView:
    """Helper that builds the top-level application window and the
    two menus ("File" and "Game").

    The original `GameGUI.do_activate` method contained a large block of
    boilerplate for creating the window, the header bar, the menus and
    registering actions.  ``WindowView`` encapsulates that logic so the
    GUI class itself can focus on game-specific widgets like the board
    overlay and tile preview.

    The class exposes the ``stack`` attribute so callers can add their own
    views, and provides a thin wrapper ``create_action`` for registering
    application actions.  Accelerators are also set up automatically when
    the menu is created.
    """

    def __init__(self, application: Gtk.Application, game_data):
        self.application = application
        self.game_data = game_data

        self.file_button = None
        self.game_button = None

        # Load keybinds from config
        config = self.game_data.game.get_game_configuration()
        self.file_keybinds = config.get(
            "file_keybinds",
            {
                "app.new": "n",
                "app.load": "l",
                "app.save": "s",
                "app.config": "comma",
                "app.info": "i",
                "app.quit": "q",
            },
        )
        self.game_keybinds = config.get(
            "game_keybinds",
            {
                "app.undo": "u",
                "app.redo": "r",
                "app.pause": "p",
                "app.hint": "h",
            },
        )

        # main window
        self.window = Gtk.ApplicationWindow(application=self.application)
        self.window.set_title("Carcassonne")
        self.window.set_default_size(1080, 720)
        self.window.add_css_class("main-title")

        # stack of views (menu / game / etc.)
        self.stack = Gtk.Stack()
        self.window.set_child(self.stack)

        # header and menus
        header = Gtk.HeaderBar()
        self.window.set_titlebar(header)

        self._build_file_menu(header)
        self._build_game_menu(header)

    def _build_file_menu(self, header: Gtk.HeaderBar):
        menu_file = Gio.Menu()
        menu_file.append("New Game", "app.new")
        menu_file.append("Load Game", "app.load")
        menu_file.append("Save Game", "app.save")
        menu_file.append("Configuration", "app.config")
        menu_file.append("Info", "app.info")
        menu_file.append("Quit", "app.quit")
        for action, key in self.file_keybinds.items():
            self.application.set_accels_for_action(action, ["<Primary>" + key])
        file_button = self.create_menu_button("File", menu_file)
        header.pack_start(file_button)

    def _build_game_menu(self, header: Gtk.HeaderBar):
        menu_game = Gio.Menu()
        menu_game.append("Undo", "app.undo")
        menu_game.append("Redo", "app.redo")
        menu_game.append("Pause", "app.pause")
        menu_game.append("Hint", "app.hint")
        for action, key in self.game_keybinds.items():
            self.application.set_accels_for_action(action, ["<Primary>" + key])

        game_button = self.create_menu_button("Game", menu_game)
        header.pack_start(game_button)

    def create_menu_button(self, label: str, menu: Gio.Menu) -> Gtk.MenuButton:
        button = Gtk.MenuButton()
        button.set_label(label)
        button.set_menu_model(menu)
        return button

    def create_action(self, name: str, callback):
        """Convenience wrapper so callers don't have to import Gio.

        ``name`` should be the short action id (e.g. "new", "undo").  The
        GTK menu items point at the corresponding full action name
        (``app.<name>``).
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.application.add_action(action)

    def hide_menus(self):
        """Cache les menus (ex: pendant le jeu ou après un clic)."""
        if self.file_button:
            self.file_button.set_visible(False)
        if self.game_button:
            self.game_button.set_visible(False)

    def show_menus(self):
        """Réaffiche les menus."""
        if self.file_button:
            self.file_button.set_visible(True)
        if self.game_button:
            self.game_button.set_visible(True)
