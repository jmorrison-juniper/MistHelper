"""Prove known child failures without turning an uncertain write into a failure."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import Mock

import pytest
import requests

from src.upgrade_portal.app.routes import org_upgrade
from tests.unit.upgrade_portal.test_org_child_controls import SITE_ONE, SITE_TWO, child, record, target

MACS = tuple(f"0011223344{number:02x}" for number in range(1, 9))


class CountSeeds:
    """Build durable count cases without a plan, a submission, or a cloud call."""

    @staticmethod
    def child(status: str, count: int, family: str = "gateway", offset: int = 0) -> dict[str, Any]:
        """Build one explicit target group with the actual stored status key."""
        site_id = SITE_ONE if offset == 0 else SITE_TWO
        targets = [target(mac, site_id, family, "1.0.0", "2.0.0") for mac in MACS[offset : offset + count]]
        row = child(f"count-{family}-{offset}", status, targets, site_id)
        row.update(device_family=family, raw_status=400 if status == "rejected" else None)
        row["route"] = "upgradeOrgDevices" if family == "ap" else "upgradeSiteDevices"
        row["error"] = "The cloud answered status 400." if status == "rejected" else "The child did not start."
        return row

    @staticmethod
    def operation(children: list[dict[str, Any]], state: str = "failed") -> dict[str, Any]:
        """Build an ordered record whose prior version readings need no cloud refresh."""
        result = record(deepcopy(children), state=state, record_version=1)
        result["versions_final"] = [row["child_id"] for row in children]
        result["actor_email"] = "count.operator@example.invalid"
        return result

    @classmethod
    def mixed(cls) -> dict[str, Any]:
        """Combine a native AP result and known failures across two sites and three families."""
        access_points = cls.child("completed", 2, "ap")
        access_points["status_data"] = {"targets": {"upgraded": list(MACS[:2]), "failed": []}}
        rejected = cls.child("rejected", 1, "gateway", 2)
        not_submitted = cls.child("not_submitted", 2, "switch", 3)
        rejected["cancellation"] = {"status": "unavailable", "message": "The cloud created no child job."}
        return cls.operation([access_points, rejected, not_submitted])

    @staticmethod
    def require_counts(summary: dict[str, Any], expected: list[tuple[int, int, int]]) -> None:
        """Check both count surfaces against an independent expected result."""
        actual = [(row["total"], row["upgraded"], row["failed"]) for row in summary["children"]]
        assert actual == expected, "The child counts lost a known outcome."
        totals = tuple(sum(values) for values in zip(*expected, strict=True)) if expected else (0, 0, 0)
        fields = ("total", "upgraded_count", "failed_count")
        assert tuple(summary[field] for field in fields) == totals, "The aggregate counts lost a known outcome."
        assert summary["site_upgrades"] == summary["children"]


@pytest.fixture(autouse=True)
def forbid_cloud(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Fail on a real SDK request and measure the zero-call boundary."""
    callback = Mock(side_effect=AssertionError("The count proof must make no cloud request."))
    monkeypatch.setattr(requests.Session, "request", callback)
    yield callback
    assert callback.call_count == 0


