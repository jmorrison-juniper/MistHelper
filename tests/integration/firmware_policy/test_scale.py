"""Prove complete, ordered policy and restoration above four thousand sites."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest

from src.operations.execution.firmware_policy.changes import FirmwarePolicy
from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles
from src.operations.execution.firmware_policy.recovery.workflow import RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from src.operations.execution.firmware_policy.workflow import PolicyWorkflow
from tests.unit.prod_readiness.operations.execution.firmware.policy.fakes import SettingsSession


class LargeSession(SettingsSession):
    """Keep exact SDK read and write evidence for two large organizations."""

    def __init__(self, directory: Path, count: int) -> None:
        """Create independent identifiers and named current site memberships."""
        super().__init__(directory)
        self.cloud = "api.mist.com"
        self.organizations = [str(UUID(int=1)), str(UUID(int=2))]
        self.listings: dict[str, list[dict[str, str]]] = {identifier: [] for identifier in self.organizations}
        self.settings = {}
        for organization in self.organizations:
            self.settings[f"/api/v1/orgs/{organization}/setting"] = {
                "org_id": organization,
                "allow_mist": False,
                "auto_upgrade": {"enabled": False, "day_of_week": "any", "time_of_day": "02:00"},
            }
        for index in range(count):
            organization = self.organizations[index % 2]
            identifier = str(UUID(int=index + 10))
            self.listings[organization].append({"id": identifier, "org_id": organization, "name": f"Site {index:05d}"})
            self.settings[f"/api/v1/sites/{identifier}/setting"] = {
                "site_id": identifier,
                "org_id": organization,
                "auto_upgrade": {"enabled": False, "day_of_week": "any", "time_of_day": "02:00"},
            }

    def get_cloud(self) -> str:
        """Expose the fixture cloud without a network connection."""
        return self.cloud

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Return exact named memberships and identities through the SDK session."""
        for organization in self.organizations:
            if uri == f"/api/v1/orgs/{organization}/sites":
                self.reads.append((uri, query or {}))
                return SimpleNamespace(status_code=200, data=deepcopy(self.listings[organization]), next=None)
            if uri == f"/api/v1/orgs/{organization}":
                self.reads.append((uri, query or {}))
                return SimpleNamespace(
                    status_code=200, data={"id": organization, "name": f"Organization {organization}"}
                )
        return super().mist_get(uri, query)


@pytest.mark.parametrize("kind", ["policy", "restore"])
def test_complete_4001_site_run_has_exact_linear_calls_and_org_first_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Every scope receives one verified write with constant membership and source reads."""
    session = LargeSession(tmp_path, 4001)
    api = PolicyApi(session)
    backup = PolicyBackup(tmp_path)
    events: list[dict[str, Any]] = []
    if kind == "policy":
        workflow = PolicyWorkflow(api, backup, progress=events.append)
        policy = FirmwarePolicy("ap", False, {"AP41": "0.15"}, "any", "02:00")
        plans = [
            workflow.prepare({"id": identifier, "name": identifier}, [policy]) for identifier in session.organizations
        ]
        proof = workflow.back_up(plans)
        result = workflow.apply(plans, proof=proof)
        assert result.failures == result.remaining == []
        assert len(result.sites) == 4001
    else:
        records = [
            {
                "scope": "org" if "/orgs/" in uri else "site",
                "id": uri.split("/")[-2],
                "settings": {**settings, **({"allow_mist": True} if "/orgs/" in uri else {})},
            }
            for uri, settings in session.settings.items()
        ]
        source = backup.save(records)
        files = BundleFiles(backup)
        parsed: list[str] = []
        read = BundleFiles.read

        def counted_read(self: BundleFiles, token: str) -> Any:
            """Record complete source parses without replacing integrity checks."""
            parsed.append(token)
            return read(self, token)

        monkeypatch.setattr(BundleFiles, "read", counted_read)
        workflow_restore = RestoreWorkflow(api, files, progress=events.append)
        selected = [f"{record['scope']}:{record['id']}" for record in records]
        plan = workflow_restore.prepare(source.stem, selected, session.cloud)
        proof = workflow_restore.back_up(plan)
        restored = workflow_restore.apply(plan, "RESTORE", proof=proof)
        assert restored.failed == restored.remaining == []
        assert len(restored.completed) == 4003
        assert parsed.count(source.stem) == 3
    expected_orgs = [f"/api/v1/orgs/{identifier}/setting" for identifier in session.organizations]
    expected_sites = sorted(uri for uri in session.settings if "/sites/" in uri)
    writes = [uri for uri, body in session.writes]
    assert writes[:2] == expected_orgs
    assert Counter(writes) == Counter(expected_orgs + expected_sites)
    reads = Counter(uri for uri, query in session.reads)
    assert all(reads[uri] == 5 for uri in expected_sites)
    assert all(reads[uri] == 5 for uri in expected_orgs)
    assert sum(count for uri, count in reads.items() if uri.endswith("/sites")) == (6 if kind == "policy" else 8)
    assert reads["/api/v1/self/usage"] >= 5  # The rolling quota requires repeated real observations.
    assert any(event["phase"] == "backup_verified" and event["completed"] == 4003 for event in events)
    assert sum(event["phase"] == "applied" for event in events) == 4003


def test_realistic_144_site_backup_above_17402805_bytes_roundtrips_privately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Legacy-sized 121,856-character site settings survive complete verified restoration."""
    session = LargeSession(tmp_path, 144)
    first, second = session.organizations
    session.listings[first].extend(session.listings.pop(second))
    session.organizations = [first]
    del session.settings[f"/api/v1/orgs/{second}/setting"]
    for site in session.listings[first]:
        site["org_id"] = first
        session.settings[f"/api/v1/sites/{site['id']}/setting"]["org_id"] = first
    payload = "x" * 121856
    records = [
        {
            "scope": "org" if "/orgs/" in uri else "site",
            "id": uri.split("/")[-2],
            "settings": {**settings, "ssr": {"conductor_token": payload}},
        }
        for uri, settings in session.settings.items()
    ]
    backup = PolicyBackup(tmp_path)
    source = backup.save(records)
    assert source.stat().st_size > 17402805
    files = BundleFiles(backup)
    workflow = RestoreWorkflow(PolicyApi(session), files)
    selected = [f"{record['scope']}:{record['id']}" for record in records]
    plan = workflow.prepare(source.stem, selected, session.cloud)
    assert len(plan.targets) == 145
    assert payload not in json.dumps(plan.preview())
    result = workflow.apply(plan, "RESTORE", proof=workflow.back_up(plan))
    assert result.failed == result.remaining == []
    assert len(result.completed) == 145
    assert files.read(source.stem).records == records
    assert all("ssr" not in settings for settings in session.settings.values())
    assert all("ssr" not in body for uri, body in session.writes)


