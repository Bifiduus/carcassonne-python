"""Utility helpers shared by several GUI modules."""

import os

from gi.repository import Gtk, Gdk, Gio


def get_images_dir() -> str:
    """Return the path to the "Images" directory inside the GUI package."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "Images")


def tile_image_path(name: str) -> str:
    """Convert a tile name (possibly including a "/") to its PNG path.

    The GUI used to duplicate this logic in several places; centralising
    it here makes it easier to test and maintain.
    """
    images_dir = get_images_dir()
    if "/" in name:
        parts = name.split("/")
        return os.path.join(images_dir, f"{parts[0]}{parts[1]}.png")
    return os.path.join(images_dir, f"{name}.png")


def load_css() -> None:
    """Install a tiny bit of application-wide CSS used by the GUI."""
    css = """
    .corner-panel {
        background-color: rgba(0, 0, 0, 0.6);
        border: 3px solid white;
        border-radius: 12px;
        padding: 12px;
    }
    .end-turn-panel {
        background-color: rgba(255, 125, 0, 0.6);
        border: 3px solid white;
        border-radius: 4px;
        padding: 4px;
    }
    .players-panel {
        background-color: rgba(255, 125, 0, 0.6);
        border: 3px solid white;
        border-radius: 4px;
        padding: 4px;
    }

    .current-player {
        background-color: rgba(255,255,255,0.15);
        border-radius: 6px;
        padding: 4px;
    }
    .main-title {
        font-size: 24px;
        font-weight: bold;
        color: orange;
    }
    .back-button {
        background-color: rgba(255, 0, 0, 0.8);
        border: 2px solid white;
        border-radius: 8px;
        color: red;
        font-weight: bold;
    }
    .back-button:hover {
        background-color: rgba(255, 0, 0, 1.0);
    }"""

    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode())

    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def register_action(application, name: str, callback) -> None:
    """Helper wrapper for creating and registering a simple action."""
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    application.add_action(action)
