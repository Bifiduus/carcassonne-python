"""Tests for ErrorMessageView - GUI error dialog display."""

from carcassonne.presentation.gui.error_message_view import ErrorMessageView
from carcassonne.presentation.gui import error_message_view
import pytest
from unittest.mock import Mock, patch, MagicMock

pytest.importorskip("gi")


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

    # Force fallback path for environments without Gtk.AlertDialog.
    monkeypatch.delattr(error_message_view.Gtk, "AlertDialog", raising=False)

    with patch.object(error_message_view.Gtk, "Window") as mock_window_class, patch.object(
        error_message_view.Gtk, "Box"
    ) as mock_box_class, patch.object(error_message_view.Gtk, "Label") as mock_label_class, patch.object(
        error_message_view.Gtk, "Button"
    ) as mock_button_class:
        dialog = MagicMock()
        box = MagicMock()
        label = MagicMock()
        button = MagicMock()

        mock_window_class.return_value = dialog
        mock_box_class.return_value = box
        mock_label_class.return_value = label
        mock_button_class.return_value = button

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
