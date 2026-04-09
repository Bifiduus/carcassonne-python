"""Tests for InfoMessage - GUI information dialog display."""

from carcassonne.presentation.gui.info_message import InfoMessage
import pytest
from unittest.mock import Mock, patch, MagicMock

pytest.importorskip("gi")


def test_info_message_initialization() -> None:
    gui = Mock()
    info_msg = InfoMessage(gui)

    assert info_msg.gui is gui


def test_show_info_creates_dialog() -> None:
    gui = Mock()
    gui.window.window = Mock()
    info_msg = InfoMessage(gui)

    with patch(
        "carcassonne.presentation.gui.info_message.Gtk.Dialog"
    ) as mock_dialog_class, patch(
        "carcassonne.presentation.gui.info_message.Gtk.TextView"
    ) as mock_text_view_class, patch(
        "carcassonne.presentation.gui.info_message.Gtk.ScrolledWindow"
    ) as mock_scrolled_class:
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        mock_text_view_class.return_value = MagicMock()
        mock_scrolled_class.return_value = MagicMock()
        mock_dialog.get_content_area.return_value = MagicMock()

        info_msg.show_info("Test info message")

        # Verify dialog setup
        mock_dialog.set_title.assert_called_once()
        mock_dialog.set_modal.assert_called_once_with(False)
        mock_dialog.set_transient_for.assert_called_once_with(
            gui.window.window)


def test_show_info_creates_text_view() -> None:
    gui = Mock()
    gui.window.window = Mock()
    info_msg = InfoMessage(gui)

    with patch("carcassonne.presentation.gui.info_message.Gtk.Dialog") as mock_dialog_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.TextView") as mock_text_view_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.ScrolledWindow") as mock_scrolled_class:

        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        mock_text_view = MagicMock()
        mock_text_view_class.return_value = mock_text_view
        mock_scrolled = MagicMock()
        mock_scrolled_class.return_value = mock_scrolled
        mock_dialog.get_content_area.return_value = MagicMock()

        info_msg.show_info("Test info")

        # Verify text view is created and configured
        mock_text_view.set_editable.assert_called_once_with(False)
        mock_text_view.set_wrap_mode.assert_called_once()


def test_show_info_configures_scrolled_window() -> None:
    gui = Mock()
    gui.window.window = Mock()
    info_msg = InfoMessage(gui)

    with patch("carcassonne.presentation.gui.info_message.Gtk.Dialog") as mock_dialog_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.TextView"), \
            patch("carcassonne.presentation.gui.info_message.Gtk.ScrolledWindow") as mock_scrolled_class:

        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        mock_scrolled = MagicMock()
        mock_scrolled_class.return_value = mock_scrolled
        mock_dialog.get_content_area.return_value = MagicMock()

        info_msg.show_info("Test info")

        # Verify scrolled window configuration
        mock_scrolled.set_min_content_height.assert_called_once_with(200)
        mock_scrolled.set_min_content_width.assert_called_once_with(400)


def test_show_info_adds_ok_button() -> None:
    gui = Mock()
    gui.window.window = Mock()
    info_msg = InfoMessage(gui)

    with patch("carcassonne.presentation.gui.info_message.Gtk.Dialog") as mock_dialog_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.TextView"), \
            patch("carcassonne.presentation.gui.info_message.Gtk.ScrolledWindow"):

        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        mock_dialog.get_content_area.return_value = MagicMock()

        info_msg.show_info("Test info")

        # Verify OK button was added
        assert mock_dialog.add_button.called


def test_show_info_with_different_messages() -> None:
    gui = Mock()
    gui.window.window = Mock()
    info_msg = InfoMessage(gui)

    messages = [
        "Welcome to Carcassonne",
        "Game saved successfully",
        "Very long information message " * 10,
    ]

    with patch("carcassonne.presentation.gui.info_message.Gtk.Dialog") as mock_dialog_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.TextView") as mock_text_view_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.ScrolledWindow"):

        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        mock_text_view = MagicMock()
        mock_text_view_class.return_value = mock_text_view
        mock_dialog.get_content_area.return_value = MagicMock()

        for msg in messages:
            info_msg.show_info(msg)
            # Verify set_text was called with the message
            mock_text_view.get_buffer.return_value.set_text.assert_called()


def test_show_info_presents_dialog() -> None:
    gui = Mock()
    gui.window.window = Mock()
    info_msg = InfoMessage(gui)

    with patch("carcassonne.presentation.gui.info_message.Gtk.Dialog") as mock_dialog_class, \
            patch("carcassonne.presentation.gui.info_message.Gtk.TextView"), \
            patch("carcassonne.presentation.gui.info_message.Gtk.ScrolledWindow"):

        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        mock_dialog.get_content_area.return_value = MagicMock()

        info_msg.show_info("Test info")

        # Verify dialog is presented
        mock_dialog.present.assert_called_once()
