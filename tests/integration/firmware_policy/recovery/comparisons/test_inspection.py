"""Exercise offline SDK inspections without backup creation, proof consumption, or settings writes."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.changes import FirmwarePolicy
from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles
from src.operations.execution.firmware_policy.recovery.workflow import RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from src.operations.execution.firmware_policy.workflow import PolicyWorkflow
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID, SettingsSession
from web_portal.routes.firmware_policy.restore.inspection import HistoricalInspection, PreparedInspection


def prepared(tmp_path: Path) -> tuple[Any, SettingsSession]:
    """Prepare the real offline domain once so inspection tests have a genuine proof."""
    session = SettingsSession(tmp_path)
    workflow = PolicyWorkflow(PolicyApi(session), PolicyBackup(tmp_path))
    plans = [workflow.prepare({"id": ORG_ID, "name": "Fixture"}, [FirmwarePolicy("ap", False, {"AP41": "new"})])]
    return (workflow, plans, workflow.back_up(plans)), session


def test_prepared_policy_comparison_is_lazy_and_does_not_consume_proof(tmp_path: Path) -> None:
    """Read one current row while retaining exact complete recovery and application ability."""
    context, session = prepared(tmp_path)
    proof = context[2]
    content = proof.path.read_bytes()
    reads = len(session.reads)
    result = PreparedInspection.read(context, "site", SITE_ID)
    settings_reads = [uri for uri, _ in session.reads[reads:] if uri.endswith("/setting")]
    assert settings_reads == [f"/api/v1/sites/{SITE_ID}/setting"]
    assert result["columns"] == ["saved", "current", "proposed"]
    assert result["stale"] is False
    assert result["observed_at"] and result["snapshot_at"]
    assert "private-fixture" not in str(result)
    assert proof.consumed is False
    assert proof.path.read_bytes() == content
    assert len(list(proof.path.parent.glob("*.json"))) == 1
    assert session.writes == []
    workflow, plans, _ = context
    assert workflow.apply(plans, proof).failures == []


def test_prepared_restore_discloses_source_and_recovery_times_and_normalization(tmp_path: Path) -> None:
    """Retain raw source defaults while showing the exact normalized proposal."""
    context, session = prepared(tmp_path)
    files = BundleFiles(context[0].backup)
    workflow = RestoreWorkflow(PolicyApi(session), files)
    plan = workflow.prepare(context[2].path.stem, ["org:" + ORG_ID, "site:" + SITE_ID], "api.mist.com")
    proof = workflow.back_up(plan)
    result = PreparedInspection.read((workflow, plan, proof), "site", SITE_ID)
    assert result["recovery_snapshot_at"] != result["snapshot_at"]
    assert result["normalizations"] == [
        "normalized:auto_upgrade.day_of_week=any",
        "normalized:auto_upgrade.time_of_day=02:00",
    ]
    fields = {field["path"]: field for field in result["fields"]}
    assert fields["auto_upgrade.time_of_day"]["cells"]["saved"]["present"] is False
    assert fields["auto_upgrade.time_of_day"]["cells"]["proposed"]["value"] == "02:00"
    assert proof.consumed is False
    assert session.writes == []


@pytest.mark.parametrize("compare", [False, True])
def test_historical_view_is_explicit_and_immutable(tmp_path: Path, compare: bool) -> None:
    """Saved-only viewing does not request current settings or create a recovery bundle."""
    context, session = prepared(tmp_path)
    proof = context[2]
    workflow = RestoreWorkflow(PolicyApi(session), BundleFiles(context[0].backup))
    original = proof.path.read_bytes()
    session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["auto_upgrade"]["enabled"] = True
    start = len(session.reads)
    result = HistoricalInspection(workflow).read(proof.path.stem, "site:" + SITE_ID, compare)
    assert ("observed_at" in result) is compare
    reads = [uri for uri, _ in session.reads[start:] if uri.endswith("/setting")]
    assert reads == ([f"/api/v1/sites/{SITE_ID}/setting"] if compare else [])
    assert result["columns"] == (["saved", "current"] if compare else ["saved"])
    assert proof.path.read_bytes() == original
    assert len(list(proof.path.parent.glob("*.json"))) == 1
    assert session.writes == []


@pytest.mark.parametrize("status", [403, 503])
def test_current_failure_is_not_an_empty_success(tmp_path: Path, status: int) -> None:
    """Surface checked HTTP failures without returning private server response text."""
    context, session = prepared(tmp_path)
    session.fail_read = f"/api/v1/sites/{SITE_ID}/setting"
    session.status = status
    with pytest.raises(PolicyError, match=f"HTTP {status}") as failure:
        PreparedInspection.read(context, "site", SITE_ID)
    assert "private-fixture" not in str(failure.value)
    assert context[2].consumed is False
    assert session.writes == []


def test_current_drift_does_not_rebind_prepared_plan(tmp_path: Path) -> None:
    """Expose stale observation without replacing original complete private settings."""
    context, session = prepared(tmp_path)
    original = deepcopy(context[1][0].sites[0].original)
    session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["allow_mist"] = False
    result = PreparedInspection.read(context, "site", SITE_ID)
    assert result["stale"] is True
    assert context[1][0].sites[0].original == original
    assert context[2].consumed is False
    assert session.writes == []


def test_wrong_current_ownership_blocks_historical_values(tmp_path: Path) -> None:
    """Do not return saved values when current ownership conflicts with the backup."""
    context, session = prepared(tmp_path)
    session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["org_id"] = SITE_ID
    workflow = RestoreWorkflow(PolicyApi(session), BundleFiles(context[0].backup))
    with pytest.raises(PolicyError, match="ownership"):
        HistoricalInspection(workflow).read(context[2].path.stem, "site:" + SITE_ID, True)
    assert session.writes == []


def test_source_change_during_current_read_stops_disclosure(tmp_path: Path, monkeypatch: Any) -> None:
    """A replaced historical file cannot become a successful comparison response."""
    context, session = prepared(tmp_path)
    workflow = RestoreWorkflow(PolicyApi(session), BundleFiles(context[0].backup))
    read = workflow.api.read

    def replace(scope: Any, identifier: str) -> dict[str, Any]:
        """Change only a synthetic source after the initial source validation."""
        result = read(scope, identifier)
        context[2].path.write_text("{}", encoding="utf-8")
        return result

    monkeypatch.setattr(workflow.api, "read", replace)
    with pytest.raises(PolicyError, match="source backup changed"):
        HistoricalInspection(workflow).read(context[2].path.stem, "site:" + SITE_ID, True)
    assert session.writes == []


def test_4001_site_preparation_keeps_inspection_to_one_current_scope(tmp_path: Path) -> None:
    """Large private plans do not serialize thousands of settings values into job records."""
    from tests.integration.firmware_policy.test_scale import LargeSession

    session = LargeSession(tmp_path, 4001)
    workflow = PolicyWorkflow(PolicyApi(session), PolicyBackup(tmp_path))
    plans = [
        workflow.prepare({"id": identifier, "name": "Fixture"}, [FirmwarePolicy("ap", False, {"AP41": "0.15"})])
        for identifier in session.organizations
    ]
    proof = workflow.back_up(plans)
    start = len(session.reads)
    identifier = plans[0].sites[0].identifier
    result = PreparedInspection.read((workflow, plans, proof), "site", identifier)
    reads = [uri for uri, _ in session.reads[start:] if uri.endswith("/setting")]
    assert reads == [f"/api/v1/sites/{identifier}/setting"]
    assert result["id"] == identifier
    assert len(result["fields"]) < 30
    assert len(proof.records) == 4003
    assert proof.consumed is False
    assert session.writes == []
