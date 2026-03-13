import os

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from carcassonne.Presentation.Gui import utils



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

        title = Gtk.Label(label="Game options")
        title.add_css_class("title-2")
        self.append(title)

        # --- random seed --------------------------------------------------
        seed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        seed_label = Gtk.Label(label="Random seed:")
        self.entry_seed = Gtk.Entry()
        self.entry_seed.set_placeholder_text("(leave blank for random)")
        seed_box.append(seed_label)
        seed_box.append(self.entry_seed)
        self.append(seed_box)

        # --- game mode ----------------------------------------------------
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mode_box.set_halign(Gtk.Align.CENTER)
        self.blitz_cb = Gtk.CheckButton(label="Blitz mode")
        self.contest_cb = Gtk.CheckButton(label="Contest mode")
        # file chooser only enabled when contest is active
        self.file_button = Gtk.Button(label="Choose contest file")
        self.file_button.connect("clicked", self.on_choose_file)
        
        self.file_button.set_visible(False)   # hidden by default
        self.selected_file = None

        mode_box.append(self.blitz_cb)
        mode_box.append(self.contest_cb)
        mode_box.append(self.file_button)
        self.append(mode_box)

        # when one mode is toggled the other must be cleared and the chooser
        # enabled/disabled appropriately
        def on_mode_toggle(button):
            if button is self.blitz_cb and button.get_active():
                self.contest_cb.set_active(False)
                
                self.file_button.set_visible(False) 
                self.selected_file = None

            elif button is self.contest_cb and button.get_active():
                self.blitz_cb.set_active(False)
                self.file_button.set_visible(True)

            else:
                self.file_button.set_visible(False)
                self.selected_file = None

        self.blitz_cb.connect("toggled", on_mode_toggle)
        self.contest_cb.connect("toggled", on_mode_toggle)

        # --- start / back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label="Back")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)
        
        self.append(btn_box)

    # ------------------------------------------------------------------
    def on_choose_file(self, button):
        dialog = Gtk.FileDialog(title="Select contest file")

        dialog.open(
            self.gui.window.window,
            None,
            self.on_file_selected
        )

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            self.selected_file = file.get_path()
            self.file_button.set_label(os.path.basename(self.selected_file))
        except Exception:
            pass

    def on_back(self, button):
        """Return to the main menu without applying any settings."""
        seed_str = self.entry_seed.get_text().strip()
        seed = None
        if seed_str:
            try:
                seed = int(seed_str)
            except ValueError:
                # ignore invalid input and treat as no seed
                seed = None

        # determine mode (only one may be selected)
        mode = None
        contest_file = None
        if self.blitz_cb.get_active():
            mode = "blitz"
        elif self.contest_cb.get_active():
            mode = "contest"
            contest_file = self.selected_file
        if mode == "contest" and not contest_file:
            print("Please select a contest file")
            return

        # apply selected settings to the game configuration and start a new game
        # (seed is passed to the game logic; mode is stored as a setting).
        if mode == "blitz":
            self.gui.game_data.game.set_game_configuration("blitz", True)
            # clear contest file if any
            self.gui.game_data.game.set_game_configuration("contest_file", "")
        else:
            self.gui.game_data.game.set_game_configuration("blitz", False)

        if contest_file:
            self.gui.game_data.game.set_game_configuration("contest_file", contest_file)

        # persist configuration to disk
        self.gui.game_data.game.save_config()

        # start the new game (players order is handled internally by Game)
        self.gui.game_data.new_game(None, seed)
        self.gui.window.stack.set_visible_child_name("options_menu")
