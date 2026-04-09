import configparser
import os
import json
from copy import deepcopy
import sys

from carcassonne.i18n import gettext as _

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".carcassonnerc")

FILE_KEYBIND_DEFAULTS = {
    "app.new": "n",
    "app.load": "l",
    "app.save": "s",
    "app.config": "comma",
    "app.info": "i",
    "app.quit": "q",
}

GAME_KEYBIND_DEFAULTS = {
    "app.undo": "u",
    "app.redo": "r",
    "app.pause": "p",
    "app.hint": "h",
}

DEFAULT_SETTINGS = {
    "verbose": False,
    "debug": False,
    "blitz": False,
    "contest": False,
    "time": 30,
    "river": False,
    "num_ai_players": 1,
    "ai_time": 5,
    "ai_mode": "minimax",
    "ai_minimax_depth": 80,
    "ai_minimax_scoring": "baseline",
    "ai_mcts_selection": "UCT",
    "contest_file": "",
    "file_keybinds": FILE_KEYBIND_DEFAULTS.copy(),
    "game_keybinds": GAME_KEYBIND_DEFAULTS.copy(),
}

BOOLEAN_SETTINGS = {"verbose", "debug", "blitz", "contest", "river"}
INTEGER_SETTINGS = {"time", "num_ai_players", "ai_time", "ai_minimax_depth"}
INTEGER_BOUNDS = {
    "time": (1, None),
    "num_ai_players": (1, 4),
    "ai_time": (1, None),
    "ai_minimax_depth": (1, None),
}
ENUM_SETTINGS = {
    "ai_mode": {"random", "minimax", "iterative", "mcts"},
    "ai_minimax_scoring": {"baseline", "short_term", "disruption"},
    "ai_mcts_selection": {"UCT", "ML"},
}
DICT_SETTINGS = {"file_keybinds", "game_keybinds"}
STRING_SETTINGS = {"contest_file"}
SETTING_ALIASES = {"timeout": "time"}


def _merge_keybinds(raw_keybinds, defaults: dict[str, str]) -> dict[str, str]:
    """Merge persisted keybind overrides with the default bindings.

    Args:
        raw_keybinds: Raw keybind mapping loaded from configuration.
        defaults: Default keybind mapping used as fallback.

    Returns:
        dict[str, str]: Keybind mapping containing defaults plus valid
            overrides found in `raw_keybinds`.
    """
    merged = defaults.copy()

    if not isinstance(raw_keybinds, dict):
        return merged

    for action, key in raw_keybinds.items():
        if action in defaults and isinstance(key, str) and key:
            merged[action] = key

    return merged


