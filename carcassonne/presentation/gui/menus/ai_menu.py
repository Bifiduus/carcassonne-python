from gi.repository import Gtk
import gi

gi.require_version("Gtk", "4.0")


class AiMenu(Gtk.Box):
    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)

        title = Gtk.Label(label="Ai")
        title.add_css_class("section-title")
        self.append(title)

        # --- AI selection --------------------------------------------------
        ai_choice_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.ai_choice = Gtk.ComboBoxText()
        # Exemple de résolutions courantes
        ais = ["Random", "Minimax", "Monte Carlo"]
        for ai in ais:
            self.ai_choice.append_text(ai)
        # Valeurs par défaut
        self.ai_choice.set_active(0)
        ai_choice_box.append(Gtk.Label(label="AI:"))
        ai_choice_box.append(self.ai_choice)
        # Connect signal to apply AI selection immediately
        self.ai_choice.connect("changed", self.on_ai_selected)
        self.append(ai_choice_box)

        # --- Numbers of AI players --------------------------------------------------
        ai_players_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.ai_players_entry = Gtk.Entry()
        self.ai_players_entry.set_placeholder_text(
            "1-4")
        ai_players_box.append(Gtk.Label(label="Number of AI players:"))
        self.ai_players_entry.connect("changed", self.on_ai_players_changed)

        ai_players_box.append(self.ai_players_entry)
        self.append(ai_players_box)

        # --- back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        btn_back = Gtk.Button(label="Back")
        btn_back.add_css_class("back-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_box.append(btn_back)
        self.append(btn_box)

    def on_ai_selected(self, combo_box):
        """Apply AI configuration immediately when selection changes"""
        # Get the selected AI and map it to the config value
        ai_selection = self.ai_choice.get_active_text()

        # Map display names to internal AI mode names
        ai_mode_map = {
            "Random": "random",
            "Minimax": "minimax",
            "Monte Carlo": "mcts"
        }

        ai_mode = ai_mode_map.get(ai_selection, "minimax")

        # Apply the AI configuration
        self.gui.game_data.game.set_game_configuration("ai_mode", ai_mode)
        self.gui.game_data.game.save_config()

    def on_ai_players_changed(self, entry):
        """Apply AI players configuration when entry changes"""
        try:
            num_ai_players = int(self.ai_players_entry.get_text())
            if 1 <= num_ai_players <= 4:
                self.gui.game_data.game.set_game_configuration(
                    "num_ai_players", num_ai_players)
                self.gui.game_data.game.save_config()
        except ValueError:
            pass

    def on_back(self, button):
        self.gui.window.stack.set_visible_child_name("singleplayer_menu")
