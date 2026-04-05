"""Utility helpers shared by several GUI modules."""

import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gtk, Gdk, Gio  # noqa: E402


def get_images_dir() -> str:
    """Return the path to the "Images" directory inside the GUI package."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "Images")


def tile_image_path(name: str | None) -> str:
    """Convert a tile name (possibly including a "/") to its PNG path.

    The GUI used to duplicate this logic in several places; centralising
    it here makes it easier to test and maintain.
    """
    images_dir = get_images_dir()
    if not name:
        return ""
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
        font-family: "DejaVu Sans Mono", monospace;
        font-size: 42px;
        font-weight: bold;
        letter-spacing: 0px;
        color: #fffdfb;
        letter-spacing: 2px;
        text-shadow: -1px -1px 0 #000, 1px -1px 0 #000,
                 -1px 1px 0 #000, 1px 1px 0 #000;
    }

    .section-title {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 36px;
    font-weight: 900;
    letter-spacing: 0px;
    color: #fffdfb;
    text-shadow: -1px -1px 0 #000, 1px -1px 0 #000,
                 -1px 1px 0 #000, 1px 1px 0 #000;
    }

    /*orange buttons*/
    .orange-buttons {
    background: #ff8032;
    color: black;
    border-radius: 10px;
    padding: 10px;
    font-weight: bold;
    border: none;
    transition: all 0.25s ease;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    /* Hover */
    .orange-buttons:hover {
        background: linear-gradient(135deg, #94FF4A, #30A61E);
        transform: translateY(-2px);
    }

    /* Click */
    .orange-buttons:active {
        transform: scale(0.96);
    }
    /* Focus (clavier) */
    .orange-buttons:focus {
        outline: 2px solid white;
        outline-offset: 2px;
    }

    /*red buttons*/
    .red-buttons {
    background: #ff3737;
    color: black;
    border-radius: 10px;
    padding: 10px;
    font-weight: bold;
    border: none;
    transition: all 0.25s ease;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    /* Hover */
    .red-buttons:hover {
        background: linear-gradient(135deg, #94FF4A, #30A61E);
        transform: translateY(-2px);
    }

    /* Click */
    .red-buttons:active {
        transform: scale(0.96);
    }
    /* Focus (clavier) */
    .red-buttons:focus {
        outline: 2px solid white;
        outline-offset: 2px;
    }
    /*header buttons*/
    /*.headers_buttons {
    background: #ab8ee7;
    color: black;
    border-radius: 10px;
    padding: 10px;
    font-weight: bold;
    border: none;
    transition: all 0.25s ease;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    outline: 2px solid white;
    outline-offset: 2px;
    }*/



    """

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