class GameConfiguration:
    def __init__(self, overrides=None):
        self.settings = self.load_config()
        if overrides:
            self.settings.update(overrides)
        self._normalize_time_key()
        self._normalize_keybind_settings()

    def _normalize_time_key(self):
        """Move legacy `timeout` config into the canonical `time` key."""
        if "time" not in self.settings and "timeout" in self.settings:
            self.settings["time"] = self.settings["timeout"]
        self.settings.pop("timeout", None)

    @staticmethod
    def _normalize_setting_key(key: str) -> str:
        """Validate and normalize one configuration key name.

        Args:
            key: Raw setting key provided by the caller.

        Returns:
            str: Canonical setting name, including alias resolution.
        """
        if not isinstance(key, str):
            raise TypeError("configuration key must be a string")
        normalized = key.strip()
        if not normalized:
            raise ValueError("configuration key cannot be empty")
        return SETTING_ALIASES.get(normalized, normalized)

    @staticmethod
    def _parse_bool(value) -> bool:
        """Parse one configuration value as a boolean.

        Args:
            value: Raw boolean-like value to convert.

        Returns:
            bool: Parsed boolean value.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
        raise ValueError(f"invalid boolean value: {value}")

    @staticmethod
    def _parse_int(value) -> int:
        """Parse one configuration value as an integer.

        Args:
            value: Raw integer-like value to convert.

        Returns:
            int: Parsed integer value.
        """
        if isinstance(value, bool):
            raise ValueError(f"invalid integer value: {value}")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                try:
                    return int(stripped)
                except ValueError as error:
                    raise ValueError(
                        f"invalid integer value: {value}"
                    ) from error
        raise ValueError(f"invalid integer value: {value}")

    def normalize_setting_update(self, key: str, value) -> tuple[str, object]:
        """Validate and normalize a pending setting update.

        Args:
            key: Raw configuration key to update.
            value: Raw value associated with `key`.

        Returns:
            tuple[str, object]: Normalized `(key, value)` pair ready to store
                in `self.settings`.
        """
        normalized_key = self._normalize_setting_key(key)
        if normalized_key not in DEFAULT_SETTINGS:
            raise KeyError(
                _("Unknown configuration parameter: {param}").format(
                    param=normalized_key
                )
            )

        if normalized_key in BOOLEAN_SETTINGS:
            return normalized_key, self._parse_bool(value)
        if normalized_key in INTEGER_SETTINGS:
            normalized_value = self._parse_int(value)
            minimum, maximum = INTEGER_BOUNDS.get(normalized_key, (None, None))
            if minimum is not None and normalized_value < minimum:
                raise ValueError(
                    _(
                        "Invalid value for '{param}': {value}. "
                        "Minimum allowed is {minimum}."
                    ).format(
                        param=normalized_key,
                        value=normalized_value,
                        minimum=minimum,
                    )
                )
            if maximum is not None and normalized_value > maximum:
                raise ValueError(
                    _(
                        "Invalid value for '{param}': {value}. "
                        "Maximum allowed is {maximum}."
                    ).format(
                        param=normalized_key,
                        value=normalized_value,
                        maximum=maximum,
                    )
                )
            return normalized_key, normalized_value
        if normalized_key in ENUM_SETTINGS:
            if value is None:
                raise ValueError(
                    _("Missing value for parameter '{param}'.").format(
                        param=normalized_key
                    )
                )
            normalized_value = str(value).strip()
            if normalized_key == "ai_mcts_selection":
                normalized_value = normalized_value.upper()
            else:
                normalized_value = normalized_value.lower()
            if normalized_value not in ENUM_SETTINGS[normalized_key]:
                allowed = ", ".join(sorted(ENUM_SETTINGS[normalized_key]))
                raise ValueError(
                    _(
                        "Invalid value for '{param}': {value}. "
                        "Expected one of: {allowed}."
                    ).format(
                        param=normalized_key,
                        value=value,
                        allowed=allowed,
                    )
                )
            return normalized_key, normalized_value
        if normalized_key in DICT_SETTINGS:
            if not isinstance(value, dict):
                raise ValueError(
                    _("Invalid value for '{param}':"
                      " expected a mapping.").format(
                        param=normalized_key
                    )
                )
            defaults = (
                FILE_KEYBIND_DEFAULTS
                if normalized_key == "file_keybinds"
                else GAME_KEYBIND_DEFAULTS
            )
            return normalized_key, _merge_keybinds(value, defaults)
        if normalized_key in STRING_SETTINGS:
            return normalized_key, "" if value is None else str(value)
        return normalized_key, value

    def set_setting_value(self, key: str, value) -> tuple[str, object]:
        """Apply one validated setting update to the current configuration.

        Args:
            key: Raw configuration key to update.
            value: Raw value to normalize and persist.

        Returns:
            tuple[str, object]: Normalized `(key, value)` pair stored in the
                configuration.
        """
        normalized_key, normalized_value = self.normalize_setting_update(
            key,
            value,
        )
        self.settings[normalized_key] = normalized_value
        self._normalize_keybind_settings()
        return normalized_key, normalized_value

    def _normalize_keybind_settings(self):
        """Ensure both keybind sections have all expected default actions."""
        self.settings["file_keybinds"] = _merge_keybinds(
            self.settings.get("file_keybinds"),
            FILE_KEYBIND_DEFAULTS,
        )
        self.settings["game_keybinds"] = _merge_keybinds(
            self.settings.get("game_keybinds"),
            GAME_KEYBIND_DEFAULTS,
        )

    def _write_config(self, config: configparser.ConfigParser):
        """Write a prepared config parser to the user configuration file.

        Args:
            config: Populated config parser ready to serialize.
        """
        with open(CONFIG_PATH, "w") as f:
            config.write(f, space_around_delimiters=False)

    def create_default_config(self):
        """Create the default configuration file on disk."""
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": "false",
            "debug": "false",
            "blitz": "false",
            "time": "30",
            "river": "false",
            "num_ai_players": "1",
            "ai_time": 5,
            "ai_mode": "minimax",
            "ai_minimax_depth": 83,
            "ai_minimax_scoring": "baseline",
            "ai_mcts_selection": "UCT",
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(FILE_KEYBIND_DEFAULTS),
            "game_keybinds": json.dumps(GAME_KEYBIND_DEFAULTS),
        }

        self._write_config(config)

    def load_config(self):
        """Load configuration settings from disk.

        Returns:
            dict[str, object]: Configuration dictionary built from defaults
                and file overrides when available.
        """
        config = configparser.ConfigParser()
        settings = deepcopy(DEFAULT_SETTINGS)

        # Case 1: missing file -> create it
        if not os.path.exists(CONFIG_PATH):
            self.create_default_config()
            return settings

        # Case 2/3: file exists
        try:
            config.read(CONFIG_PATH)

            if "defaults" not in config:
                raise ValueError("Missing [defaults] section")

            if config.has_option("defaults", "verbose"):
                settings["verbose"] = config.getboolean("defaults", "verbose")
            if config.has_option("defaults", "debug"):
                settings["debug"] = config.getboolean("defaults", "debug")
            if config.has_option("defaults", "blitz"):
                settings["blitz"] = config.getboolean("defaults", "blitz")
            if config.has_option("defaults", "river"):
                settings["river"] = config.getboolean("defaults", "river")

            if config.has_option("defaults", "time"):
                settings["time"] = config.getint("defaults", "time")
            elif config.has_option("defaults", "timeout"):
                # backward compatibility with previous setting name
                settings["time"] = config.getint("defaults", "timeout")
            if config.has_option("defaults", "num_ai_players"):
                settings["num_ai_players"] = config.getint(
                    "defaults", "num_ai_players"
                )
            if config.has_option("defaults", "ai_time"):
                settings["ai_time"] = config.getint("defaults", "ai_time")
            if config.has_option("defaults", "ai_mode"):
                settings["ai_mode"] = config.get("defaults", "ai_mode")
            if config.has_option("defaults", "ai_minimax_depth"):
                settings["ai_minimax_depth"] = config.getint(
                    "defaults", "ai_minimax_depth"
                )
            if config.has_option("defaults", "ai_minimax_scoring"):
                settings["ai_minimax_scoring"] = config.get(
                    "defaults", "ai_minimax_scoring"
                )
            if config.has_option("defaults", "ai_mcts_selection"):
                settings["ai_mcts_selection"] = config.get(
                    "defaults", "ai_mcts_selection"
                )
            # `contest_file` is intentionally runtime-only so a stale path
            # cannot silently reactivate contest mode on the next launch.
            if "keybinds" in config:
                if config.has_option("keybinds", "file_keybinds"):
                    settings["file_keybinds"] = _merge_keybinds(
                        json.loads(
                            config.get("keybinds", "file_keybinds")
                        ),
                        FILE_KEYBIND_DEFAULTS,
                    )
                if config.has_option("keybinds", "game_keybinds"):
                    settings["game_keybinds"] = _merge_keybinds(
                        json.loads(
                            config.get("keybinds", "game_keybinds")
                        ),
                        GAME_KEYBIND_DEFAULTS,
                    )

        except Exception as e:
            print(_("Warning: invalid configuration file."), file=sys.stderr)
            print(f"   ({e})", file=sys.stderr)
            print(_("Starting with default options."), file=sys.stderr)

        return settings

    def save_config(self):
        """Persist the current configuration to the user config file."""
        config = configparser.ConfigParser()
        config["defaults"] = {
            "verbose": str(self.settings["verbose"]).lower(),
            "debug": str(self.settings.get("debug", False)).lower(),
            "blitz": str(self.settings["blitz"]).lower(),
            "time": str(self.settings["time"]),
            "river": str(self.settings.get("river")).lower(),
            "num_ai_players": str(self.settings.get("num_ai_players", 1)),
            "ai_time": str(self.settings["ai_time"]),
            "ai_mode": str(self.settings["ai_mode"]),
            "ai_minimax_depth": str(self.settings["ai_minimax_depth"]),
            "ai_minimax_scoring": str(
                self.settings["ai_minimax_scoring"]
            ),
            "ai_mcts_selection": str(self.settings["ai_mcts_selection"]),
        }
        config["keybinds"] = {
            "file_keybinds": json.dumps(self.settings["file_keybinds"]),
            "game_keybinds": json.dumps(self.settings["game_keybinds"]),
        }

        self._write_config(config)

    def show_config(self):
        """Print the current configuration values to standard output."""
        print(_("Current game configuration:"))
        for key, value in self.settings.items():
            print(f"  {key}: {value}")

    def get_setting(self):
        """Return a copy of the full configuration mapping.

        Returns:
            dict[str, object]: Snapshot of all stored settings.
        """
        return self.settings.copy()

    def get_setting_value(self, key):
        """Return the value associated with one configuration key.

        Args:
            key: Setting name to look up.

        Returns:
            object | None: Stored value for `key`, or None if absent.
        """
        return self.settings.get(key)
