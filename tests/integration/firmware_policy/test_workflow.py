"""Exercise real SDK settings calls, full backup gates, and partial policy outcomes offline."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.operations.execution.firmware_policy.backup import PolicyBackup
from src.operations.execution.firmware_policy.changes import FirmwarePolicy
from src.operations.execution.firmware_policy.cli import PolicyCatalog, PolicyMenu, PolicyMenuInputs, PolicyPrompt
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from src.operations.execution.firmware_policy.workflow import PolicyWorkflow
from tests.unit.firmware_policy.fakes import ORG_ID, OTHER_SITE_ID, SITE_ID, SettingsSession


def prepared(tmp_path: Path) -> tuple[SettingsSession, PolicyWorkflow, list[Any]]:
    """Build a complete offline organization plan through the actual SDK methods."""
    session = SettingsSession(tmp_path)
    workflow = PolicyWorkflow(PolicyApi(session), PolicyBackup(tmp_path))
    policy = FirmwarePolicy("ap", False, {"AP41": "new"}, "mon", "02:00")
    plans = [workflow.prepare({"id": ORG_ID, "name": "Example"}, [policy])]
    return session, workflow, plans


def test_confirmed_settings_flow_backs_up_every_scope_before_any_write(tmp_path: Path) -> None:
    """Save organization standards first, then clear only local site overrides."""
    session, workflow, plans = prepared(tmp_path)
    result = workflow.apply(plans)
    assert result.organizations == [ORG_ID]
    assert result.sites == [SITE_ID]
    assert result.unchanged == [OTHER_SITE_ID]
    assert result.failures == []
    assert result.remaining == []
    assert [uri for uri, _ in session.writes] == [f"/api/v1/orgs/{ORG_ID}/setting", f"/api/v1/sites/{SITE_ID}/setting"]
    bundle = next((tmp_path / ".firmware-policy-backups").glob("*.json"))
    records = json.loads(bundle.read_text())["records"]
    assert len(records) == 3
    assert records[0]["settings"] == plans[0].original
    assert records[1]["settings"] == plans[0].sites[0].original
    assert records[2]["settings"] == plans[0].sites[1].original
    assert "auto_upgrade" not in session.settings[f"/api/v1/sites/{SITE_ID}/setting"]
    assert session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["ssr"] == {"conductor_token": "private-fixture"}


@pytest.mark.parametrize("scope", ["org", "site"])
@pytest.mark.parametrize("status", [403, 503])
def test_http_failures_report_partial_and_stop_remaining_work(tmp_path: Path, scope: str, status: int) -> None:
    """HTTP 4xx and 5xx must never appear as a successful settings change."""
    session, workflow, plans = prepared(tmp_path)
    identifier = ORG_ID if scope == "org" else SITE_ID
    session.fail_write = f"/api/v1/{'orgs' if scope == 'org' else 'sites'}/{identifier}/setting"
    session.status = status
    result = workflow.apply(plans)
    assert len(result.failures) == 1
    assert f"HTTP {status}" in result.failures[0]
    assert result.organizations == ([] if scope == "org" else [ORG_ID])
    assert result.sites == []
    assert result.remaining == [SITE_ID, OTHER_SITE_ID]
    assert len(session.writes) == (1 if scope == "org" else 2)


def test_unverified_organization_prevents_all_site_changes(tmp_path: Path) -> None:
    """Refuse false HTTP success before exposing sites to an unverified policy."""
    session, workflow, plans = prepared(tmp_path)
    session.ignore_write = True
    result = workflow.apply(plans)
    assert result.organizations == []
    assert result.sites == []
    assert "verification failed" in result.failures[0]
    assert len(session.writes) == 1


def test_backup_failure_or_corruption_prevents_every_cloud_write(tmp_path: Path, monkeypatch: Any) -> None:
    """A complete plan still cannot bypass a failed full-backup verification gate."""
    session, workflow, plans = prepared(tmp_path)

    def failed_verify(path: Path, expected: list[dict]) -> None:
        """Simulate a detected corrupt bundle before the apply boundary."""
        raise PolicyError("The settings backup does not match the original settings.")

    monkeypatch.setattr(workflow.backup, "verify", failed_verify)
    with pytest.raises(PolicyError, match="backup does not match"):
        workflow.apply(plans)
    assert session.writes == []


@pytest.mark.parametrize("content", [b"", b"bad json"])
def test_empty_body_and_malformed_json_backup_prevent_all_writes(
    tmp_path: Path, monkeypatch: Any, content: bytes
) -> None:
    """Exercise the actual backup parser before the first permitted settings request."""
    session, workflow, plans = prepared(tmp_path)
    create_file = workflow.backup._create_file

    def corrupt_bundle(document: dict[str, Any]) -> Path:
        """Replace a completed bundle with an empty or malformed response-shaped file."""
        path = create_file(document)
        path.write_bytes(content)
        return path

    monkeypatch.setattr(workflow.backup, "_create_file", corrupt_bundle)
    with pytest.raises(PolicyError, match="could not be verified"):
        workflow.apply(plans)
    assert session.writes == []


def test_stale_preview_or_stop_signal_prevents_cloud_writes(tmp_path: Path) -> None:
    """Require the backed-up settings to match the current complete settings."""
    session, workflow, plans = prepared(tmp_path)
    session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["timezone"] = "UTC"
    with pytest.raises(PolicyError, match="changed after preview"):
        workflow.apply(plans)
    assert session.writes == []
    workflow.stopped = lambda: True
    with pytest.raises(PolicyError, match="cancelled"):
        workflow.apply(plans)
    assert session.writes == []


@pytest.mark.parametrize("status", [403, 503])
def test_required_read_failure_prevents_planning(tmp_path: Path, status: int) -> None:
    """Missing site settings cannot become an empty successful target list."""
    session = SettingsSession(tmp_path)
    session.fail_read = f"/api/v1/sites/{SITE_ID}/setting"
    session.status = status
    workflow = PolicyWorkflow(PolicyApi(session), PolicyBackup(tmp_path))
    with pytest.raises(PolicyError, match=f"HTTP {status}"):
        workflow.prepare({"id": ORG_ID}, [FirmwarePolicy("ap", False, {"AP41": "new"})])
    assert session.writes == []


@pytest.mark.parametrize("dry_run,confirmation", [(True, ""), (False, "NO"), (False, ""), (False, "CONFIGURE")])
def test_cli_dry_run_cancel_and_confirm_paths(tmp_path: Path, capsys: Any, dry_run: bool, confirmation: str) -> None:
    """Use familiar model selection without calling any firmware execution method."""
    session = SettingsSession(tmp_path)
    answers = iter(["1", "1", "1", "DISABLE", "mon", "02:00", confirmation])
    menu = PolicyMenu(
        PolicyApi(session),
        PolicyMenuInputs(lambda: ORG_ID, dry_run=dry_run, data_directory=tmp_path),
        PolicyPrompt(lambda prompt: next(answers)),
    )
    menu.run()
    output = capsys.readouterr().out
    assert "Warning:" in output
    assert SITE_ID in output and OTHER_SITE_ID in output
    if not dry_run and confirmation == "CONFIGURE":
        assert len(session.writes) == 2
        assert "Verified organization changes: 1" in output
    else:
        assert session.writes == []
        assert not (tmp_path / ".firmware-policy-backups").exists()
    assert "private-fixture" not in output


def test_catalog_supports_ap_switch_srx_and_ssr_models(tmp_path: Path) -> None:
    """Use per-type SDK catalogs and inventory-derived SSR model names."""
    session = SettingsSession(tmp_path)
    api = PolicyApi(session)
    catalogs = PolicyCatalog.common(api, [{"id": ORG_ID}], ["ap", "switch", "juniper_srx", "ssr"])
    assert catalogs["ap"]["AP41"] == ["new", "stable"]
    assert catalogs["switch"]["EX4400"] == ["new", "stable"]
    assert catalogs["juniper_srx"]["SRX320"] == ["new", "stable"]
    assert catalogs["ssr"]["SSR120"] == ["6.3.0"]
    assert session.writes == []
    with pytest.raises(PolicyError, match="not available"):
        PolicyCatalog.validate([FirmwarePolicy("ap", False, {"AP41": "missing"})], catalogs)


def test_multiple_organizations_share_one_verified_complete_backup(tmp_path: Path, monkeypatch: Any) -> None:
    """Back up all selected organizations and all their sites before the first change."""
    session = SettingsSession(tmp_path)
    other_org = "00000000-0000-0000-0000-000000000004"
    other_site = "00000000-0000-0000-0000-000000000005"
    session.settings[f"/api/v1/orgs/{other_org}/setting"] = deepcopy(session.settings[f"/api/v1/orgs/{ORG_ID}/setting"])
    session.settings[f"/api/v1/sites/{other_site}/setting"] = {"auto_upgrade": {"enabled": True}, "timezone": "UTC"}
    original_get = session.mist_get

    def get(uri: str, query: dict[str, str] | None = None) -> Any:
        """Give the second organization its own site without real transport."""
        if uri == f"/api/v1/orgs/{other_org}/sites":
            return SimpleNamespace(status_code=200, data=[{"id": other_site, "name": "Second org site"}], next=None)
        return original_get(uri, query)

    monkeypatch.setattr(session, "mist_get", get)
    workflow = PolicyWorkflow(PolicyApi(session), PolicyBackup(tmp_path))
    policies = [FirmwarePolicy("ap", False, {"AP41": "new"}, "fri", "03:00")]
    plans = [workflow.prepare({"id": identifier}, policies) for identifier in (ORG_ID, other_org)]
    result = workflow.apply(plans)
    assert result.organizations == [ORG_ID, other_org]
    assert result.sites == [SITE_ID, other_site]
    assert result.failures == []
    document = json.loads(next((tmp_path / ".firmware-policy-backups").glob("*.json")).read_text())
    assert document["record_count"] == 5
    assert {record["id"] for record in document["records"]} == {ORG_ID, other_org, SITE_ID, OTHER_SITE_ID, other_site}
    assert len(session.writes) == 4


def test_msp_selectors_are_reused_without_running_upgrade_workflows(tmp_path: Path, capsys: Any) -> None:
    """Exercise the injected menu 168 organization selection flow with a read-only dry run."""
    session = SettingsSession(tmp_path)
    calls: list[str] = []

    def select_msps() -> list[dict[str, str]]:
        """Record the read-only MSP selection hook."""
        calls.append("msps")
        return [{"msp_id": ORG_ID}]

    def select_orgs(msp: dict[str, str]) -> list[dict[str, str]]:
        """Record the read-only organization selection hook."""
        calls.append(msp["msp_id"])
        return [{"id": ORG_ID, "name": "MSP organization"}]

    answers = iter(["2", "1", "1", "1", "DISABLE", "any", "any"])
    inputs = PolicyMenuInputs(lambda: None, (select_msps, select_orgs), dry_run=True, data_directory=tmp_path)
    PolicyMenu(PolicyApi(session), inputs, PolicyPrompt(lambda prompt: next(answers))).run()
    assert calls == ["msps", ORG_ID]
    assert "MSP organization" in capsys.readouterr().out
    assert session.writes == []
