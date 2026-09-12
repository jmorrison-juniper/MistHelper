"""Unit tests for src.troubleshooting.interactive_test_runner.

Wave 13 P2 coverage lift — extended coverage for the selector path,
fallback path, skip emission, org_id resolution, site-resolution
failure branches, and option-loop failure telemetry.
"""

from __future__ import annotations

import logging  # WHY: #886 slice 18/N — caplog level control for logger-based output
from unittest.mock import MagicMock

import pytest  # WHY: pytest monkeypatch fixture for os.environ selector control

from src.dataclasses.progress_event import TestSummary  # WHY: assert summary payload without ceremony
from src.troubleshooting.interactive_test_runner import (
    InteractiveTestRunner,
    SuiteContext,
    SuiteTallies,
    TestSiteSelectorUnresolved,  # WHY: #1637 fail-closed selector contract exception.
)


@pytest.fixture(autouse=True)
def _capture_warnings(caplog: pytest.LogCaptureFixture) -> None:
    """Capture WARNING+ logger output for every test in this module.

    Why:
        #886 slice 18/N migrated operator-facing ``print()`` calls in
        ``interactive_test_runner.py`` to ``logging.warning`` /
        ``logging.error``. Setting the caplog level at WARNING makes all
        migrated banners visible via ``caplog.text`` without per-test
        boilerplate, keeping the assertion shape identical to the legacy
        ``capsys`` pattern.
    """
    caplog.set_level(logging.WARNING)


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


def test_log_selector_miss_prints_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    """_log_selector_miss emits the fail-closed selector-miss error record (issue #1637)."""
    with caplog.at_level("ERROR"):
        InteractiveTestRunner._log_selector_miss("selector-xyz")
    assert "selector-xyz" in caplog.text  # WHY: operator-facing selector id preserved in the record
    assert any(
        "did not match" in rec.message and rec.levelno == logging.ERROR for rec in caplog.records
    )  # WHY: fail-closed wording + ERROR level (issue #1637)


def test_lookup_selector_site_returns_match(caplog: pytest.LogCaptureFixture) -> None:
    """_lookup_selector_site returns the matched site tuple and logs the legacy success line."""
    mistapi_module = MagicMock()
    site_response = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._lookup_selector_site("org-1", "site-a")
    assert (site_id, site_name) == ("site-a", "Alpha")
    assert "Alpha" in caplog.text  # WHY: legacy success message routed through the logger


def test_lookup_selector_site_raises_on_miss(caplog: pytest.LogCaptureFixture) -> None:
    """_lookup_selector_site raises TestSiteSelectorUnresolved and logs the miss on selector failure.

    Why:
        Issue #1637 — an unresolved MIST_INTERACTIVE_TEST_SITE selector must
        fail closed rather than silently falling back to the first available
        site. The lookup helper is the seam where the operator's explicit
        intent is verified, so the miss must raise a domain-specific
        exception that ``_resolve_site_or_close`` catches to abort the suite.
    """
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(TestSiteSelectorUnresolved) as exc_info:
            runner._lookup_selector_site("org-1", "nope")
    assert "nope" in str(exc_info.value)  # WHY: message must surface the unresolved selector value.


def test_lookup_first_available_site_returns_none_when_empty() -> None:
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


def test_resolve_site_or_close_returns_none_when_no_sites(caplog: pytest.LogCaptureFixture) -> None:
    """_resolve_site_or_close closes the emitter and logs the no-site banner when nothing is found."""
    mistapi_module = MagicMock()
    site_response = MagicMock()
    site_response.data = []  # WHY: no sites -> abort path
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response
    runner = _make_runner(mistapi_module=mistapi_module)
    emitter = _TelemetryStub("data/x.jsonl")
    with caplog.at_level("ERROR"):  # WHY: no-site path now uses logging.error
        site_id, site_name = runner._resolve_site_or_close("org-1", emitter)
    assert site_id is None
    assert site_name == ""
    assert emitter.closed is True  # WHY: emitter flushed on failure
    assert "No sites found" in caplog.text  # WHY: legacy error banner now routed through the logger


