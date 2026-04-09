import io
import unittest

from carcassonne import i18n


class I18NTestCase(unittest.TestCase):
    def tearDown(self):
        i18n.configure_i18n(env={}, stderr=io.StringIO())

    def test_defaults_to_english_when_no_environment_variable_is_set(self):
        stderr = io.StringIO()

        language = i18n.configure_i18n(env={}, stderr=stderr)

        self.assertEqual(language, "en")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(i18n.gettext("Quit"), "Quit")

    def test_lang_is_used_for_supported_french_locale(self):
        stderr = io.StringIO()

        language = i18n.configure_i18n(
            env={"LANG": "fr_FR.UTF-8"},
            stderr=stderr,
        )

        self.assertEqual(language, "fr")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(i18n.gettext("Quit"), "Quitter")
        self.assertEqual(
            i18n.gettext("Welcome to Carcassonne"),
            "Bienvenue dans Carcassonne",
        )

    def test_lc_all_has_priority_over_lang(self):
        stderr = io.StringIO()

        language = i18n.configure_i18n(
            env={
                "LANG": "fr_FR.UTF-8",
                "LC_ALL": "en_US.UTF-8",
            },
            stderr=stderr,
        )

        self.assertEqual(language, "en")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(i18n.gettext("Quit"), "Quit")

    def test_unsupported_language_warns_and_falls_back_to_english(self):
        stderr = io.StringIO()

        language = i18n.configure_i18n(
            env={"LANG": "es_ES.UTF-8"},
            stderr=stderr,
        )

        self.assertEqual(language, "en")
        self.assertIn("unsupported language 'es_ES.UTF-8'", stderr.getvalue())
        self.assertEqual(i18n.gettext("Quit"), "Quit")

    def test_normalize_language_keeps_supported_short_code(self):
        self.assertEqual(i18n.normalize_language("fr"), "fr")
        self.assertEqual(i18n.normalize_language("en_US.UTF-8"), "en")
        self.assertEqual(i18n.normalize_language("fr-FR@euro"), "fr")

    def test_prepare_gui_locale_rewrites_short_lang_for_gtk(self):
        env = {"LANG": "fr"}

        selected_locale = i18n.prepare_gui_locale(
            "fr",
            env=env,
            locale_is_supported=lambda locale_name: (
                locale_name == "fr_FR.UTF-8"
            ),
        )

        self.assertEqual(selected_locale, "fr_FR.UTF-8")
        self.assertEqual(env["LANG"], "fr_FR.UTF-8")

    def test_prepare_gui_locale_preserves_supported_locale(self):
        env = {"LANG": "fr_FR.UTF-8"}

        selected_locale = i18n.prepare_gui_locale(
            "fr",
            env=env,
            locale_is_supported=lambda locale_name: (
                locale_name == "fr_FR.UTF-8"
            ),
        )

        self.assertEqual(selected_locale, "fr_FR.UTF-8")
        self.assertEqual(env["LANG"], "fr_FR.UTF-8")

    def test_prepare_gui_locale_updates_lc_all_when_present(self):
        env = {"LANG": "fr", "LC_ALL": "fr"}

        selected_locale = i18n.prepare_gui_locale(
            "fr",
            env=env,
            locale_is_supported=lambda locale_name: (
                locale_name == "fr_FR.UTF-8"
            ),
        )

        self.assertEqual(selected_locale, "fr_FR.UTF-8")
        self.assertEqual(env["LC_ALL"], "fr_FR.UTF-8")
        self.assertEqual(env["LANG"], "fr")


if __name__ == "__main__":
    unittest.main()
