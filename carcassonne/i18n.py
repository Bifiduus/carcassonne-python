"""Internationalization helpers for the Carcassonne application."""

from __future__ import annotations

import ast
import builtins
from gettext import NullTranslations, translation
import locale
import os
from pathlib import Path
import sys
from typing import Callable, Mapping, MutableMapping

TEXT_DOMAIN = "carcassonne"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = frozenset({"en", "fr"})
LOCALE_DIR = Path(__file__).resolve().parent / "locale"
SYSTEM_LOCALE_CANDIDATES = {
    "en": ("en_US.UTF-8", "en_US.utf8", "C.UTF-8", "C.utf8", "C"),
    "fr": ("fr_FR.UTF-8", "fr_FR.utf8", "fr_FR"),
}

_TRANSLATION: NullTranslations = NullTranslations()
CURRENT_LANGUAGE = DEFAULT_LANGUAGE


class POTranslations(NullTranslations):
    """Minimal `.po` loader used when compiled catalogs are unavailable."""

    def __init__(self, po_file: Path):
        super().__init__()
        self._catalog = self._parse_catalog(po_file)

    @staticmethod
    def _parse_catalog(po_file: Path) -> dict[str, str]:
        catalog: dict[str, str] = {}
        state: str | None = None
        current_msgid: str | None = None
        current_msgstr: str | None = None
        is_fuzzy = False

        def flush_entry() -> None:
            nonlocal current_msgid, current_msgstr, is_fuzzy
            if (
                current_msgid is not None
                and current_msgstr is not None
                and current_msgid != ""
                and not is_fuzzy
            ):
                catalog[current_msgid] = current_msgstr
            current_msgid = None
            current_msgstr = None
            is_fuzzy = False

        with po_file.open(encoding="utf-8") as stream:
            for raw_line in stream:
                line = raw_line.rstrip("\n")
                stripped = line.strip()

                if stripped == "":
                    flush_entry()
                    state = None
                    continue

                if stripped.startswith("#,") and "fuzzy" in stripped:
                    is_fuzzy = True
                    continue

                if stripped.startswith("#"):
                    continue

                if stripped.startswith("msgid "):
                    flush_entry()
                    current_msgid = ast.literal_eval(stripped[5:].strip())
                    state = "msgid"
                    continue

                if stripped.startswith("msgstr "):
                    current_msgstr = ast.literal_eval(stripped[6:].strip())
                    state = "msgstr"
                    continue

                if stripped.startswith('"'):
                    value = ast.literal_eval(stripped)
                    if state == "msgid" and current_msgid is not None:
                        current_msgid += value
                    elif state == "msgstr" and current_msgstr is not None:
                        current_msgstr += value

        flush_entry()
        return catalog

    def gettext(self, message: str) -> str:
        return self._catalog.get(message, message)


def gettext(message: str) -> str:
    """Return the translated message for the active language."""

    return _TRANSLATION.gettext(message)


def get_language_from_environment(
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Return the locale requested by the environment, if any."""

    environment = os.environ if env is None else env
    for variable in ("LC_ALL", "LANG"):
        value = environment.get(variable)
        if value:
            return value
    return None


def normalize_language(locale_value: str | None) -> str | None:
    """Collapse locale variants such as `fr_FR.UTF-8` to `fr`."""

    if locale_value is None:
        return None

    candidate = locale_value.strip()
    if candidate == "":
        return None

    candidate = candidate.split(".", 1)[0]
    candidate = candidate.split("@", 1)[0]
    candidate = candidate.replace("-", "_").lower()

    if candidate in {"c", "posix"}:
        return DEFAULT_LANGUAGE

    language = candidate.split("_", 1)[0]
    return language or None


def is_language_supported(language: str | None) -> bool:
    """Return True when the language is supported by the application."""

    return bool(language in SUPPORTED_LANGUAGES)


def is_system_locale_supported(locale_name: str) -> bool:
    """Return True when the C library accepts the locale name."""

    current_locale = locale.setlocale(locale.LC_ALL)
    try:
        locale.setlocale(locale.LC_ALL, locale_name)
    except locale.Error:
        return False
    finally:
        try:
            locale.setlocale(locale.LC_ALL, current_locale)
        except locale.Error:
            pass
    return True


def get_supported_system_locale(
    language: str,
    locale_is_supported: Callable[[str], bool] | None = None,
) -> str | None:
    """Return an installed system locale matching the application language."""

    checker = is_system_locale_supported
    if locale_is_supported is not None:
        checker = locale_is_supported

    for candidate in SYSTEM_LOCALE_CANDIDATES.get(language, ()):
        if checker(candidate):
            return candidate
    return None


def prepare_gui_locale(
    language: str,
    env: MutableMapping[str, str] | None = None,
    locale_is_supported: Callable[[str], bool] | None = None,
) -> str | None:
    """Rewrite short or invalid locale names before GTK initializes."""

    environment = os.environ if env is None else env
    checker = is_system_locale_supported
    if locale_is_supported is not None:
        checker = locale_is_supported

    requested_locale = get_language_from_environment(environment)
    if requested_locale and checker(requested_locale):
        return requested_locale

    supported_locale = get_supported_system_locale(
        language,
        locale_is_supported=checker,
    )
    if supported_locale is None:
        return None

    target_variable = "LC_ALL" if environment.get("LC_ALL") else "LANG"
    environment[target_variable] = supported_locale
    return supported_locale


def _load_translation(language: str) -> NullTranslations:
    try:
        return translation(
            TEXT_DOMAIN,
            localedir=str(LOCALE_DIR),
            languages=[language],
        )
    except FileNotFoundError:
        po_file = LOCALE_DIR / language / "LC_MESSAGES" / f"{TEXT_DOMAIN}.po"
        if po_file.exists():
            return POTranslations(po_file)
        return NullTranslations()


def configure_i18n(
    env: Mapping[str, str] | None = None,
    stderr=None,
) -> str:
    """Install the translation selected from `LC_ALL` or `LANG`."""

    global _TRANSLATION, CURRENT_LANGUAGE

    err_stream = sys.stderr if stderr is None else stderr
    requested_locale = get_language_from_environment(env)
    selected_language = DEFAULT_LANGUAGE

    if requested_locale is not None:
        normalized_language = normalize_language(requested_locale)
        if is_language_supported(normalized_language):
            selected_language = normalized_language or DEFAULT_LANGUAGE
        else:
            print(
                (
                    "Warning: unsupported language "
                    f"'{requested_locale}'. Falling back to English."
                ),
                file=err_stream,
            )

    _TRANSLATION = _load_translation(selected_language)
    CURRENT_LANGUAGE = selected_language
    builtins.__dict__["_"] = gettext
    return CURRENT_LANGUAGE
