"""Tests proving pre-checks fetch the org device inventory once per run.

Issue #1886. Before this fix, PreCheckService called list_all_entities
once for every target device, so a run over N devices paged the whole
org inventory N times. These tests prove the fetch count no longer
depends on the number of target devices.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.worker.checks.pre_checks import PreCheckService

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
