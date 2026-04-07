import unittest
from types import SimpleNamespace
from unittest.mock import Mock


class SingleplayerMenuTestCase(unittest.TestCase):
    def setUp(self) -> None:
        try:
            from carcassonne.presentation.gui.menus.singleplayer_menu import (
                SingleplayerMenu,
            )
        except Exception as exc:
            self.skipTest(f"GTK unavailable: {exc}")

        self.singleplayer_menu = SingleplayerMenu

    def _build_menu(self):
        game = SimpleNamespace(
            set_game_configuration=Mock(),
            save_config=Mock(),
        )
        menu = SimpleNamespace(
            gui=SimpleNamespace(game_data=SimpleNamespace(game=game)),
            file_button=SimpleNamespace(
                set_visible=Mock(),
                set_label=Mock(),
            ),
            time_box=SimpleNamespace(set_visible=Mock()),
            blitz_cb=SimpleNamespace(
                get_active=Mock(return_value=False),
                set_active=Mock(),
            ),
            contest_cb=SimpleNamespace(
                get_active=Mock(return_value=False),
                set_active=Mock(),
            ),
            river_cb=SimpleNamespace(get_active=Mock(return_value=False)),
            selected_file="/tmp/contest.txt",
        )
        menu._clear_contest_selection = (
            lambda: self.singleplayer_menu._clear_contest_selection(menu)
        )
        return menu, game

    def test_disabling_contest_clears_runtime_file_selection(self) -> None:
        menu, game = self._build_menu()

        self.singleplayer_menu.on_mode_toggle(menu, menu.contest_cb)

        self.assertIsNone(menu.selected_file)
        menu.file_button.set_visible.assert_called_once_with(False)
        menu.time_box.set_visible.assert_called_once_with(False)
        menu.file_button.set_label.assert_called_once()
        game.set_game_configuration.assert_any_call("contest_file", "")
        game.set_game_configuration.assert_any_call("blitz", False)
        game.save_config.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
