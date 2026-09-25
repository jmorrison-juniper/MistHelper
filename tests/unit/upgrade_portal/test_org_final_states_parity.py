"""Unit tests that the page script and the service name one set of final states.

Why:
    Issue #3225. The service refuses a cancel of a final operation, and the
    page poll stops on the final states. If the two lists differ, the page
    polls a final operation again, or it stops the poll of a live operation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.firmware.aggregate_upgrade_service import FINAL_OPERATION_STATES

REPO_ROOT = Path(__file__).resolve().parents[3]  # The root of the repository.
SCRIPT_PATH = REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets" / "static" / "js" / "portal.js"
LIST_PATTERN = re.compile(r"var ORG_UPGRADE_FINISHED_STATES = (\[[^\]]*\]);")  # The list of the poll rule.


def test_the_page_script_stops_the_poll_on_the_final_states_of_the_service() -> None:
    """The poll rule of the page script and the cancel rule of the service read one set."""
    match = LIST_PATTERN.search(SCRIPT_PATH.read_text(encoding="utf-8"))  # The list in the script.
    assert isinstance(match, re.Match), "portal.js holds no list of the finished multi-site states."
    assert frozenset(json.loads(match.group(1))) == FINAL_OPERATION_STATES  # The same three words.
