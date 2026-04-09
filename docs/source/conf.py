import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

import carcassonne

project = "carcassonne"
copyright = (
    "2026, Clément SIMON, Maxence SALIN, Loic THIN, "
    "Anthony BEAUVIEUX, Tony HUANG"
)
author = (
    "Clément SIMON, Maxence SALIN, Loic THIN, "
    "Anthony BEAUVIEUX, Tony HUANG"
)
release = carcassonne.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

exclude_patterns = []

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_mock_imports = ["gi", "gi.repository"]

html_theme = "sphinx_rtd_theme"
