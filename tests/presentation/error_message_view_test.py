"""Tests for ErrorMessageView - GUI error dialog display."""

from types import SimpleNamespace
from unittest.mock import Mock, patch, MagicMock

import pytest

pytest.importorskip("gi")

from carcassonne.presentation.gui import error_message_view  # noqa: E402
from carcassonne.presentation.gui.error_message_view import (  # noqa: E402
    ErrorMessageView,
)


def test_error_message_view_initialization() -> None:
    gui = Mock()
    error_view = ErrorMessageView(gui)

    assert error_view.gui is gui


def test_show_error_creates_alert_dialog() -> None:
    gui = Mock()
    gui.window.window = Mock()
    error_view = ErrorMessageView(gui)

    with patch(
        "carcassonne.presentation.gui.error_message_view.Gtk.AlertDialog",
        create=True,
    ) as mock_dialog_class:
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        error_view.show_error("Test error message")

        # Verify dialog was created and configured
        mock_dialog.set_message.assert_called_once()
        mock_dialog.set_detail.assert_called_once_with("Test error message")
        mock_dialog.set_modal.assert_called_once_with(False)
        mock_dialog.show.assert_called_once_with(gui.window.window)


def test_show_error_presents_gui_window() -> None:
    gui = Mock()
    gui.window.window = Mock()
    error_view = ErrorMessageView(gui)

    with patch(
        "carcassonne.presentation.gui.error_message_view.Gtk.AlertDialog",
        create=True,
    ):
        error_view.show_error("Error message")

        gui.window.window.present.assert_called_once()


def test_show_error_with_different_messages() -> None:
    gui = Mock()
    gui.window.window = Mock()
    error_view = ErrorMessageView(gui)

    messages = [
        "Invalid move",
        "Network connection lost",
        "Game save failed",
    ]

    with patch(
        "carcassonne.presentation.gui.error_message_view.Gtk.AlertDialog",
        create=True,
    ) as mock_dialog_class:
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        for msg in messages:
            error_view.show_error(msg)
            mock_dialog.set_detail.assert_called_with(msg)


def test_show_error_fallback_when_alert_dialog_is_unavailable(
    monkeypatch,
) -> None:
    gui = Mock()
    gui.window.window = Mock()
    error_view = ErrorMessageView(gui)

    dialog = MagicMock()
    box = MagicMock()
    label = MagicMock()
    button = MagicMock()
    fake_gtk = SimpleNamespace(
        Window=MagicMock(return_value=dialog),
        Box=MagicMock(return_value=box),
        Label=MagicMock(return_value=label),
        Button=MagicMock(return_value=button),
        Orientation=SimpleNamespace(VERTICAL="vertical"),
    )

    # Force fallback path with a Gtk replacement that does not expose
    # AlertDialog, which is more reliable than deleting attributes from
    # the GI proxy module.
    monkeypatch.setattr(error_message_view, "Gtk", fake_gtk)

    error_view.show_error("Fallback error")

    gui.window.window.present.assert_called_once()
    dialog.set_modal.assert_called_once_with(False)
    dialog.set_transient_for.assert_called_once_with(gui.window.window)
    box.set_margin_top.assert_called_once_with(16)
    box.set_margin_bottom.assert_called_once_with(16)
    box.set_margin_start.assert_called_once_with(16)
    box.set_margin_end.assert_called_once_with(16)
    box.append.assert_any_call(label)
    box.append.assert_any_call(button)
    dialog.set_child.assert_called_once_with(box)
    dialog.present.assert_called_once()

    # Verify connected callback closes the dialog.
    click_handler = button.connect.call_args.args[1]
    click_handler(None)
    dialog.close.assert_called_once()
