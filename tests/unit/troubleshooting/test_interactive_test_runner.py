"""Unit tests for src.troubleshooting.interactive_test_runner.

Wave 13 P2 coverage lift — extended coverage for the selector path,
fallback path, skip emission, org_id resolution, site-resolution
failure branches, and option-loop failure telemetry.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest  # WHY: pytest monkeypatch fixture for os.environ selector control

from src.dataclasses.progress_event import TestSummary  # WHY: assert summary payload without ceremony
from src.troubleshooting.interactive_test_runner import (
    InteractiveTestRunner,
    SuiteContext,
    SuiteTallies,
)


class _TelemetryStub:
    """Minimal telemetry stub for deterministic runner tests."""

    def __init__(self, _path: str) -> None:
        self.events: list[tuple[str, tuple]] = []  # WHY: capture ordered events for behavioural assertions
        self.closed = False  # WHY: assert close() was called on happy + failure paths
        self.retention_enforced = False  # WHY: assert retention was applied on happy paths

    @staticmethod
    def timestamped_path(_directory: str) -> str:
        return "data/test_events_stub.jsonl"

    def emit_test_skip(self, *args) -> None:
        self.events.append(("skip", args))

    def emit_test_start(self, *args) -> None:
        self.events.append(("start", args))

    def emit_test_pass(self, *args) -> None:
        self.events.append(("pass", args))

    def emit_test_fail(self, *args) -> None:
        self.events.append(("fail", args))

    def emit_test_summary(self, *args) -> None:
        self.events.append(("summary", args))

    def close(self) -> None:
        self.closed = True

    def enforce_retention(self) -> None:
        self.retention_enforced = True


class _OperationRegistryStub:
    """Operation registry stub exposing one interactive-safe option."""

    @staticmethod
    def interactive_safe_options(_all_options):
        return ["1"]

    @staticmethod
    def is_interactive_safe(option):
        return option == "1"

    @staticmethod
    def skip_reason(_option):
        return "skip"

    @staticmethod
    def skip_category(_option):
        return "interactive"


class _RegistryWithSkip:
    """Registry that classifies option '2' as non-interactive-safe to exercise skip branches."""

    @staticmethod
    def interactive_safe_options(_all_options):
        return ["1"]  # WHY: only option 1 is safe -> option 2 goes to the skip branches

    @staticmethod
    def is_interactive_safe(option):
        return option == "1"

    @staticmethod
    def skip_reason(_option):
        return "not-safe-in-tests"  # WHY: distinctive reason for assertion

    @staticmethod
    def skip_category(_option):
        return "interactive"


def _make_runner(
    *,
    menu_actions: dict | None = None,
    registry=_OperationRegistryStub,
    mistapi_module: MagicMock | None = None,
    org_id_getter=lambda: "org-1",
    org_id_setter=lambda _value: None,
    config_utils: MagicMock | None = None,
) -> InteractiveTestRunner:
    """Build a runner with sensible defaults so per-test setup stays terse."""
    if menu_actions is None:  # WHY: default menu wires one no-op interactive option
        menu_actions = {"1": (lambda site_id=None: None, "Option One")}
    if mistapi_module is None:  # WHY: default mistapi returns a single site
        mistapi_module = MagicMock()
        site_response = MagicMock()
        site_response.data = [{"id": "site-1", "name": "Site One"}]
        mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    return InteractiveTestRunner(
        menu_actions=menu_actions,
        operation_registry=registry,
        telemetry_emitter_cls=_TelemetryStub,
        config_utils=config_utils or MagicMock(),
        mistapi_module=mistapi_module,
        apisession=MagicMock(),
        org_id_getter=org_id_getter,
        org_id_setter=org_id_setter,
    )


def test_execute_runs_interactive_option_successfully() -> None:
    """Runner should execute interactive-safe callable and return True on success."""
    called = {"value": False}

    def _option(site_id=None):
        called["value"] = site_id == "site-1"

    menu_actions = {"1": (_option, "Option One")}
    runner = _make_runner(menu_actions=menu_actions)

    result = runner.execute()

    assert result is True
    assert called["value"] is True


def test_find_selector_match_by_id() -> None:
    """_find_selector_match locates a site by exact UUID."""
    sites = [{"id": "site-a", "name": "Alpha"}, {"id": "site-b", "name": "Beta"}]
    match = InteractiveTestRunner._find_selector_match(sites, "site-b")
    assert match == {"id": "site-b", "name": "Beta"}


def test_find_selector_match_case_insensitive_name() -> None:
    """_find_selector_match matches sites by lowercased name."""
    sites = [{"id": "site-a", "name": "Alpha"}]
    match = InteractiveTestRunner._find_selector_match(sites, "ALPHA")
    assert match == {"id": "site-a", "name": "Alpha"}


def test_find_selector_match_returns_none_when_missing() -> None:
    """_find_selector_match returns None for an unknown selector."""
    sites = [{"id": "site-a", "name": "Alpha"}]
    assert InteractiveTestRunner._find_selector_match(sites, "gamma") is None


def test_log_selector_miss_prints_and_logs(capsys, caplog) -> None:
    """_log_selector_miss emits the legacy warning banner and a warning log."""
    with caplog.at_level("WARNING"):
        InteractiveTestRunner._log_selector_miss("selector-xyz")
    captured = capsys.readouterr()
    assert "selector-xyz" in captured.out  # WHY: legacy operator-facing banner
    assert any("not found" in rec.message for rec in caplog.records)  # WHY: warning log preserved


def test_lookup_selector_site_returns_match(capsys) -> None:
    """_lookup_selector_site returns the matched site tuple and prints the legacy success line."""
    mistapi_module = MagicMock()
    site_response = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._lookup_selector_site("org-1", "site-a")
    assert (site_id, site_name) == ("site-a", "Alpha")
    assert "Alpha" in capsys.readouterr().out  # WHY: legacy success message printed


def test_lookup_selector_site_miss_returns_none() -> None:
    """_lookup_selector_site returns (None, 'Unknown') and logs a miss on selector failure."""
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._lookup_selector_site("org-1", "nope")
    assert site_id is None
    assert site_name == "Unknown"


def test_lookup_first_available_site_returns_none_when_empty(capsys) -> None:
    """_lookup_first_available_site returns (None, 'Unknown') when the org has no sites."""
    mistapi_module = MagicMock()
    site_response = MagicMock()
    site_response.data = []  # WHY: exercise the empty-data branch
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._lookup_first_available_site("org-1")
    assert site_id is None
    assert site_name == "Unknown"


def test_resolve_test_site_uses_environment_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    """_resolve_test_site delegates to the selector helper when MIST_INTERACTIVE_TEST_SITE is set."""
    monkeypatch.setenv("MIST_INTERACTIVE_TEST_SITE", "site-a")
    mistapi_module = MagicMock()
    site_response = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._resolve_test_site("org-1")
    assert (site_id, site_name) == ("site-a", "Alpha")


def test_ensure_org_id_resolves_when_cache_empty() -> None:
    """_ensure_org_id resolves via config_utils and calls the setter when cache is empty."""
    stored = {"org_id": None}

    def _setter(value):
        stored["org_id"] = value

    config_utils = MagicMock()
    config_utils.get_cached_or_prompted_org_id.return_value = "resolved-org"
    runner = _make_runner(
        org_id_getter=lambda: None,  # WHY: force the resolve branch
        org_id_setter=_setter,
        config_utils=config_utils,
    )
    result = runner._ensure_org_id()
    assert result == "resolved-org"  # WHY: helper returned the resolved id
    assert stored["org_id"] == "resolved-org"  # WHY: setter persisted the id


def test_resolve_site_or_close_returns_none_when_no_sites(capsys) -> None:
    """_resolve_site_or_close closes the emitter and prints the no-site banner when nothing is found."""
    mistapi_module = MagicMock()
    site_response = MagicMock()
    site_response.data = []  # WHY: no sites -> abort path
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    runner = _make_runner(mistapi_module=mistapi_module)
    emitter = _TelemetryStub("data/x.jsonl")
    site_id, site_name = runner._resolve_site_or_close("org-1", emitter)
    assert site_id is None
    assert site_name == ""
    assert emitter.closed is True  # WHY: emitter flushed on failure
    assert "No sites found" in capsys.readouterr().out  # WHY: legacy error banner


def test_resolve_site_or_close_handles_exception(capsys) -> None:
    """_resolve_site_or_close catches exceptions from _resolve_test_site and closes the emitter."""
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.side_effect = RuntimeError("api boom")
    runner = _make_runner(mistapi_module=mistapi_module)
    emitter = _TelemetryStub("data/x.jsonl")
    site_id, site_name = runner._resolve_site_or_close("org-1", emitter)
    assert site_id is None
    assert site_name == ""
    assert emitter.closed is True  # WHY: emitter flushed on failure
    assert "Failed to fetch test site" in capsys.readouterr().out  # WHY: legacy failure banner


def test_emit_skip_events_records_skip_per_option(capsys) -> None:
    """_emit_skip_events emits telemetry for each option present in menu_actions."""

    def _noop_with_site(site_id: str | None = None) -> None:  # WHY: named callable so mypy can type-check
        return None

    def _noop() -> None:  # WHY: named callable so mypy can type-check
        return None

    menu_actions = {
        "1": (_noop_with_site, "Option One"),
        "2": (_noop, "Option Two"),
    }
    runner = _make_runner(menu_actions=menu_actions, registry=_RegistryWithSkip)
    emitter = _TelemetryStub("data/x.jsonl")
    count = runner._emit_skip_events(emitter, ["2", "unknown-option"])
    assert count == 1  # WHY: only option "2" is in menu_actions; "unknown-option" is filtered
    assert emitter.events[0][0] == "skip"  # WHY: skip event emitted first


def test_print_skipped_options_writes_reason_lines(capsys) -> None:
    """_print_skipped_options renders one reason line per skipped option present in menu_actions."""

    def _noop_with_site(site_id: str | None = None) -> None:  # WHY: named callable so mypy can type-check
        return None

    def _noop() -> None:  # WHY: named callable so mypy can type-check
        return None

    menu_actions = {
        "1": (_noop_with_site, "Option One"),
        "2": (_noop, "Option Two"),
    }
    runner = _make_runner(menu_actions=menu_actions, registry=_RegistryWithSkip)
    runner._print_skipped_options(["2"])
    output = capsys.readouterr().out
    assert "not-safe-in-tests" in output  # WHY: skip reason surfaces in output
    assert "2" in output  # WHY: option id present


def test_print_summary_verdict_returns_false_when_failures(capsys, caplog) -> None:
    """_print_summary_verdict returns False and logs a warning when there are failures."""
    runner = _make_runner()
    tallies = SuiteTallies(success_count=1, error_count=2, skip_count=0, total_time=1.5)
    with caplog.at_level("WARNING"):
        result = runner._print_summary_verdict(tallies, interactive_total=3)
    assert result is False
    assert "2 operations failed" in capsys.readouterr().out  # WHY: legacy failure banner
    assert any("2 operations failed" in rec.message for rec in caplog.records)  # WHY: warning log


def test_run_option_loop_records_failure_via_telemetry() -> None:
    """_run_option_loop emits a fail event when the option callable raises."""

    def _boom(site_id=None):
        raise RuntimeError("kaboom")

    menu_actions = {"1": (_boom, "Fails")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")
    success, failure = runner._run_option_loop(["1"], "site-1", emitter)
    assert success == 0  # WHY: no successes because option raised
    assert failure == 1  # WHY: exactly one failure recorded
    event_types = [event[0] for event in emitter.events]  # WHY: verify start+fail sequence
    assert "start" in event_types
    assert "fail" in event_types


def test_run_option_loop_skips_options_missing_from_menu() -> None:
    """_run_option_loop silently skips option ids not present in menu_actions."""
    menu_actions = {"1": (lambda site_id=None: None, "One")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")
    # WHY: pass an option not in menu_actions to exercise the `continue` branch
    success, failure = runner._run_option_loop(["1", "does-not-exist"], "site-1", emitter)
    assert success == 1  # WHY: only the valid option ran
    assert failure == 0  # WHY: no failures produced


def test_finalize_telemetry_emits_summary_and_closes() -> None:
    """_finalize_telemetry emits a TestSummary event and closes the emitter with retention."""
    runner = _make_runner()
    emitter = _TelemetryStub("data/x.jsonl")
    tallies = SuiteTallies(success_count=3, error_count=1, skip_count=2, total_time=4.0)
    runner._finalize_telemetry(emitter, tallies, total_ops=10)
    summary_events = [event for event in emitter.events if event[0] == "summary"]
    assert len(summary_events) == 1  # WHY: summary emitted exactly once
    payload = summary_events[0][1][0]  # WHY: first positional arg is the TestSummary dataclass
    assert isinstance(payload, TestSummary)  # WHY: contract: summary event uses TestSummary aggregator
    assert emitter.closed is True  # WHY: emitter closed after summary
    assert emitter.retention_enforced is True  # WHY: retention policy applied on happy path


def test_run_and_finalize_returns_false_when_option_fails() -> None:
    """_run_and_finalize returns False when the executed option fails."""

    def _boom(site_id=None):
        raise RuntimeError("boom")

    menu_actions = {"1": (_boom, "Fails")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")
    ctx = SuiteContext(
        all_options=["1"],
        interactive_options=["1"],
        test_site_id="site-1",
        emitter=emitter,
        telemetry_path="data/x.jsonl",
        skip_count=0,
        start_time=0.0,
    )
    assert runner._run_and_finalize(ctx) is False  # WHY: failure path returns False


def test_execute_returns_false_when_no_sites(monkeypatch: pytest.MonkeyPatch) -> None:
    """execute() returns False when site resolution fails (no sites in the org)."""
    monkeypatch.delenv("MIST_INTERACTIVE_TEST_SITE", raising=False)
    mistapi_module = MagicMock()
    site_response = MagicMock()
    site_response.data = []  # WHY: force the resolve-failure abort
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    runner = _make_runner(mistapi_module=mistapi_module)
    assert runner.execute() is False  # WHY: no test site -> False verdict
