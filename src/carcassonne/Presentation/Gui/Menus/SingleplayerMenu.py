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
        btn_start = Gtk.Button(label="Start Game")
        btn_back = Gtk.Button(label="Back")
        btn_start.connect("clicked", self.on_start)
        btn_back.connect("clicked", self.on_back)
        btn_start.set_hexpand(False)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_start)
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
        self.gui.window.stack.set_visible_child_name("menu")

    def on_start(self, button):
        """Apply the chosen options and switch to the game view."""
        # parse seed entry
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

        # start a new game with the chosen seed; any further data (mode,
        # contest file) is stored on the GUI object for downstream logic.
        # the GameDataGui helper simply accepts seed and optionally other
        # values, so we extend it to carry these new pieces of state.
        """self.gui.game_data.new_game(seed=seed)
        # record the selected mode and contest path on the GUI/data objects
        self.gui.game_mode = mode
        # attributes on game_data are convenient for game logic later
        self.gui.game_data.mode = mode
        if contest_file:
            self.gui.contest_file = contest_file
            self.gui.game_data.contest_file = contest_file"""

        # switch to the board view
        self.gui.window.stack.set_visible_child_name("game")

