from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("gi")

from carcassonne.presentation.gui import utils


def test_get_images_dir_points_to_gui_images_folder() -> None:
    images_dir = utils.get_images_dir()

    assert images_dir.endswith("carcassonne/presentation/gui/Images")


def test_tile_image_path_handles_empty_plain_and_slash_names() -> None:
    assert utils.tile_image_path(None) == ""
    assert utils.tile_image_path("") == ""

    plain = utils.tile_image_path("CFFF")
    slash = utils.tile_image_path("CDFF/5E1")

    assert plain.endswith("/Images/CFFF.png")
    assert slash.endswith("/Images/CDFF5E1.png")


def test_register_action_creates_connects_and_registers_action(monkeypatch) -> None:
    action = Mock()
    new_action = Mock(return_value=action)
    monkeypatch.setattr(utils.Gio.SimpleAction, "new", new_action)

    callback = Mock()
    app = Mock()

    utils.register_action(app, "draw", callback)

    new_action.assert_called_once_with("draw", None)
    action.connect.assert_called_once_with("activate", callback)
    app.add_action.assert_called_once_with(action)


def test_load_css_installs_provider_on_default_display(monkeypatch) -> None:
    provider = Mock()
    provider.load_from_data = Mock()

    css_provider_ctor = Mock(return_value=provider)
    add_provider = Mock()
    display = object()
    get_default_display = Mock(return_value=display)

    monkeypatch.setattr(utils.Gtk, "CssProvider", css_provider_ctor)
    monkeypatch.setattr(
        utils.Gtk.StyleContext,
        "add_provider_for_display",
        add_provider,
    )
    monkeypatch.setattr(utils.Gdk.Display, "get_default", get_default_display)

    utils.load_css()

    css_provider_ctor.assert_called_once_with()
    provider.load_from_data.assert_called_once()
    css_bytes = provider.load_from_data.call_args.args[0]
    assert b".corner-panel" in css_bytes
    add_provider.assert_called_once_with(
        display,
        provider,
        utils.Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
