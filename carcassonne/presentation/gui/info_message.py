from gi.repository import Gtk
import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class InfoMessage:
    def __init__(self, gui):
        self.gui = gui

    def show_info(self, message: str):
        dialog = Gtk.Dialog()
        dialog.set_title(_("Information"))
        dialog.set_modal(False)
        dialog.set_transient_for(self.gui.window.window)

        # Create a text view for long text
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        buffer = text_view.get_buffer()
        buffer.set_text(message)

        # Put in a scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(text_view)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)  # Minimum height for readability
        scrolled.set_min_content_width(400)  # Minimum width

        # Add to dialog content area
        dialog.get_content_area().append(scrolled)

        dialog.add_button(_("OK"), Gtk.ResponseType.OK)
        dialog.connect("response", lambda d, r: d.destroy())

        dialog.present()
