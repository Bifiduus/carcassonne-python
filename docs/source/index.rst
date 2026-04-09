carcassonne documentation
=========================

Carcassonne Python is a Python implementation of the Carcassonne board game
with both a command-line interface and a GTK4 graphical interface.

Overview
========

The project provides a playable version of the game together with several
runtime modes and support modules:

* CLI and GTK4 GUI frontends
* AI opponents including ``random``, ``minimax``, ``iterative``, and ``mcts``
* Optional ML-assisted MCTS selection
* Blitz mode, river mode, and contest mode
* Save and load support for game states
* Client and server components for multiplayer-related workflows

Documentation Map
=================

Use the generated API reference to navigate the Python packages and modules:

* ``carcassonne.business_logic`` for game rules, AI, save/load, and networking
* ``carcassonne.datas`` for data models, deck handling, and persistence helpers
* ``carcassonne.interfaces`` for shared interfaces
* ``carcassonne.presentation`` for CLI and GTK4 frontends

The main developer entry point for rebuilding this documentation is:

.. code-block:: bash

   make -C docs html PYTHON=python3

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   carcassonne.presentation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
