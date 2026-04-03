"""Internationalization helpers for the Carcassonne application."""

from __future__ import annotations

import ast
import builtins
from gettext import NullTranslations, translation
import os
from pathlib import Path
import sys
from typing import Mapping

TEXT_DOMAIN = "carcassonne"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = frozenset({"en", "fr"})
LOCALE_DIR = Path(__file__).resolve().parent / "locale"

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
