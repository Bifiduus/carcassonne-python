import os

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from carcassonne.Presentation.Gui import utils

class OptionsMenu(Gtk.Box):
    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)

        title = Gtk.Label(label="Options")
        title.add_css_class("title-2")
        self.append(title)

        # --- game options button --------------------------------------------------
        keybinds_button = Gtk.Button(label="Game Options")
        keybinds_button.connect("clicked", self.on_game_options)
        self.append(keybinds_button)

        # --- keybinds button --------------------------------------------------
        keybinds_button = Gtk.Button(label="Keybinds")
        keybinds_button.connect("clicked", self.on_keybinds)
        self.append(keybinds_button)

        

        # --- back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        btn_back = Gtk.Button(label="Back")
        btn_back.connect("clicked", self.on_back)
        btn_box.append(btn_back)
        self.append(btn_box)


        # ------------------------------------------------------------------

        
    def on_back(self, button):
        """Return to the main menu"""
        self.gui.window.stack.set_visible_child_name("menu")

    def on_keybinds(self, button):
        self.gui.window.stack.set_visible_child_name("keybinds_menu")

    def on_game_options(self, button):
        self.gui.window.stack.set_visible_child_name("singleplayer_menu")
