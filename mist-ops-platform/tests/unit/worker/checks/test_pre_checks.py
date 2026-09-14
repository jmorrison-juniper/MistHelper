"""Tests proving pre-checks fetch the org device inventory once per run.

Issue #1886. Before this fix, PreCheckService called list_all_entities
once for every target device, so a run over N devices paged the whole
org inventory N times. These tests prove the fetch count no longer
depends on the number of target devices.

Issue #2038, finding 3: the version compatibility check always returned
a passing result with no comparison. These tests prove the fix.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from src.worker.checks.pre_checks import CheckResult, PreCheckService

if TYPE_CHECKING:
    import pytest

EXPECTED_INVENTORY_FETCHES_PER_RUN = 1  # WHY: name the proof value instead of a bare 1.
SMALL_FLEET_SIZE = 5  # WHY: a small fleet must still cause one fetch.
LARGE_FLEET_SIZE = 50  # WHY: a much larger fleet must still cause one fetch.


def _mock_inventory(device_ids: list[str]) -> SimpleNamespace:
    """Build a mock org_device_list response covering every device id."""
    # WHY: one connected record per id, matching the real API shape.
    records = [{"id": device_id, "status": "connected"} for device_id in device_ids]
    return SimpleNamespace(status_code=200, data=records)


def _make_service(device_ids: list[str]) -> PreCheckService:
    """Build a PreCheckService whose Mist client returns one inventory page."""
    mist = MagicMock()  # WHY: stand in for the real Mist client.
    # WHY: one page must answer for every device the test checks.
    mist.list_all_entities.return_value = _mock_inventory(device_ids)
    return PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused by these checks.


class TestInventoryFetchCountIsIndependentOfFleetSize:
    """Verify one run makes exactly one inventory call, for any fleet size."""

    def test_five_targets_make_one_inventory_fetch(self) -> None:
        # WHY: build a small fleet of distinct device ids.
        device_ids = [f"dev-{i}" for i in range(SMALL_FLEET_SIZE)]
        service = _make_service(device_ids)

        service.run_all("org-1", device_ids)  # WHY: exercise the full check pipeline.

        # WHY: prove the fetch count does not grow with the target count.
        assert service._mist.list_all_entities.call_count == EXPECTED_INVENTORY_FETCHES_PER_RUN

    def test_fifty_targets_still_make_one_inventory_fetch(self) -> None:
        # WHY: build a much larger fleet to prove the count stays constant.
        device_ids = [f"dev-{i}" for i in range(LARGE_FLEET_SIZE)]
        service = _make_service(device_ids)

        service.run_all("org-1", device_ids)  # WHY: exercise the full check pipeline.

        # WHY: the fix makes the count constant, not one call per device.
        assert service._mist.list_all_entities.call_count == EXPECTED_INVENTORY_FETCHES_PER_RUN

    def test_zero_targets_make_zero_inventory_fetches(self) -> None:
        service = _make_service([])  # WHY: an empty run has nothing to check.

        service.run_all("org-1", [])  # WHY: exercise the full check pipeline.

        # WHY: no targets means no reason to call the Mist API at all.
        assert service._mist.list_all_entities.call_count == 0


class TestReachabilityResultsUseTheSharedIndex:
    """Verify per-device results still reflect each device's real status."""

    def test_connected_devices_pass_and_disconnected_devices_fail(self) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        # WHY: one page holds a mix of healthy and unhealthy devices.
        mist.list_all_entities.return_value = SimpleNamespace(
            status_code=200,
            data=[
                {"id": "dev-a", "status": "connected"},
                {"id": "dev-b", "status": "disconnected"},
            ],
        )
        service = PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused here.

        # WHY: run both devices through the real pipeline.
        results = service.run_all("org-1", ["dev-a", "dev-b"])

        by_name = {r.name: r for r in results}  # WHY: index results for a readable assertion.
        assert by_name["reachability:dev-a"].passed is True  # WHY: connected must pass.
        assert by_name["reachability:dev-b"].passed is False  # WHY: disconnected must fail.

    def test_a_device_missing_from_inventory_fails_with_a_clear_message(self) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        # WHY: dev-x is deliberately absent from the returned page.
        mist.list_all_entities.return_value = _mock_inventory(["dev-a"])
        service = PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused here.

        # WHY: dev-x is not in the inventory page, so it must fail cleanly.
        results = service.run_all("org-1", ["dev-x"])

        by_name = {r.name: r for r in results}  # WHY: index results for a readable assertion.
        assert by_name["reachability:dev-x"].passed is False  # WHY: a missing device must fail.
        # WHY: message names the cause.
        assert "not found" in by_name["reachability:dev-x"].message


class TestInventoryFetchFailureFailsEveryTarget:
    """Verify a failed shared fetch fails every device instead of crashing."""

    def test_an_api_exception_fails_every_target_with_the_error(self) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        # WHY: simulate the Mist API being unreachable for the shared fetch.
        mist.list_all_entities.side_effect = RuntimeError("Mist API unreachable")
        service = PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused here.

        # WHY: both devices depend on the one failed shared fetch.
        results = service.run_all("org-1", ["dev-a", "dev-b"])

        by_name = {r.name: r for r in results}  # WHY: index results for a readable assertion.
        assert by_name["reachability:dev-a"].passed is False  # WHY: no device can pass on failure.
        assert by_name["reachability:dev-b"].passed is False  # WHY: no device can pass on failure.
        # WHY: the failure detail must reach the caller, not just False.
        assert "Mist API unreachable" in by_name["reachability:dev-a"].message
        # WHY: the failure must still cost exactly one fetch attempt, not two.
        assert mist.list_all_entities.call_count == EXPECTED_INVENTORY_FETCHES_PER_RUN


