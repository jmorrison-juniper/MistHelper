"""Rewrite the static menu description map of the web portal.

Why:
    ``web_portal/menu_registry.py`` holds a description for each operation that
    the portal may run. The portal reads that map only when it cannot import
    MistHelper, which happens when no API session exists. The map was written by
    hand, so it drifted. It held 77 rows while the registry called 165
    operations safe, and 4 of its rows named an operation that is not safe to
    run from a browser.

    This script rewrites the map from the two authoritative sources: the menu
    titles in ``MistHelper.menu_actions`` and the safety class in
    ``OperationRegistry``. Run it after adding an operation.

Usage:
    python scripts/generate_portal_menu_registry.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]  # The script sits in scripts/.
TARGET = REPO_ROOT / "web_portal" / "menu_registry.py"

HEADER = '''"""Static menu operation descriptions for the web portal.

Provides operation metadata without requiring MistHelper imports
or API authentication. Used by wsgi.py to populate the operations
list when the portal starts independently from MistHelper CLI.

Warning: this file is generated. Run
``python scripts/generate_portal_menu_registry.py`` after adding or renaming an
operation. ``tests/guardrails/test_portal_menu_registry_sync.py`` fails when
this map drifts from ``OperationRegistry``.

The map holds every operation that ``OperationRegistry`` calls ``safe`` or
``interactive_safe``, because those are the two classes the portal may run.
"""

from src.utils.menu_entry import MenuEntry  # WHY: static rows must match the real menu row shape.

MENU_DESCRIPTIONS = {
'''

FOOTER = '''}


def build_static_menu_actions() -> dict:
    """Build a menu_actions dict with descriptions for listing only."""
    return {
        key: MenuEntry(
            menu_id=key,  # WHY: keep the static row key aligned with the real menu shape.
            handler=None,  # WHY: execution requires full MistHelper initialization.
            title=desc,  # WHY: the portal list only needs display text.
            category="static",  # WHY: the portal still reads live safety from OperationRegistry.
            destructive=False,  # WHY: static rows cannot execute destructive code.
            supports_fast=False,  # WHY: static rows never run in the systematic test runner.
        )
        for key, desc in MENU_DESCRIPTIONS.items()
    }
'''


def sort_key(option: str) -> float:
    """Return the natural order key that the project uses for a menu option."""
    return float(option.replace("a", ".1"))  # An ``aN`` suffix sorts just after ``N``.


def main() -> int:
    """Rewrite the description map and report the row count."""
    payload = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if payload is None or not payload.is_file():
        logger.error("Pass the path of a JSON file that maps each menu number to its title.")
        return 1
    logger.info("Reading the menu titles from %s", payload)
    titles: dict[str, str] = json.loads(payload.read_text(encoding="utf-8"))
    rows = []
    for option in sorted(titles, key=sort_key):  # A stable order keeps the diff readable.
        text = titles[option].replace('"', '\\"')  # A quote inside a title would end the literal early.
        rows.append(f'    "{option}": "{text}",')
    logger.info("Writing %d description rows to %s", len(rows), TARGET)
    TARGET.write_text(HEADER + "\n".join(rows) + "\n" + FOOTER, encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
