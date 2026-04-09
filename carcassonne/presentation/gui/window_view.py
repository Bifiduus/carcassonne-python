"""Top-level GTK window and header/menu construction helpers."""

import math


from gi.repository import Gio, Gtk, GLib

from carcassonne.datas.game_configuration import (
    FILE_KEYBIND_DEFAULTS,
    GAME_KEYBIND_DEFAULTS,
)
from carcassonne.i18n import gettext as _


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
        raw_file_keybinds = config.get("file_keybinds", {})
        raw_game_keybinds = config.get("game_keybinds", {})
        self.file_keybinds = FILE_KEYBIND_DEFAULTS.copy()
        self.game_keybinds = GAME_KEYBIND_DEFAULTS.copy()
        if isinstance(raw_file_keybinds, dict):
            self.file_keybinds.update(raw_file_keybinds)
        if isinstance(raw_game_keybinds, dict):
            self.game_keybinds.update(raw_game_keybinds)

        # main window
        self.window = Gtk.ApplicationWindow(application=self.application)
        self.window.set_title("Carcassonne")
        self.window.set_default_size(1080, 720)

        # stack of views (menu / game / etc.)
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_halign(Gtk.Align.FILL)
        self.stack.set_valign(Gtk.Align.FILL)

        # header and menus

        header = Gtk.HeaderBar()
        self.window.set_titlebar(header)
        header.add_css_class("headers")

        self.header = header  # keep a reference
        self._setup_header_animation()

        self._build_file_menu(header)
        self._build_game_menu(header)

    def _build_file_menu(self, header: Gtk.HeaderBar):
        """Create and attach the File menu button with accelerators."""
        menu_file = Gio.Menu()
        menu_file.append(_("New game"), "app.new")
        menu_file.append(_("Load game"), "app.load")
        menu_file.append(_("Save game"), "app.save")
        menu_file.append(_("Configuration"), "app.config")
        menu_file.append(_("Info"), "app.info")
        menu_file.append(_("Quit"), "app.quit")
        for action, key in self.file_keybinds.items():
            self.application.set_accels_for_action(action, ["<Primary>" + key])
        file_button = self.create_menu_button(_("File"), menu_file)
        file_button.add_css_class("headers_buttons")
        header.pack_start(file_button)

    def _build_game_menu(self, header: Gtk.HeaderBar):
        """Create and attach the Game menu button with accelerators."""
        menu_game = Gio.Menu()
        menu_game.append(_("Undo"), "app.undo")
        menu_game.append(_("Redo"), "app.redo")
        menu_game.append(_("Pause"), "app.pause")
        menu_game.append(_("Hint"), "app.hint")
        for action, key in self.game_keybinds.items():
            self.application.set_accels_for_action(action, ["<Primary>" + key])

        game_button = self.create_menu_button(_("Game"), menu_game)
        game_button.add_css_class("headers_buttons")
        header.pack_start(game_button)

    def create_menu_button(self, label: str, menu: Gio.Menu) -> Gtk.MenuButton:
        """Return a Gtk.MenuButton bound to the provided Gio.Menu model."""
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
        """Hide menus, for example during gameplay."""
        if self.file_button:
            self.file_button.set_visible(False)
        if self.game_button:
            self.game_button.set_visible(False)

    def show_menus(self):
        """Show menus again."""
        if self.file_button:
            self.file_button.set_visible(True)
        if self.game_button:
            self.game_button.set_visible(True)

    def _setup_header_animation(self):
        """Initialize animated gradient state for the header bar."""
        self._t = 0

        self._css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            self.window.get_display(),
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        GLib.timeout_add(50, self._animate_header)

    def _animate_header(self):
        """Update header gradient; returns True to keep timeout alive."""
        self._t += 0.02

        # Animated colors for a fluid header effect.
        r = int((math.sin(self._t) + 1) * 127)
        g = int((math.sin(self._t + 2) + 1) * 127)
        b = int((math.sin(self._t + 4) + 1) * 127)

        color1 = f"rgb({r},{g},{b})"
        color2 = f"rgb({b},{r},{g})"

        css = f"""
        .headers {{
            background: linear-gradient(135deg, {color1}, {color2});
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-weight: bold;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }}
        """

        self._css_provider.load_from_data(css.encode())

        return True