class TestRejectedChildCounts:
    """Check exact failed counts and the evidence that must remain unchanged."""

    @pytest.mark.parametrize(
        ("status", "count"), [("rejected", 1), ("not_submitted", 2), ("rejected", 0), ("not_submitted", 0)]
    )
    @pytest.mark.parametrize("cloud_data", [{}, {"targets": {"upgraded": [MACS[0]], "failed": [MACS[0]]}}])
    def test_known_outcomes_replace_cloud_counts(self, status: str, count: int, cloud_data: dict[str, Any]) -> None:
        """A known refusal has no successful cloud outcome and counts each explicit target once."""
        row = CountSeeds.child(status, count)
        row["status_data"] = deepcopy(cloud_data)
        original = deepcopy(row)
        assert org_upgrade._aggregate_child_counts(row) == (count, 0, count)
        summary = org_upgrade.aggregate_summary(CountSeeds.operation([row]))
        CountSeeds.require_counts(summary, [(count, 0, count)])
        assert row == original
        assert summary["children"][0]["status"] == status
        assert summary["children"][0]["error"] == row["error"]
        print(f"Checked 1 {status} record and 1 child row. Cloud callbacks: 0.")

    @pytest.mark.parametrize(
        "status",
        [
            "unknown",
            "submission_unknown",
            "read_unknown",
            "submission_claimed",
            "planned",
            "accepted",
            "partial",
            "running",
            "cancelled",
            "failed",
            "completed",
        ],
    )
    def test_uncertainty_and_lifecycle_states_infer_no_failure(self, status: str) -> None:
        """Only known no-write outcomes can replace cloud counts."""
        row = CountSeeds.child(status, 2)
        row["state"] = "rejected"
        assert org_upgrade._aggregate_child_counts(row) == (2, 0, 0)
        summary = org_upgrade.aggregate_summary(CountSeeds.operation([row], "attention_required"))
        CountSeeds.require_counts(summary, [(2, 0, 0)])
        assert summary["children"][0]["status"] == status
        row["status_data"] = {"targets": {"upgraded": [MACS[0]], "failed": [MACS[1]]}}
        assert org_upgrade._aggregate_child_counts(row) == (2, 1, 1)
        print(f"Checked 1 {status} control and 1 child row. Inferred failures: 0.")

    @pytest.mark.parametrize("raw_status", [None, 200, 202, 399, 500, 503])
    def test_an_uncertain_rejection_preserves_native_counts(self, raw_status: int | None) -> None:
        """A legacy rejected word cannot prove that an uncertain submission created no cloud job."""
        row = CountSeeds.child("rejected", 2)
        row["raw_status"] = raw_status
        row["error"] = (
            f"The cloud answered status {raw_status}."
            if raw_status is not None
            else "The submission response has no HTTP status."
        )
        assert org_upgrade._aggregate_child_counts(row) == (2, 0, 0)
        row["status_data"] = {"targets": {"upgraded": [MACS[0]], "failed": [MACS[1]]}}
        assert org_upgrade._aggregate_child_counts(row) == (2, 1, 1)

    @pytest.mark.parametrize("raw_status", [400, 401, 403, 404, 409, 429, 499])
    def test_existing_http_4xx_refusal_evidence_counts_each_target(self, raw_status: int) -> None:
        """The inclusive refused-status range defines the same known rejection as the cancellation reader."""
        row = CountSeeds.child("rejected", 1)
        row["raw_status"] = raw_status
        assert org_upgrade._aggregate_child_counts(row) == (1, 0, 1)

    def test_mixed_summary_and_negative_proof_preserve_uncertainty(self) -> None:
        """Both reporting surfaces must reject dropped failures and accept a zero-failure uncertainty control."""
        operation = CountSeeds.mixed()
        before = deepcopy(operation)
        summary = org_upgrade.aggregate_summary(operation)
        CountSeeds.require_counts(summary, [(2, 2, 0), (1, 0, 1), (2, 0, 2)])
        assert operation == before
        assert [row["device_family"] for row in summary["children"]] == ["ap", "gateway", "switch"]
        assert [row["mac"] for row in summary["devices"]] == list(MACS[:5])
        damaged = deepcopy(summary)
        damaged["failed_count"] = 0
        damaged["children"][1]["failed"] = 0
        with pytest.raises(AssertionError, match="lost a known outcome"):
            CountSeeds.require_counts(damaged, [(2, 2, 0), (1, 0, 1), (2, 0, 2)])
        control = org_upgrade.aggregate_summary(CountSeeds.operation([CountSeeds.child("submission_unknown", 1)]))
        CountSeeds.require_counts(control, [(1, 0, 0)])
        CountSeeds.require_counts(org_upgrade.aggregate_summary(CountSeeds.operation([])), [])
        print("Checked 3 mixed child rows, 5 device rows, 1 negative proof, and 1 uncertainty control.")


class TestNativeOutcomeCounts:
    """Preserve the actual cloud and completed-proof paths of the existing helper."""

    @pytest.mark.parametrize("array_name", ["site_upgrades", "upgrades"])
    @pytest.mark.parametrize("proven", [False, True])
    def test_nested_ap_arrays_and_completed_proof_keep_precedence(self, array_name: str, proven: bool) -> None:
        """Nested AP lists retain their counts, while completed proof keeps its device-level failure rule."""
        row = CountSeeds.child("completed", 3, "ap")
        row["status_data"] = {
            "targets": {"upgraded": list(MACS[:3]), "failed": list(MACS[:3])},
            array_name: [
                {"site_id": SITE_ONE, "upgrade": {"targets": {"upgraded": list(MACS[:2]), "failed": [MACS[2]]}}},
            ],
        }
        if proven:
            row["reconciliation"] = {"proven": True}
            row["status_data"]["targets"] = {}
        assert org_upgrade._aggregate_child_counts(row) == (3, 2, 1)
        row["status_data"] = {}
        assert org_upgrade._aggregate_child_counts(row) == ((3, 3, 0) if proven else (3, 0, 0))

    @pytest.mark.parametrize(
        "cloud_data",
        [
            None,
            [],
            "unreadable",
            {"targets": None},
            {"targets": {"upgraded": None, "failed": "unreadable"}},
            {"upgrades": None},
        ],
    )
    def test_unreadable_cloud_arrays_keep_zero_native_counts(self, cloud_data: Any) -> None:
        """Missing cloud evidence does not invent an outcome for an accepted child."""
        row = CountSeeds.child("accepted", 1)
        row["status_data"] = cloud_data
        assert org_upgrade._aggregate_child_counts(row) == (1, 0, 0)
