from gi.repository import Gtk
import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class AiMenu(Gtk.Box):
    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)

        title = Gtk.Label(label=_("AI"))
        title.add_css_class("section-title")
        self.append(title)

        # --- AI selection --------------------------------------------------
        ai_choice_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6
        )
        self.ai_choice = Gtk.ComboBoxText()
        # Example of common AI choices
        ais = ["Random", "Minimax", "Monte Carlo", "Iterative"]
        for ai in ais:
            self.ai_choice.append_text(_(ai))
        # Default value.
        self.ai_choice.set_active(0)
        ai_choice_box.append(Gtk.Label(label=_("AI:")))
        ai_choice_box.append(self.ai_choice)
        # Connect signal to apply AI selection immediately
        self.ai_choice.connect("changed", self.on_ai_selected)
        self.append(ai_choice_box)

        # --- Selection function for MCTS -----------------------------------
        self.selection_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6
        )
        self.selection_choice = Gtk.ComboBoxText()
        selection_functions = ["UCT", "ML"]
        for func in selection_functions:
            self.selection_choice.append_text(func)
        self.selection_choice.set_active(0)
        self.selection_box.append(Gtk.Label(label=_("Selection function:")))
        self.selection_box.append(self.selection_choice)
        self.selection_choice.connect("changed", self.on_selection_changed)
        self.selection_box.set_visible(False)  # Hidden by default
        self.append(self.selection_box)

        # --- Numbers of AI players ---------------------------------------
        ai_players_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6
        )
        self.ai_players_entry = Gtk.Entry()
        self.ai_players_entry.set_placeholder_text(_("1-4"))
        ai_players_box.append(Gtk.Label(label=_("Number of AI players:")))
        self.ai_players_entry.connect("changed", self.on_ai_players_changed)

        ai_players_box.append(self.ai_players_entry)
        self.append(ai_players_box)

        # --- AI Time (seconds) -------------------------------------------
        ai_time_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6
        )
        self.ai_time_entry = Gtk.Entry()
        self.ai_time_entry.set_placeholder_text(_("seconds"))
        ai_time_box.append(Gtk.Label(label=_("AI time (seconds):")))
        self.ai_time_entry.connect("changed", self.on_ai_time_changed)
        ai_time_box.append(self.ai_time_entry)
        self.append(ai_time_box)

        # --- back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        btn_back = Gtk.Button(label=_("Back"))
        btn_back.add_css_class("orange-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_box.append(btn_back)
        self.append(btn_box)

    def on_ai_selected(self, combo_box):
        """Apply AI configuration immediately when selection changes"""
        # Get the selected AI and map it to the config value
        ai_selection = self.ai_choice.get_active_text()

        # Map display names to internal AI mode names
        ai_mode_map = {
            _("Random"): "random",
            _("Minimax"): "minimax",
            _("Monte Carlo"): "mcts",
            _("Iterative"): "iterative",
        }

        ai_mode = ai_mode_map.get(ai_selection, "minimax")

        # Apply the AI configuration
        self.gui.game_data.game.set_game_configuration("ai_mode", ai_mode)

        # Show/hide selection function based on AI mode
        if ai_selection == _("Monte Carlo"):
            self.selection_box.set_visible(True)
            # Set the selection function
            selection = self.selection_choice.get_active_text()
            selection_map = {"UCT": "uct", "ML": "ml"}
            selection_func = selection_map.get(selection, "uct")
            self.gui.game_data.game.set_game_configuration(
                "selection_function", selection_func)
        else:
            self.selection_box.set_visible(False)

        self.gui.game_data.game.save_config()

    def on_ai_players_changed(self, entry):
        """Apply AI players configuration when entry changes"""
        try:
            num_ai_players = int(self.ai_players_entry.get_text())
            if 1 <= num_ai_players <= 4:
                self.gui.game_data.game.set_game_configuration(
                    "num_ai_players", num_ai_players
                )
                self.gui.game_data.game.save_config()
        except ValueError:
            pass

    def on_ai_time_changed(self, entry):
        """Apply AI time configuration when entry changes"""
        try:
            ai_time = int(self.ai_time_entry.get_text())
            if ai_time > 0:
                self.gui.game_data.game.set_game_configuration(
                    "ai_time", ai_time
                )
                self.gui.game_data.game.save_config()
        except ValueError:
            pass

    def on_selection_changed(self, combo_box):
        """Apply selection function configuration when changed"""
        if self.selection_box.get_visible():
            selection = self.selection_choice.get_active_text()
            selection_map = {"UCT": "uct", "ML": "ml"}
            selection_func = selection_map.get(selection, "uct")
            self.gui.game_data.game.set_game_configuration(
                "selection_function", selection_func)
            self.gui.game_data.game.save_config()

    def on_back(self, button):
        self.gui.window.stack.set_visible_child_name("singleplayer_menu")
