from gi.repository import Gtk
import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class ErrorMessageView:
    def __init__(self, gui):
        self.gui = gui

    def show_error(self, message: str):
        self.gui.window.window.present()
        dialog = Gtk.AlertDialog()
        dialog.set_message(_("Error"))
        dialog.set_detail(message)
        dialog.set_modal(False)
        dialog.show(self.gui.window.window)
