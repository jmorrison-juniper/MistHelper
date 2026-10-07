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
import threading
from pathlib import Path

import pytest

from web_portal.services.operation import _RunLogHandler

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

# The modules whose INFO lines describe plumbing rather than the operation.
PLUMBING_MODULES = (
    "src/foundation/runtime/config/source_dependency_resolver.py",
    "src/foundation/runtime/config/config_utils.py",
    "src/foundation/support/refactors/main_entrypoint.py",
)

# The message stems that mark a plumbing line in those modules.
PLUMBING_STEMS = ("Resolving ", "Selecting the bootstrap", "Activating the bootstrap", "Setting the active application")


def _handler() -> _RunLogHandler:
    """Return a handler bound to an empty run record, with no event bus."""
    run = {"run_id": "test-run", "log_messages": [], "debug_messages": [], "output_files": []}
    return _RunLogHandler(run, None)


def _record(
    message: str, level: int = logging.INFO, name: str = "src.foundation.runtime.config.source_dependency_resolver"
):
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
    handler.emit(_record(message, name="src.operations.exporting.export.site_config_exporter"))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]
    assert handler._run["debug_messages"] == []


def test_a_plumbing_warning_still_reaches_the_operator():
    """A warning from the resolver is a real problem, so the operator must see it."""
    handler = _handler()
    message = "Resolving source dependency DataExporter failed, so the export cannot run"
    handler.emit(_record(message, level=logging.WARNING))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]


# Issue #3232: the site prompt logs its menu at WARNING, and a WARNING always
# reached the Execution Log. Every site-scoped run showed a heading and one row
# for each of the 143 sites, after the pick list had already answered.
SITE_MENU_MODULE = "src/interfaces/visualization/ui/prompt_utils.py"


def _site_menu_messages() -> list[str]:
    """Render the heading and one row of the site menu from their source calls."""
    tree = ast.parse((REPOSITORY_ROOT / SITE_MENU_MODULE).read_text(encoding="utf-8"))
    rendered: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "warning" and node.args):
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        if "Available Sites" in first.value:
            rendered.append(first.value)  # The heading takes no argument.
        elif first.value == "[%s] %s":
            rendered.append(first.value % (7, "AlamoSanAntonio"))  # Render one row as a run would.
    return rendered


SITE_MENU_MESSAGES = _site_menu_messages()


def test_the_site_menu_calls_still_exist():
    """The routing below means something only while the menu calls exist."""
    assert len(SITE_MENU_MESSAGES) == 2, f"found {SITE_MENU_MESSAGES}, so the menu calls moved or changed shape"


@pytest.mark.parametrize("message", SITE_MENU_MESSAGES)
def test_each_site_menu_line_goes_to_the_debug_panel(message):
    """The pick list already answered the site menu, so the operator never needs it."""
    handler = _handler()
    handler.emit(_record(message, level=logging.WARNING, name="src.interfaces.visualization.ui.prompt_utils"))
    assert handler._run["log_messages"] == [], f"{message!r} reached the Execution Log"
    assert [entry["message"] for entry in handler._run["debug_messages"]] == [message]


def test_a_site_not_found_line_stays_in_the_execution_log():
    """This line tells the operator why the run stopped, so it must stay visible."""
    handler = _handler()
    message = "Site not found by name or index: AlamoSanAntonio"
    handler.emit(_record(message, level=logging.WARNING, name="src.interfaces.visualization.ui.prompt_utils"))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]


def test_a_numbered_line_from_another_module_stays_in_the_execution_log():
    """The routing matches one logger only, so real numbered output stays visible."""
    handler = _handler()
    message = "[1] Found 3 gateways with an HA cluster"
    handler.emit(_record(message, level=logging.WARNING, name="src.operations.exporting.export.gateway_ha_exporter"))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]


def test_a_database_info_line_goes_to_the_debug_panel():
    """A site cache refresh writes one JSON line for each collection, which is plumbing."""
    handler = _handler()
    message = '{"collection": "sitegroups", "written": 5, "failed": 0, "event": "import_complete"}'
    handler.emit(_record(message, name="src.foundation.persistence.db.writers.arango_writer"))
    assert handler._run["log_messages"] == [], "a database INFO line reached the Execution Log"
    assert [entry["message"] for entry in handler._run["debug_messages"]] == [message]


def test_a_database_warning_still_reaches_the_operator():
    """A failed write is a real problem, so the prefix rule applies below WARNING only."""
    handler = _handler()
    message = "Polyglot write failed for listOrgSites: the store refused 144 rows"
    handler.emit(_record(message, level=logging.WARNING, name="src.foundation.persistence.db.writers.arango_writer"))
    assert [entry["message"] for entry in handler._run["log_messages"]] == [message]


def test_the_store_summary_line_goes_to_the_debug_panel():
    """The polyglot summary describes the cache refresh, not the operation."""
    handler = _handler()
    message = "Polyglot write: backend=arangodb, written=144, failed=0"
    handler.emit(_record(message, name="src.operations.exporting.export.data_exporter"))
    assert handler._run["log_messages"] == [], "the store summary reached the Execution Log"
    assert [entry["message"] for entry in handler._run["debug_messages"]] == [message]


@pytest.mark.parametrize("logger_name", ["redis_writer", "redis_json_writer"])
def test_a_redis_writer_info_line_goes_to_the_debug_panel(logger_name):
    """The Redis writers bind bare logger names, and their connect lines are plumbing."""
    handler = _handler()
    message = '{"host": "misthelper-redis", "event": "redis_connected"}'
    handler.emit(_record(message, name=logger_name))
    assert handler._run["log_messages"] == [], f"a {logger_name} INFO line reached the Execution Log"
    assert [entry["message"] for entry in handler._run["debug_messages"]] == [message]


def test_the_store_start_line_goes_to_the_debug_panel():
    """The router start line belongs to the cache refresh, not to the operation."""
    handler = _handler()
    handler.emit(_record("Polyglot DatabaseRouter initialized", name="src.operations.exporting.export.data_exporter"))
    assert handler._run["log_messages"] == [], "the store start line reached the Execution Log"


def test_handler_rejects_a_foreign_worker_record_before_any_run_mutation():
    """A root handler must ignore a record from another operation worker."""
    run = {  # Build every evidence store that a foreign record could mutate.
        "run_id": "owner-run",  # Keep the run identifier stable for an event assertion.
        "log_messages": [],  # Detect a foreign user-facing record.
        "debug_messages": [],  # Detect a foreign debug record.
        "output_files": [],  # Detect a filename scraped from foreign log prose.
        "dropped_log_count": 0,  # Detect a foreign bounded-store discard.
    }
    handler = _RunLogHandler(run, None)  # Bind direct capture to the current worker thread.
    record = _record("Wrote 5 rows to data/Foreign.csv")  # Build a record that would change two evidence stores.
    record.thread = threading.get_ident() + 1  # Give the record a different worker owner.
    handler.emit(record)  # Exercise the earliest ownership gate.
    assert run["log_messages"] == []  # Reject the foreign user-facing line.
    assert run["debug_messages"] == []  # Reject any foreign debug routing.
    assert run["output_files"] == []  # Reject foreign filename extraction.
    assert run["dropped_log_count"] == 0  # Reject foreign discard accounting.
