"""Add the installed app folder to sys.path for the bundled Python.

Embeddable CPython reads python*._pth and then does not put the current
working directory on sys.path. Flask and the MCP server both import
`lessons` from {install}/app.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _add_app_dir() -> None:
    python_dir = Path(__file__).resolve().parent
    app_dir = python_dir.parent / "app"
    if not app_dir.is_dir():
        return
    path = str(app_dir)
    if path not in sys.path:
        sys.path.insert(0, path)


_add_app_dir()
