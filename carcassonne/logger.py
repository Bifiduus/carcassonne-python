"""Logging configuration for Carcassonne.

Two log levels are supported:
- INFO  (verbose mode, -v): game-level events (turn, placement, scoring).
- DEBUG (debug mode, -d):   technical internals (merges, validation, AI).

Usage in any submodule::

    import logging
    logger = logging.getLogger(__name__)
    logger.info("some event")
    logger.debug("internal detail")
"""

import logging
import sys

_PACKAGE_LOGGER = "carcassonne"


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Configure the carcassonne package logger level.

    Args:
        verbose: Enable INFO-level messages (game events).
        debug: Enable DEBUG-level messages (internal details).
            Supersedes verbose when both are set.

    Returns:
        None.
    """
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING  # Silent default

    pkg_logger = logging.getLogger(_PACKAGE_LOGGER)
    pkg_logger.setLevel(level)
    pkg_logger.propagate = False  # Don't propagate to root logger

    # Reuse existing handler if available, otherwise create new one
    if pkg_logger.handlers:
        handler = pkg_logger.handlers[0]
    else:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        pkg_logger.addHandler(handler)
    handler.setLevel(level)
