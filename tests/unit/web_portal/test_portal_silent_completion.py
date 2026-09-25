"""Tests for issue #3144 portal silent completion behavior."""

from __future__ import annotations  # WHY: keep annotations cheap and consistent with project style.

from src.utils.menu_entry import MenuEntry  # WHY: OperationExecutor expects menu entries, not raw callables.
from web_portal.services.operation import PARAMETER_REGISTRY, OperationExecutor  # WHY: test the portal run contract.

ISSUE_3144_MENUS = ("66", "75", "76", "209", "210", "213", "224", "233")  # WHY: exact issue scope.
REQUIRED_CONTROL_NAMES = {  # WHY: each site or identifier row must offer these browser controls (issue #3320).
    "66": ("site_id",),  # WHY: menu 66 prompts for a site only.
    "75": ("site_id", "client_mac"),  # WHY: menu 75 prompts for a site and a client MAC address.
    "76": ("site_id", "device_id"),  # WHY: menu 76 prompts for a site and a device.
    "209": ("site_id", "beacon_id"),  # WHY: menu 209 prompts for a site and a beacon.
    "210": ("site_id",),  # WHY: menu 210 prompts for a site only.
    "213": ("site_id",),  # WHY: menu 213 prompts for a site only.
    "224": ("site_id",),  # WHY: menu 224 prompts for a site only.
}
NO_DATA_LINE = "! No data found for this operation"  # WHY: the honest empty-result line that a handler logs.
NO_DATA_COMPLETION = f"Operation completed with no output file: {NO_DATA_LINE}"  # WHY: the exact operator message.


class _EventBus:
    """Collect published events without starting a browser or SSE stream."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []  # WHY: preserve event type and payload for assertions.

    def publish(self, event_type: str, data: dict) -> None:
        self.events.append((event_type, data))  # WHY: record the exact event the executor would stream.


def _build_executor() -> OperationExecutor:
    """Build an executor with only the issue #3144 menu records."""
    menu_actions = {  # WHY: the executor needs a handler and title for each run record.
        menu: MenuEntry(  # WHY: match the production menu row shape.
            menu_id=menu,  # WHY: keep the menu number available to the executor.
            handler=lambda: None,  # WHY: these tests call finish helpers directly.
            title=f"Operation {menu}",  # WHY: run records require a readable title.
            category="safe",  # WHY: the run helpers do not read this field.
            destructive=False,  # WHY: these issue rows are read-only.
            supports_fast=False,  # WHY: fast-mode metadata is irrelevant here.
        )
        for menu in ISSUE_3144_MENUS  # WHY: state the measured issue scope in one place.
    }
    return OperationExecutor(menu_actions, None, None, _EventBus())  # WHY: use a fake event bus for event assertions.


def test_issue_3144_controls_cover_site_and_identifier_prompts() -> None:
    """Every site or identifier scoped silent-completion row must offer controls."""
    print(f"The issue #3144 parameter guard checked {len(REQUIRED_CONTROL_NAMES)} operations.")  # WHY: guard proof.
    for menu, required_names in REQUIRED_CONTROL_NAMES.items():  # WHY: check each affected row, not only one example.
        entry = PARAMETER_REGISTRY.get(menu, {})  # WHY: a missing definition reads as empty, so it fails below.
        offered = {parameter.get("name") for parameter in entry.get("parameters", [])}  # WHY: one control per name.
        missing = [name for name in required_names if name not in offered]  # WHY: name each absent control.
        assert missing == [], f"Menu {menu} lacks the portal controls {missing}."  # WHY: no controls caused silence.


def test_completed_issue_3144_runs_explain_no_output() -> None:
    """A completed no-output run must carry a no-data message."""
    executor = _build_executor()  # WHY: build the production executor helpers under test.
    try:
        print(f"The issue #3144 completion guard checked {len(ISSUE_3144_MENUS)} operations.")  # WHY: guard proof.
        for menu in ISSUE_3144_MENUS:  # WHY: every issue row gets the same no-output contract.
            run = executor._build_run_record(menu)  # WHY: use the production run record shape.
            run["log_messages"].append(  # WHY: emulate a handler that returned an honest empty result.
                {"message": NO_DATA_LINE, "level": "info"}  # WHY: the same line that a real handler logs.
            )
            message = executor._completion_message(run)  # WHY: completed no-output runs need a visible reason.
            reported = f"Menu {menu} reported {message!r} instead of the no-data reason."  # WHY: name the wrong text.
            assert message == NO_DATA_COMPLETION, reported  # WHY: silence or a lost reason is the defect.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.


def test_missing_required_input_does_not_complete() -> None:
    """A missing required answer is a failed run, not a completed empty run."""
    executor = _build_executor()  # WHY: build the production executor helpers under test.
    try:
        run = executor._build_run_record("75")  # WHY: menu 75 was one observed missing-site example.
        run["log_messages"].append(  # WHY: emulate the exact handler log that used to become a false success.
            {"message": "No site selected. Exiting.", "level": "error"}
        )
        executor._finish_successful_operation(run)  # WHY: this is the path used after a handler returns.
        assert run["status"] == "failed", "Missing site input reported as Complete."  # WHY: false success is unsafe.
        assert "required input was missing" in str(run["error_message"])  # WHY: the operator needs the cause.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.


def test_handled_handler_error_does_not_complete() -> None:
    """A handler that logs an error and returns must fail the run."""
    executor = _build_executor()  # WHY: build the production executor helpers under test.
    try:
        run = executor._build_run_record("209")  # WHY: get-by-id prompts can receive invalid identifiers.
        run["log_messages"].append(  # WHY: emulate an exporter that caught an SDK error and returned.
            {"message": "! Error fetching site beacon detail: Not Found", "level": "info"}
        )
        executor._finish_successful_operation(run)  # WHY: this is the path used after a handler returns.
        assert run["status"] == "failed", "A handled API error reported as Complete."  # WHY: fail honestly.
        assert "Error fetching site beacon detail" in str(run["error_message"])  # WHY: preserve the real cause.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.
