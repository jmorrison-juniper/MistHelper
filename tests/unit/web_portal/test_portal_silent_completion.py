"""Tests for issue #3144 portal silent completion behavior."""

from __future__ import annotations  # WHY: keep annotations cheap and consistent with project style.

from pathlib import Path  # WHY: create unrelated output inside the scanner root.
from typing import NamedTuple  # WHY: carry the classifier answer in a typed record, not three loose booleans.
from unittest.mock import MagicMock, patch  # WHY: isolate the prompt, Mist call, and output root.

from src.foundation.support.utils.menu_entry import (
    MenuEntry,
)  # WHY: OperationExecutor expects menu entries, not raw callables.
from src.foundation.support.refactors import (
    device_data_fetcher as fetcher_module,
)  # WHY: patch the real fetcher's dependency resolver.
from src.foundation.support.refactors.device_data_fetcher import (
    DeviceDataFetcher,
)  # WHY: keep the real fetcher in the Menu 95 path.
from src.interfaces.visualization.ui import (
    interactive_display_utils as display_module,
)  # WHY: patch and execute the real Menu 95 display path.
from src.interfaces.visualization.ui.interactive_display_utils import (
    InteractiveDisplayUtils,
)  # WHY: Menu 95 uses this real handler.
from web_portal.services import operation as operation_module  # WHY: replace only the scanner root in the executor.
from web_portal.services.operation import PARAMETER_REGISTRY, OperationExecutor  # WHY: test the portal run contract.
from web_portal.services.output_scan import OutputFileScanner  # WHY: retain the real output scanner behavior.

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
MISSING_ORG_LINE = "No org_id available. Exiting."  # WHY: the tracked issue #3168 message that reported Complete.
EXPECTED_COMPLETION_GUARD_SCOPE = 8  # WHY: measured count of the issue #3144 completion rows on 2026-10-06.
EXPECTED_PARAMETER_GUARD_SCOPE = 7  # WHY: measured count of the issue #3320 control rows on 2026-10-06.


class _Classification(NamedTuple):
    """Hold the three portal classifier answers for one log message."""

    missing_input: bool  # WHY: a required answer never arrived, so the operation did not run.
    handled_error: bool  # WHY: the handler caught an error and returned without a result.
    no_output: bool  # WHY: the handler ran and honestly produced an empty result.


def _classify(executor: OperationExecutor, message: str) -> _Classification:
    """Return the typed classifier answer for one handler log message."""
    run = executor._build_run_record("210")  # WHY: menu 210 calls the resolver that logs the tracked message.
    run["log_messages"].append({"message": message, "level": "error"})  # WHY: emulate the exact handler log line.
    return _Classification(  # WHY: one typed record keeps the three answers readable in the assertion output.
        missing_input=executor._missing_input_reason(run) is not None,  # WHY: read the production missing-input scan.
        handled_error=executor._handled_error_reason(run) is not None,  # WHY: read the production handled-error scan.
        no_output=executor._no_output_reason(run) is not None,  # WHY: read the production empty-result scan.
    )


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


def _build_menu_95_executor() -> OperationExecutor:
    """Build an executor that runs the real Menu 95 display handler."""
    menu_actions = {  # WHY: one menu keeps the regression isolated from the full registry.
        "95": MenuEntry(  # WHY: match the production menu row shape.
            menu_id="95",  # WHY: retain the affected menu number in the run.
            handler=InteractiveDisplayUtils.device_tests,  # WHY: execute the real display and fetcher path.
            title="View Gateway Synthetic Test Statistics",  # WHY: give the run a readable production title.
            category="interactive_safe",  # WHY: match the registered operation category.
            destructive=False,  # WHY: the operation reads synthetic test results.
            supports_fast=False,  # WHY: this single-device path has no fast-mode contract.
        )
    }
    return OperationExecutor(menu_actions, None, None, _EventBus())  # WHY: capture terminal events without a server.


def test_issue_3144_controls_cover_site_and_identifier_prompts() -> None:
    """Every site or identifier scoped silent-completion row must offer controls."""
    print(f"The issue #3144 parameter guard checked {len(REQUIRED_CONTROL_NAMES)} operations.")  # WHY: guard proof.
    assert len(REQUIRED_CONTROL_NAMES) == EXPECTED_PARAMETER_GUARD_SCOPE, (  # WHY: a zero scope is a silent no-op.
        f"The parameter guard scope is {len(REQUIRED_CONTROL_NAMES)} rows, "
        f"but the measured scope is {EXPECTED_PARAMETER_GUARD_SCOPE} rows. "
        "An empty or changed scope makes this guard pass without a check."
    )
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
        assert len(ISSUE_3144_MENUS) == EXPECTED_COMPLETION_GUARD_SCOPE, (  # WHY: a zero scope is a silent no-op.
            f"The completion guard scope is {len(ISSUE_3144_MENUS)} menus, "
            f"but the measured scope is {EXPECTED_COMPLETION_GUARD_SCOPE} menus. "
            "An empty or changed scope makes this guard pass without a check."
        )
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


