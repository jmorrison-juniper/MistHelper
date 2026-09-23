"""Guard the Execution Log against internal plumbing lines.

Issue #3229: the dependency resolver and the bootstrap log each step at INFO,
because the repository logging standard requires an INFO record before each
action. The portal showed those lines in the Execution Log. In menu 4, about
12 of the 22 visible lines were plumbing, and the result sat between them.

The portal routes an INFO message to the Debug Log panel when the message
starts with a prefix in ``_RunLogHandler._INTERNAL_PREFIXES``. These tests
hold three contracts: each plumbing line goes to the debug panel, each
operator line stays in the Execution Log, and each plumbing call in the
source still matches a prefix, so a reworded message cannot slip back.
"""

import ast
import logging
from pathlib import Path

import pytest

from web_portal.services.operation import _RunLogHandler

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

# The modules whose INFO lines describe plumbing rather than the operation.
PLUMBING_MODULES = (
    "src/config/source_dependency_resolver.py",
    "src/config/config_utils.py",
    "src/refactors/main_entrypoint.py",
)

# The message stems that mark a plumbing line in those modules.
PLUMBING_STEMS = ("Resolving ", "Selecting the bootstrap", "Activating the bootstrap", "Setting the active application")


def _handler() -> _RunLogHandler:
    """Return a handler bound to an empty run record, with no event bus."""
    run = {"run_id": "test-run", "log_messages": [], "debug_messages": [], "output_files": []}
    return _RunLogHandler(run, None)


def _record(message: str, level: int = logging.INFO, name: str = "src.config.source_dependency_resolver"):
    """Build one log record as the handler would receive it."""
    return logging.LogRecord(name, level, __file__, 1, message, None, None)


def _plumbing_messages() -> list[str]:
    """Return the literal message of each plumbing INFO call in the source modules."""
    found: list[str] = []
    for relative in PLUMBING_MODULES:
        tree = ast.parse((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "info"):
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                continue
            text = node.args[0].value
            if text.startswith(PLUMBING_STEMS):
                found.append(text.replace("%s", "DataExporter"))  # Render the argument as a real run would.
    return found


PLUMBING_MESSAGES = _plumbing_messages()


def test_the_source_still_holds_the_plumbing_calls():
    """The guard below means something only while the calls exist."""
    # Measured on 2026-09-23: eight plumbing calls across the three modules.
    assert len(PLUMBING_MESSAGES) >= 8, f"found only {PLUMBING_MESSAGES}, so the parse no longer matches"


@pytest.mark.parametrize("message", PLUMBING_MESSAGES)
def test_each_plumbing_line_goes_to_the_debug_panel(message):
    """A plumbing line never reaches the Execution Log."""
    handler = _handler()
    handler.emit(_record(message))
    assert handler._run["log_messages"] == [], f"{message!r} reached the Execution Log"
    assert [entry["message"] for entry in handler._run["debug_messages"]] == [message]


@pytest.mark.parametrize(
    "message",
    [
        "! 0 current guest users exported to OrgCurrentGuests.csv",
        "Fetched 144 sites from the organization",
        "Starting export of site WLANs...",
        "! No zone session data found for this site",
    ],
)
def test_each_operator_line_stays_in_the_execution_log(message):
    """A line that tells the operator what the run did stays in the main log."""
    handler = _handler()
    handler.emit(_record(message, name="src.export.site_config_exporter"))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]
    assert handler._run["debug_messages"] == []


def test_a_plumbing_warning_still_reaches_the_operator():
    """A warning from the resolver is a real problem, so the operator must see it."""
    handler = _handler()
    message = "Resolving source dependency DataExporter failed, so the export cannot run"
    handler.emit(_record(message, level=logging.WARNING))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]
