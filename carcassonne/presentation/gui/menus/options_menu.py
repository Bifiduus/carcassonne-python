from gi.repository import Gtk

import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class OptionsMenu(Gtk.Box):
    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)

        title = Gtk.Label(label=_("Options"))
        title.add_css_class("section-title")
        self.append(title)

        # --- game options button ---------------------------------------------
        keybinds_button = Gtk.Button(label="Game")
        keybinds_button.add_css_class("orange-buttons")
        keybinds_button.connect("clicked", self.on_game_options)
        self.append(keybinds_button)

        # --- keybinds button -------------------------------------------------
        keybinds_button = Gtk.Button(label="Keybinds")
        keybinds_button.add_css_class("orange-buttons")
        keybinds_button.connect("clicked", self.on_keybinds)
        self.append(keybinds_button)

        # ------------------------------------------------------------------

        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        options_box.set_halign(Gtk.Align.CENTER)
        self.fullscreen_cb = Gtk.CheckButton(label=_("Fullscreen"))

        options_box.append(self.fullscreen_cb)
        self.fullscreen_cb.connect("toggled", self.on_fullscreen_toggled)
        self.append(options_box)

        res_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.width_combo = Gtk.ComboBoxText()
        self.height_combo = Gtk.ComboBoxText()

        # Common screen resolutions.
        resolutions = [(800, 600), (1024, 768), (1280, 720), (1920, 1080)]
        for w, h in resolutions:
            self.width_combo.append_text(str(w))
            self.height_combo.append_text(str(h))

        # Default values.
        self.width_combo.set_active(0)
        self.height_combo.set_active(0)

        res_box.append(Gtk.Label(label=_("Width:")))
        res_box.append(self.width_combo)
        res_box.append(Gtk.Label(label=_("Height:")))
        res_box.append(self.height_combo)

        # bouton pour appliquer la résolution
        apply_btn = Gtk.Button(label="Apply Resolution")
        apply_btn.add_css_class("orange-buttons")
        apply_btn.connect("clicked", self.apply_resolution)
        res_box.append(apply_btn)

        self.append(res_box)

        # --- back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        btn_back = Gtk.Button(label="Back")
        btn_back.add_css_class("red-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_box.append(btn_back)
        self.append(btn_box)

    def on_back(self, button):
        self.gui.window.stack.set_visible_child_name("menu")

    def on_keybinds(self, button):
        self.gui.window.stack.set_visible_child_name("keybinds_menu")

    def on_game_options(self, button):
        self.gui.window.stack.set_visible_child_name("singleplayer_menu")

    def on_fullscreen_toggled(self, button):
        if self.fullscreen_cb.get_active():
            self.gui.window.fullscreen()
        else:
            # Apply the selected resolution when leaving fullscreen.
            self.apply_resolution()

    def apply_resolution(self, button=None):
        width = int(self.width_combo.get_active_text())
        height = int(self.height_combo.get_active_text())
        if self.fullscreen_cb.get_active():
            self.gui.window.window.fullscreen()
        else:
            self.gui.window.window.unfullscreen()
            self.gui.window.window.set_default_size(width, height)