def test_resolve_site_or_close_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """_resolve_site_or_close catches exceptions from _resolve_test_site and closes the emitter."""
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.side_effect = RuntimeError("api boom")
    runner = _make_runner(mistapi_module=mistapi_module)
    emitter = _TelemetryStub("data/x.jsonl")
    with caplog.at_level("ERROR"):  # WHY: failure path now uses logging.error
        site_id, site_name = runner._resolve_site_or_close("org-1", emitter)
    assert site_id is None
    assert site_name == ""
    assert emitter.closed is True  # WHY: emitter flushed on failure
    assert "Failed to fetch test site" in caplog.text  # WHY: legacy failure banner now via logger


def test_emit_skip_events_records_skip_per_option() -> None:
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


def test_print_skipped_options_writes_reason_lines(caplog: pytest.LogCaptureFixture) -> None:
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
    assert "not-safe-in-tests" in caplog.text  # WHY: skip reason surfaces in the log record
    assert "2" in caplog.text  # WHY: option id present in the log record


def test_print_summary_verdict_returns_false_when_failures(caplog: pytest.LogCaptureFixture) -> None:
    """_print_summary_verdict returns False and logs a warning when there are failures."""
    runner = _make_runner()
    tallies = SuiteTallies(success_count=1, error_count=2, skip_count=0, total_time=1.5)
    with caplog.at_level("WARNING"):
        result = runner._print_summary_verdict(tallies, interactive_total=3)
    assert result is False
    assert "2 operations failed" in caplog.text  # WHY: legacy failure banner routed through the logger


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


