from gi.repository import Gtk
import os

import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class SingleplayerMenu(Gtk.Box):
    """Simple form that lets the user pick a few configuration options.

    The view is shown when the player chooses *Singleplayer* (or the
    standalone *Options* button) from the main menu.  It doesn't attempt to
    replicate every setting that the command-line version exposes; at the
    moment we only wire up a random seed and a background image so that the
    information can actually be used by the rest of the GUI.  New fields can
    be added later as the project evolves.

    The view keeps a reference to the parent :class:`GameGUI` instance so that
    it can drive navigation and apply the selected options when the user
    presses the *Start* button.  A *Back* button simply returns the stack to
    the main menu.
    """

    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)

        title = Gtk.Label(label=_("Game"))
        title.add_css_class("section-title")
        self.append(title)

        ai_button = Gtk.Button(label=_("AI"))
        ai_button.add_css_class("options-buttons")
        ai_button.connect("clicked", self.on_ai_options)
        self.append(ai_button)

        # --- random seed --------------------------------------------------
        seed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        seed_label = Gtk.Label(label=_("Random seed:"))
        self.entry_seed = Gtk.Entry()
        self.entry_seed.set_placeholder_text(_("Leave blank for random"))
        self.entry_seed.connect("changed", self.on_seed_changed)
        seed_box.append(seed_label)
        seed_box.append(self.entry_seed)
        self.append(seed_box)

        # --- game mode ----------------------------------------------------
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mode_box.set_halign(Gtk.Align.CENTER)
        self.blitz_cb = Gtk.CheckButton(label=_("Blitz mode"))
        self.contest_cb = Gtk.CheckButton(label=_("Contest mode"))
        # file chooser only enabled when contest is active
        self.file_button = Gtk.Button(label=_("Choose contest file"))
        self.file_button.connect("clicked", self.on_choose_file)

        self.time_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6
        )
        entry_label = Gtk.Label(label=_("Time limit (minutes):"))
        self.entry_time = Gtk.Entry()
        self.entry_time.connect("changed", self.on_time_changed)
        self.time_box.append(entry_label)
        self.time_box.append(self.entry_time)

        self.file_button.set_visible(False)  # hidden by default
        self.time_box.set_visible(False)  # hidden by default
        self.selected_file = None

        mode_box.append(self.blitz_cb)
        mode_box.append(self.time_box)
        mode_box.append(self.contest_cb)
        mode_box.append(self.file_button)
        mode_box.append(self.river_cb)

        self.append(mode_box)

        # Connect mode toggle to apply configuration immediately
        self.blitz_cb.connect("toggled", self.on_mode_toggle)
        self.contest_cb.connect("toggled", self.on_mode_toggle)
        self.river_cb.connect("toggled", self.on_mode_toggle)

        # --- start / back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label=_("Back"))
        btn_back.add_css_class("back-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.append(btn_box)

    # ------------------------------------------------------------------

    def on_ai_options(self, button):
        self.gui.window.stack.set_visible_child_name("ai_menu")

    def on_choose_file(self, button):
        self.gui.window.window.present()
        dialog = Gtk.FileDialog(title=_("Select contest file"))

        dialog.open(self.gui.window.window, None, self.on_file_selected)

    def on_seed_changed(self, entry):
        """Apply seed configuration when it changes"""
        seed_str = self.entry_seed.get_text().strip()
        # Store seed for later use (will be passed to new_game)
        self.seed_value = None
        if seed_str:
            try:
                self.seed_value = int(seed_str)
            except ValueError:
                pass

    def on_time_changed(self, entry):
        """Apply time configuration when it changes"""
        time_str = self.entry_time.get_text().strip() or "30"
        self.gui.game_data.game.set_game_configuration("time", time_str)
        self.gui.game_data.game.save_config()

    def on_mode_toggle(self, button):
        """Apply mode configuration when it changes"""
        # Update UI visibility
        if button is self.river_cb:
            river_active = button.get_active()
            self.gui.game_data.game.set_game_configuration(
                "river", river_active)
            self.gui.game_data.game.save_config()
            return

        if button is self.blitz_cb and button.get_active():
            self.contest_cb.set_active(False)
            self.time_box.set_visible(True)
            self.file_button.set_visible(False)
            self.selected_file = None

            # Apply blitz mode
            self.gui.game_data.game.set_game_configuration("blitz", True)
            self.gui.game_data.game.set_game_configuration("contest_file", "")

        elif button is self.contest_cb and button.get_active():
            self.blitz_cb.set_active(False)
            self.file_button.set_visible(True)
            self.time_box.set_visible(False)
            self.selected_file = None

            # Apply contest mode
            self.gui.game_data.game.set_game_configuration("blitz", False)

        else:
            self.file_button.set_visible(False)
            self.time_box.set_visible(False)
            self.selected_file = None

            # Clear both modes
            self.gui.game_data.game.set_game_configuration("blitz", False)

        self.gui.game_data.game.save_config()

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            self.selected_file = file.get_path()
            self.file_button.set_label(os.path.basename(self.selected_file))
            # Apply contest file configuration immediately
            self.gui.game_data.game.set_game_configuration(
                "contest_file", self.selected_file
            )
            self.gui.game_data.game.save_config()
        except Exception:
            pass

    def on_back(self, button):
        """Validate configuration and start a new game."""
        # Validate contest file if contest mode is selected
        if self.contest_cb.get_active() and not self.selected_file:
            print(_("Please select a contest file."))
            return

        # Start the new game with the seed value
        seed = getattr(self, "seed_value", None)
        self.gui.game_data.new_game(None, seed)
        self.gui.window.stack.set_visible_child_name("options_menu")