class TestReachabilityFailuresFailClosed:
    """Verify unusual target results fail closed."""

    def test_target_check_exception_returns_failed_result(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        mist.list_all_entities.return_value = _mock_inventory(["dev-a"])  # WHY: let fetch pass.
        service = PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused here.

        def _raise_for_target(
            _device_id: str,
            _device_index: dict[str, dict[str, object]],
            _fetch_error: str | None,
        ) -> CheckResult:
            raise RuntimeError("target check failed")  # WHY: prove a bad target cannot crash.

        monkeypatch.setattr(service, "_ping_device", _raise_for_target)  # WHY: simulate failure.

        results = service.run_all("org-1", ["dev-a"])  # WHY: exercise the guarded path.

        by_name = {r.name: r for r in results}  # WHY: index results for a readable assertion.
        assert by_name["reachability:dev-a"].passed is False  # WHY: exceptions fail closed.
        assert "target check failed" in by_name["reachability:dev-a"].message  # WHY: show cause.

    def test_target_check_none_returns_failed_result(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        mist.list_all_entities.return_value = _mock_inventory(["dev-a"])  # WHY: let fetch pass.
        service = PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused here.
        monkeypatch.setattr(
            service,
            "_ping_device",
            lambda _device_id, _device_index, _fetch_error: None,
        )  # WHY: simulate a broken target check that returns no verdict.

        results = service.run_all("org-1", ["dev-a"])  # WHY: exercise the guarded path.

        by_name = {r.name: r for r in results}  # WHY: index results for a readable assertion.
        assert by_name["reachability:dev-a"].passed is False  # WHY: no verdict fails closed.
        assert "no result" in by_name["reachability:dev-a"].message  # WHY: show cause.


class TestInventoryPermissionFailure:
    """Verify API status errors do not look like absent devices."""

    def test_permission_failure_reports_permission_error(self) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        mist.list_all_entities.return_value = SimpleNamespace(
            status_code=403,
            data=[],
        )  # WHY: simulate an authenticated account without inventory permission.
        service = PreCheckService(MagicMock(), mist)  # WHY: the DB session is unused here.

        results = service.run_all("org-1", ["dev-a"])  # WHY: exercise the fetch status check.

        by_name = {r.name: r for r in results}  # WHY: index results for a readable assertion.
        assert by_name["reachability:dev-a"].passed is False  # WHY: permission blocks proof.
        assert "Permission denied" in by_name["reachability:dev-a"].message  # WHY: show cause.


# ---------------------------------------------------------------------------
# Issue #2038, finding 3: version compatibility check must not report a pass
# ---------------------------------------------------------------------------


class TestVersionCompatUsesConfiguredMinimum:
    """Prove that version_compat compares the configured minimum version."""

    def test_version_compat_passes_when_device_meets_the_floor(self) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        mist.list_all_entities.return_value = SimpleNamespace(
            status_code=200,
            data=[{"id": "dev-a", "status": "connected", "firmware_version": "1.2.0"}],
        )  # WHY: supply the version data that the check must compare.
        service = PreCheckService(MagicMock(), mist)  # WHY: DB session unused here.
        check_defs = [{"type": "version_compat", "min_version": "1.1.0"}]  # WHY: set a gate.

        results = service.run_all("org-1", ["dev-a"], check_defs)  # WHY: exercise the pipeline.

        by_name = {r.name: r for r in results}  # WHY: index for a readable assertion.
        compat_result = by_name["version_compat:dev-a"]  # WHY: read the exact check result.
        assert compat_result.passed is True  # WHY: 1.2.0 is compatible with the 1.1.0 floor.

    def test_version_compat_fails_when_device_is_below_the_floor(self) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        mist.list_all_entities.return_value = SimpleNamespace(
            status_code=200,
            data=[{"id": "dev-b", "status": "connected", "version": "1.0.0"}],
        )  # WHY: use the Mist field name for coverage.
        service = PreCheckService(MagicMock(), mist)  # WHY: DB session unused here.
        check_defs = [{"type": "version_compat", "min_version": "1.1.0"}]  # WHY: set a gate.

        results = service.run_all("org-1", ["dev-b"], check_defs)  # WHY: exercise the pipeline.

        by_name = {r.name: r for r in results}  # WHY: index for a readable assertion.
        compat_result = by_name["version_compat:dev-b"]  # WHY: read the exact check result.
        assert compat_result.passed is False  # WHY: 1.0.0 is below the 1.1.0 floor.
        assert "below" in compat_result.message  # WHY: the operator needs the failure cause.

    def test_version_compat_is_absent_when_no_gate_is_configured(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mist = MagicMock()  # WHY: stand in for the real Mist client.
        mist.list_all_entities.return_value = SimpleNamespace(
            status_code=200,
            data=[{"id": "dev-c", "status": "connected", "version": "1.0.0"}],
        )  # WHY: supply a connected device so reachability passes.
        service = PreCheckService(MagicMock(), mist)  # WHY: DB session unused here.

        with caplog.at_level(logging.WARNING, logger="src.worker.checks.pre_checks"):
            results = service.run_all("org-1", ["dev-c"])  # WHY: run without a version gate.

        by_name = {r.name: r for r in results}  # WHY: index for a readable assertion.
        assert "version_compat:dev-c" not in by_name  # WHY: absent gates must not block a job.
        assert any(r.levelno >= logging.WARNING for r in caplog.records)  # WHY: log the skip.
