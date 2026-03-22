from gi.repository import Gtk
import gi

gi.require_version("Gtk", "4.0")


class ErrorMessageView:
    def __init__(self, gui):
        self.gui = gui

    def show_error(self, message: str):
        self.gui.window.window.present()
        dialog = Gtk.AlertDialog()
        dialog.set_message("Erreur")
        dialog.set_detail(message)
        dialog.set_modal(True)
        dialog.show(self.gui.window.window)
