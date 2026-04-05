from gi.repository import Gtk

import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class KeybindsMenu(Gtk.Box):
    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)

        title = Gtk.Label(label=_("Keybinds"))
        title.add_css_class("section-title")
        self.append(title)

        # --- keybinds button -------------------------------------------------
        # -------- FILE KEYBINDS --------
        file_title = Gtk.Label(label=_("File"))
        file_title.add_css_class("heading")
        self.append(file_title)

        file_box = self.build_keybind_section(self.gui.window.file_keybinds)
        self.append(file_box)

        # -------- GAME KEYBINDS --------
        game_title = Gtk.Label(label=_("Game"))
        game_title.add_css_class("heading")
        self.append(game_title)

        game_box = self.build_keybind_section(self.gui.window.game_keybinds)
        self.append(game_box)

        # --- back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        btn_back = Gtk.Button(label=_("Back"))
        btn_back.add_css_class("red-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_box.append(btn_back)
        self.append(btn_box)

        # ------------------------------------------------------------------

    def on_back(self, button):
        """Return to the options menu."""
        self.gui.window.stack.set_visible_child_name("options_menu")

    def build_keybind_section(self, keybind_dict):
        """Create a column of keybind rows."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        for action, key in keybind_dict.items():

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

            # pretty label
            pretty_name = action.replace("app.", "").replace("_", " ").title()

            label = Gtk.Label(label=pretty_name)
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)

            button = Gtk.Button(label=key)
            button.connect(
                "clicked", self.on_rebind_clicked, action, button, keybind_dict
            )

            row.append(label)
            row.append(button)

            box.append(row)

        return box

    def on_rebind_clicked(self, button, action, button_widget, keybind_dict):
        button_widget.set_label(_("Press key..."))

        controller = Gtk.EventControllerKey.new()
        controller.connect(
            "key-pressed",
            self.on_key_pressed,
            action,
            button_widget,
            keybind_dict,
        )

        self.add_controller(controller)

    def on_key_pressed(
        self,
        controller,
        keyval,
        keycode,
        state,
        action,
        button_widget,
        keybind_dict,
    ):

        keyname = Gtk.accelerator_name(keyval, 0)
        key = keyname.replace("<Primary>", "").lower()

        # prevent duplicates across BOTH sections
        all_keys = list(self.gui.window.file_keybinds.values()) + list(
            self.gui.window.game_keybinds.values()
        )

        if key in all_keys:
            print(_("Key already used."))
            button_widget.set_label(keybind_dict[action])
            self.remove_controller(controller)
            return True

        # update dictionary
        keybind_dict[action] = key

        # update config
        if keybind_dict is self.gui.window.file_keybinds:
            self.gui.game_data.game.set_game_configuration(
                "file_keybinds", self.gui.window.file_keybinds
            )
        else:
            self.gui.game_data.game.set_game_configuration(
                "game_keybinds", self.gui.window.game_keybinds
            )
        self.gui.game_data.game.save_config()

        # update GTK accelerator
        self.gui.window.application.set_accels_for_action(
            action, ["<Primary>" + key]
        )

        button_widget.set_label(key)

        self.remove_controller(controller)

        return True
