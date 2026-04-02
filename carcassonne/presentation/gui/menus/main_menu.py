"""Simple helper for building the initial main menu UI."""

from gi.repository import Gtk

from carcassonne.i18n import gettext as _


class MainMenu:
    @staticmethod
    def create(gui):
        """Return a centered vertical box containing the main menu buttons.

        ``gui`` is expected to be the :class:`GameGUI` instance so that the
        signal handlers (start_singleplayer/start_multiplayer) can access
        ``self.window`` etc.  Keeping these handlers on the GUI class keeps
        the coupling low while still letting the menu be built from a
        separate module.
        """
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )

        title = Gtk.Label(label="Carcassonne")
        title.add_css_class("main-title")

        btn_single = Gtk.Button(label="Start Game")
        btn_single.add_css_class("orange-buttons")
        btn_multi = Gtk.Button(label="Multiplayer")
        btn_multi.add_css_class("orange-buttons")
        btn_options = Gtk.Button(label="Options")
        btn_options.add_css_class("orange-buttons")
        btn_quit = Gtk.Button(label="Quit")
        btn_quit.add_css_class("red-buttons")

        btn_single.connect("clicked", gui.start_singleplayer)
        btn_multi.connect("clicked", gui.start_multiplayer)
        btn_options.connect("clicked", gui.show_options)
        btn_quit.connect("clicked", lambda b: gui.quit())

        for widget in (title, btn_single, btn_multi, btn_options, btn_quit):
            box.append(widget)

        return box
