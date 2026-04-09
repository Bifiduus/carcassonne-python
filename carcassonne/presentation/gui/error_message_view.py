"""Error dialog helpers for the GTK interface."""

import gi
import importlib
from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")
Gtk = importlib.import_module("gi.repository.Gtk")


class ErrorMessageView:
    """Display non-blocking error dialogs tied to the application window."""

    def __init__(self, gui):
        """Store parent GUI reference used as transient window parent."""
        self.gui = gui

    def show_error(self, message: str):
        """Display an error message using AlertDialog or a fallback window."""
        self.gui.window.window.present()
        if hasattr(Gtk, "AlertDialog"):
            dialog = Gtk.AlertDialog()
            dialog.set_message(_("Error"))
            dialog.set_detail(message)
            dialog.set_modal(False)
            dialog.show(self.gui.window.window)
            return

        # Fallback for Gtk versions where AlertDialog is unavailable.
        dialog = Gtk.Window(title=_("Error"))
        dialog.set_modal(False)
        dialog.set_transient_for(self.gui.window.window)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        label = Gtk.Label(label=message)
        label.set_wrap(True)
        box.append(label)

        button = Gtk.Button(label=_("OK"))
        button.connect("clicked", lambda _: dialog.close())
        box.append(button)

        dialog.set_child(box)
        dialog.present()