@pytest.mark.parametrize("status", [403, 503])
def test_http_4xx_and_http_5xx_large_membership_failure_stops_before_settings_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """A failed large membership page cannot become a partial policy target list."""
    session = LargeSession(tmp_path, 4001)
    original = session.mist_get
    failed_uri = f"/api/v1/orgs/{session.organizations[0]}/sites"

    def failed_membership(uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Fail the authoritative membership request without leaking response contents."""
        if uri == failed_uri:
            session.reads.append((uri, query or {}))
            return SimpleNamespace(status_code=status, data={"error": "private-fixture"}, next=None)
        return original(uri, query)

    monkeypatch.setattr(session, "mist_get", failed_membership)
    workflow = PolicyWorkflow(PolicyApi(session), PolicyBackup(tmp_path))
    with pytest.raises(PolicyError, match=f"HTTP {status}"):
        workflow.prepare({"id": session.organizations[0]}, [FirmwarePolicy("ap", False, {"AP41": "0.15"})])
    assert session.writes == []
    assert not any("/sites/" in uri for uri, query in session.reads)
    assert [uri for uri, query in session.reads].count(failed_uri) == 1


def test_realistic_4001_site_policy_backup_restore_pipeline_has_complete_ordered_calls(tmp_path: Path) -> None:
    """Restore the actual large policy recovery file with exact complete SDK call evidence."""
    session = LargeSession(tmp_path, 4001)
    payload = "x" * 121856
    for uri, settings in session.settings.items():
        settings["ssr"] = {"conductor_token": payload}
        settings["unknown_response_field"] = None
        settings["uwb_config"] = {"port": None}
        settings["mist_nac"] = {"idps": [{"id": session.organizations[0]}]}
        if "/orgs/" in uri:
            settings["auto_upgrade"] = {"enabled": False, "day_of_week": "any", "time_of_day": "02:00"}
    original = deepcopy(session.settings)
    backup = PolicyBackup(tmp_path)
    api = PolicyApi(session)
    workflow = PolicyWorkflow(api, backup)
    policy = FirmwarePolicy("ap", False, {"AP41": "0.15"}, "any", "02:00")
    plans = [workflow.prepare({"id": identifier, "name": identifier}, [policy]) for identifier in session.organizations]
    proof = workflow.back_up(plans)
    source = proof.path
    assert source.stat().st_size > 480_000_000
    changed = workflow.apply(plans, proof=proof)
    assert changed.failures == changed.remaining == []
    assert len(changed.organizations) == 2
    assert len(changed.sites) == 4001
    selected = [f"{'org' if '/orgs/' in uri else 'site'}:{uri.split('/')[-2]}" for uri in original]
    restore = RestoreWorkflow(PolicyApi(session), BundleFiles(backup))
    plan = restore.prepare(source.stem, selected, session.cloud)
    restored = restore.apply(plan, "RESTORE", proof=restore.back_up(plan))
    assert restored.failed == restored.remaining == []
    assert len(restored.completed) == 4003
    assert session.settings == original
    writes = [uri for uri, body in session.writes]
    expected_orgs = [f"/api/v1/orgs/{identifier}/setting" for identifier in session.organizations]
    assert writes[:2] == writes[4003:4005] == expected_orgs
    assert Counter(writes) == Counter({uri: 2 for uri in original})
    reads = Counter(uri for uri, query in session.reads)
    assert all(reads[uri] == 10 for uri in original)
    assert sum(count for uri, count in reads.items() if uri.endswith("/sites")) == 14
    assert reads["/api/v1/self/usage"] == 10
    assert len(writes) == 8006
    print(
        json.dumps(
            {
                "source_bytes": source.stat().st_size,
                "records": 4003,
                "settings_reads": 40030,
                "settings_writes": len(writes),
                "membership_reads": 14,
                "usage_reads": reads["/api/v1/self/usage"],
            }
        )
    )