def test_run_option_loop_flags_logged_error_as_failure(caplog: pytest.LogCaptureFixture) -> None:
    """Handler that logs ERROR then returns None must be classified as failure, not pass.

    Why:
        Issue #1636 — the current runner treats any non-exception return as a
        pass. A handler that emits ``logging.error(...)`` and swallows the
        error silently reports success, inflating the pass rate. The runner
        must observe ERROR records emitted during the option and treat them
        as a logged-error outcome (failure), not a clean pass.
    """

    def _logs_error(site_id: str | None = None) -> None:
        logging.error("simulated operation failure")
        return None

    menu_actions = {"1": (_logs_error, "Logs Error")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")
    with caplog.at_level(logging.ERROR):
        success, failure = runner._run_option_loop(["1"], "site-1", emitter)
    assert success == 0  # WHY: option logged ERROR -> not a clean pass
    assert failure == 1  # WHY: logged_error counts against the run
    event_types = [event[0] for event in emitter.events]
    assert "fail" in event_types  # WHY: emitter records the failure, not a pass
    assert "pass" not in event_types  # WHY: logged-error path must not emit pass


def test_print_summary_verdict_false_on_logged_error(caplog: pytest.LogCaptureFixture) -> None:
    """_print_summary_verdict must return False when any operation logged an ERROR.

    Why:
        Issue #1636 exit-code path — a run containing logged-error outcomes
        must produce a non-zero exit even if no exception was raised. The
        verdict helper is the single seam that decides the process exit code
        for ``--testinteractive``.
    """
    runner = _make_runner()
    # WHY: error_count is the aggregate of logged_error + raised_exception; a
    # run with one logged-error operation and no exceptions still fails.
    tallies = SuiteTallies(success_count=0, error_count=1, skip_count=0, total_time=0.5)
    with caplog.at_level(logging.WARNING):
        result = runner._print_summary_verdict(tallies, interactive_total=1)
    assert result is False  # WHY: any logged_error must fail the suite


def test_resolve_test_site_propagates_unresolved_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    """_resolve_test_site must raise TestSiteSelectorUnresolved rather than falling back on selector miss.

    Why:
        Issue #1637 — the silent-fallback bug lives in ``_resolve_test_site``;
        it currently reruns ``_lookup_first_available_site`` whenever the
        selector lookup returns ``(None, "Unknown")``. Under fail-closed
        semantics an unresolved explicit selector must propagate out of the
        resolver so ``_resolve_site_or_close`` can abort the suite instead
        of exercising a different site than the operator requested.
    """
    monkeypatch.setenv("MIST_INTERACTIVE_TEST_SITE", "does-not-exist")
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    with pytest.raises(TestSiteSelectorUnresolved):
        runner._resolve_test_site("org-1")


def test_resolve_test_site_exact_uuid_match_no_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exact UUID selector match must resolve without consulting the fallback helper.

    Why:
        Issue #1637 — deterministic exact-match behaviour is the acceptance
        criterion for a resolved selector. Only the selector fetch path
        (``listOrgSites`` + ``get_all``) should run; the fallback branch
        (``listOrgSites(..., limit=1)``) must not be invoked when the
        operator's selector already matched.
    """
    monkeypatch.setenv("MIST_INTERACTIVE_TEST_SITE", "site-a")
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._resolve_test_site("org-1")
    assert (site_id, site_name) == ("site-a", "Alpha")
    # WHY: exactly one selector fetch; fallback (limit=1) must not fire.
    assert mistapi_module.api.v1.orgs.sites.listOrgSites.call_count == 1


def test_resolve_test_site_exact_name_case_insensitive_match(monkeypatch: pytest.MonkeyPatch) -> None:
    """Case-insensitive exact-name selector must resolve deterministically.

    Why:
        Issue #1637 — operators commonly reference sites by human name
        (e.g. ``Morrison House Site``). The selector match is documented as
        case-insensitive; this test locks that contract alongside the
        fail-closed behaviour so a future refactor cannot silently narrow it.
    """
    monkeypatch.setenv("MIST_INTERACTIVE_TEST_SITE", "ALPHA")
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    site_id, site_name = runner._resolve_test_site("org-1")
    assert (site_id, site_name) == ("site-a", "Alpha")


def test_resolve_site_or_close_fail_closed_on_unresolved_selector(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """_resolve_site_or_close aborts, closes the emitter, and logs a fail-closed banner.

    Why:
        Issue #1637 — the single seam that maps selector-resolution errors
        onto the suite abort path. Behaviour must be identical to the
        pre-existing no-site path (emitter closed, ``(None, "")`` returned)
        but the operator-facing record must clearly attribute the abort to
        the unresolved selector, not to a generic fetch failure.
    """
    monkeypatch.setenv("MIST_INTERACTIVE_TEST_SITE", "does-not-exist")
    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = _make_runner(mistapi_module=mistapi_module)
    emitter = _TelemetryStub("data/x.jsonl")
    with caplog.at_level(logging.ERROR):
        site_id, site_name = runner._resolve_site_or_close("org-1", emitter)
    assert site_id is None
    assert site_name == ""
    assert emitter.closed is True  # WHY: emitter flushed on fail-closed abort.
    assert "does-not-exist" in caplog.text  # WHY: unresolved selector value surfaced to the operator.


def test_execute_returns_false_on_unresolved_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    """execute() returns False and emits no test_start when the selector cannot be resolved.

    Why:
        Issue #1637 end-to-end — the top-level contract is that a run with
        an unresolved explicit selector must abort before any interactive
        option runs. Asserting the absence of any ``start``/``pass``/``fail``
        event proves no option was actually exercised against a wrong site.
    """
    monkeypatch.setenv("MIST_INTERACTIVE_TEST_SITE", "does-not-exist")
    telemetry_stubs: list[_TelemetryStub] = []

    class _CapturingStub(_TelemetryStub):
        """Capture the created emitter instance so the test can inspect events."""

        def __init__(self, path: str) -> None:
            super().__init__(path)
            telemetry_stubs.append(self)

    mistapi_module = MagicMock()
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
    mistapi_module.get_all.return_value = [{"id": "site-a", "name": "Alpha"}]
    runner = InteractiveTestRunner(
        menu_actions={"1": (lambda site_id=None: None, "Option One")},
        operation_registry=_OperationRegistryStub,
        telemetry_emitter_cls=_CapturingStub,
        config_utils=MagicMock(),
        mistapi_module=mistapi_module,
        apisession=MagicMock(),
        org_id_getter=lambda: "org-1",
        org_id_setter=lambda _v: None,
    )
    result = runner.execute()
    assert result is False  # WHY: unresolved selector -> suite verdict must be failure.
    assert telemetry_stubs, "emitter was never constructed"  # WHY: guard against stub wiring drift.
    event_types = [event[0] for event in telemetry_stubs[0].events]
    assert "start" not in event_types  # WHY: no option ran against a wrong site.
    assert "pass" not in event_types
    assert "fail" not in event_types


def test_run_single_option_marks_site_scoped_when_handler_accepts_site_id() -> None:
    """Handler accepting ``site_id`` must be recorded as ``interactive-site-scoped``.

    Why:
        Issue #1638 — reports must distinguish handlers invoked *with* a resolved
        site context from those invoked without one. Without this distinction the
        operator cannot tell whether a green pass actually exercised the test site
        or whether the callable ignored it entirely. The classifier is the
        ``test_mode`` positional passed to ``emit_test_pass``.
    """

    def _accepts_site(site_id: str | None = None) -> None:
        del site_id  # WHY: signature acceptance is the only behaviour under test.

    menu_actions = {"1": (_accepts_site, "Site-Scoped Op")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")

    success, failure = runner._run_option_loop(["1"], "site-1", emitter)

    assert success == 1
    assert failure == 0
    pass_events = [event for event in emitter.events if event[0] == "pass"]
    assert len(pass_events) == 1
    # WHY: emit_test_pass args tuple: (option, description, duration, test_mode)
    assert pass_events[0][1][3] == "interactive-site-scoped"


def test_run_single_option_marks_no_context_when_handler_lacks_site_id() -> None:
    """Handler without ``site_id`` parameter must be recorded as ``interactive-no-context``.

    Why:
        Issue #1638 — a handler that does not accept ``site_id`` cannot have been
        exercised against the resolved test site. Conflating it with a
        site-scoped pass hides a real coverage gap. The runner must classify the
        outcome via a distinct ``test_mode`` so downstream reports can separate
        the two populations.
    """

    def _no_site() -> None:
        return None

    menu_actions = {"1": (_no_site, "No Context Op")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")

    success, failure = runner._run_option_loop(["1"], "site-1", emitter)

    assert success == 1
    assert failure == 0
    pass_events = [event for event in emitter.events if event[0] == "pass"]
    assert len(pass_events) == 1
    assert pass_events[0][1][3] == "interactive-no-context"


def test_run_single_option_marks_prompt_cancelled_on_eof(caplog: pytest.LogCaptureFixture) -> None:
    """Handler raising ``EOFError`` must be recorded as ``interactive-cancelled``.

    Why:
        Issue #1638 — under ``--testinteractive`` an operator who cancels a
        handler's prompt with Ctrl-D produces an ``EOFError``. The current
        implementation catches this via the generic ``except Exception`` branch
        and reports the option identically to a genuine crash. Reports must
        distinguish an operator-cancelled prompt from a raised-exception failure
        so a benign cancellation cannot masquerade as a real regression. The
        outcome still counts against the suite verdict (the operation did not
        complete) but the ``test_mode`` on ``emit_test_fail`` must reflect the
        cancellation.
    """

    def _cancelled(site_id: str | None = None) -> None:
        del site_id  # WHY: cancellation is the only behaviour under test.
        raise EOFError("simulated Ctrl+D at prompt")

    menu_actions = {"1": (_cancelled, "Prompt Cancelled")}
    runner = _make_runner(menu_actions=menu_actions)
    emitter = _TelemetryStub("data/x.jsonl")

    with caplog.at_level(logging.WARNING):
        success, failure = runner._run_option_loop(["1"], "site-1", emitter)

    assert success == 0
    assert failure == 1  # WHY: cancellation still counts as a non-completion.
    fail_events = [event for event in emitter.events if event[0] == "fail"]
    pass_events = [event for event in emitter.events if event[0] == "pass"]
    assert len(fail_events) == 1
    assert not pass_events
    # WHY: emit_test_fail args tuple: (option, description, duration, error, test_mode)
    assert fail_events[0][1][4] == "interactive-cancelled"