def test_issue_4030_unresolved_site_reports_failed_with_unrelated_output(tmp_path: Path) -> None:
    """Menu 95 must fail when site resolution stops before the Mist request."""
    unrelated_name = "unrelated.csv"  # WHY: prove another file cannot convert failure into completion.
    resolver = MagicMock()  # WHY: isolate the real fetcher from live application state.
    resolver.DeviceDataFetcher = DeviceDataFetcher  # WHY: retain the production fetcher contract.
    resolver.apisession = MagicMock(name="apisession")  # WHY: block any accidental live authentication.
    resolver.PromptUtils.select_site_id_from_csv.side_effect = lambda: _write_unrelated_output(tmp_path, unrelated_name)
    executor = _build_menu_95_executor()  # WHY: use the production completion classifier.
    run = executor._build_run_record("95")  # WHY: use the production run-record shape.
    scanner_factory = lambda: OutputFileScanner(str(tmp_path))  # WHY: scan only the temporary evidence directory.
    try:
        with patch.object(display_module, "SourceDependencyResolver", resolver):  # WHY: route the real display path.
            with patch.object(fetcher_module, "_MH", resolver):  # WHY: route the real fetcher path.
                with patch.object(DeviceDataFetcher, "_fetch_data") as fetch_data:  # WHY: observe an owned seam.
                    with patch.object(operation_module, "OutputFileScanner", scanner_factory):  # WHY: real scanner.
                        executor._execute_operation(run, {})  # WHY: drive capture, scanning, and verdict together.
        assert run["status"] == "failed", "An unresolved Menu 95 site reported Complete."  # WHY: issue #4030.
        assert run["error_message"] == "! Error fetching device data: site ID could not be resolved."  # WHY: exact.
        assert unrelated_name in run["output_files"]  # WHY: retain concurrent evidence without trusting it.
        assert "Completed device_tests execution." not in _run_messages(run)  # WHY: no false wrapper success.
        fetch_data.assert_not_called()  # WHY: a missing site must stop before the Mist request.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.


def _write_unrelated_output(root: Path, name: str) -> str:
    """Write unrelated output and return an unresolved site identifier."""
    (root / name).write_text("unrelated\n", encoding="utf-8")  # WHY: emulate concurrent output during selection.
    return ""  # WHY: the real prompt seam reports that no site was resolved.


def _run_messages(run: dict) -> list[str]:
    """Return captured operator messages from one portal run."""
    return [str(entry.get("message", "")) for entry in run["log_messages"]]  # WHY: inspect the captured text.


def test_missing_org_identifier_classifies_as_missing_input() -> None:
    """Issue #3168: a missing organization identifier is a missing input, not an empty result."""
    executor = _build_executor()  # WHY: drive the production classifier helpers directly.
    try:
        result = _classify(executor, MISSING_ORG_LINE)  # WHY: read the typed answer for the tracked message.
        assert result.missing_input is True, f"{MISSING_ORG_LINE!r} classified as {result!r}."  # WHY: the live gap.
        assert result.no_output is False, f"{MISSING_ORG_LINE!r} classified as {result!r}."  # WHY: no false Complete.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.


def test_missing_org_identifier_run_reports_failed() -> None:
    """Issue #3168: a missing organization identifier must fail the run, not complete it."""
    executor = _build_executor()  # WHY: drive the production completion path, not only the classifier.
    try:
        run = executor._build_run_record("210")  # WHY: menu 210 calls the resolver that logs this message.
        run["log_messages"].append({"message": MISSING_ORG_LINE, "level": "error"})  # WHY: emulate the handler log.
        executor._finish_successful_operation(run)  # WHY: this is the path used after a handler returns.
        assert run["status"] == "failed", "A missing organization identifier reported as Complete."  # WHY: unsafe.
        assert "required input was missing" in str(run["error_message"])  # WHY: the operator needs the cause.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.


def test_empty_result_line_still_classifies_as_no_output() -> None:
    """Issue #3168: the repair must not turn an honest empty result into a missing input."""
    executor = _build_executor()  # WHY: prove the opposite direction of the classifier still holds.
    try:
        result = _classify(executor, NO_DATA_LINE)  # WHY: read the typed answer for an honest empty result.
        assert result.no_output is True, f"{NO_DATA_LINE!r} classified as {result!r}."  # WHY: keep the empty result.
        assert result.missing_input is False, f"{NO_DATA_LINE!r} classified as {result!r}."  # WHY: no wider marker.
    finally:
        executor.shutdown(0)  # WHY: release the executor thread pool created for the test.
