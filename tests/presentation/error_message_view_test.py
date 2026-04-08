"""Tests for ErrorMessageView - GUI error dialog display."""

from carcassonne.presentation.gui.error_message_view import ErrorMessageView
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
