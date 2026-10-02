"""Build a plan-only portal with counted cloud and start boundaries."""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Callable
from dataclasses import asdict
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from flask import Flask

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app.config import SECRET_KEY_VARIABLE
from src.upgrade_portal.app.factory import create_app
from src.upgrade_portal.app.routes import org_upgrade
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.upgrade import options as option_rules
from tests.support.upgrade_portal_e2e import build_e2e_overrides


class FailureLimitScope:
    """Supply two sites and model-specific inventory without a cloud read."""

    org_id = "11111111-1111-1111-1111-111111111111"
    facts: dict[str, Any] = {
        "sites": [
            {"id": "22222222-2222-2222-2222-222222222222", "name": "Failure limit site one"},
            {"id": "33333333-3333-3333-3333-333333333333", "name": "Failure limit site two"},
        ],
        "versions": {
            "AP45": ("0.14.1", "0.15.1"),
            "EX4400": ("23.4R1.8", "23.4R1.9"),
            "SRX320": ("23.4R1.8", "23.4R1.9"),
        },
        "form": {
            "selected_types": ["ap", "switch", "gateway"],
            "reboot": "yes",
            "junos_file_action": "yes",
            "reboot_at": "",
            "start_time": "",
            "stable_version": "no",
            "enable_p2p": "no",
        },
        "radio_fields": (
            "rrm_first_batch_percentage",
            "rrm_max_batch_percentage",
            "rrm_node_order",
            "rrm_mesh_upgrade",
            "rrm_slow_ramp",
        ),
        "actions": ("capture_runner", "run_launcher", "stop_runner", "options_builder"),
    }

    @classmethod
    def devices(cls, site_id: str) -> list[dict[str, Any]]:
        """Return three supported devices of the named site."""
        site_index = [site["id"] for site in cls.facts["sites"]].index(site_id)
        rows = []
        for index, (family, model) in enumerate((("ap", "AP45"), ("switch", "EX4400"), ("gateway", "SRX320")), 1):
            row = {
                "mac": f"000000000{site_index}{index:02d}",
                "name": f"{model} at site {site_index + 1}",
                "type": family,
                "model": model,
                "version": cls.facts["versions"][model][0],
            }
            rows.append(row)
        return rows

    @classmethod
    def view(cls, cloud_session: Any, org_id: str, site_id: str) -> dict[str, Any]:
        """Use the shipped version builders with controlled inventory."""
        del cloud_session
        if org_id != cls.org_id:
            raise ValueError("The fixture received another organization.")
        devices = cls.devices(site_id)
        versions = cls.facts["versions"]
        selections = option_rules.TypedVersionSelector().select(devices, versions)
        return {
            "targets": option_rules.build_version_options(devices, versions, selections),
            "versions_by_model": {model: list(values) for model, values in versions.items()},
            "type_selections": selections,
            "partial_reasons": [],
        }

    @classmethod
    def read_cloud(cls, name: str, **parameters: Any) -> list[dict[str, Any]]:
        """Answer only the two selection reads that this journey needs."""
        del parameters
        if name == "listOrgSites":
            return [{**site, "org_id": cls.org_id} for site in cls.facts["sites"]]
        if name == "listOrgSiteStats":
            return [
                {"id": site["id"], "num_aps": 1, "num_switches": 1, "num_gateways": 1} for site in cls.facts["sites"]
            ]
        raise ValueError(f"The fixture does not permit the cloud read {name}.")


class FailureLimitCloud:
    """Count and refuse every SDK transport method of the signed stand-in."""

    def __init__(self) -> None:
        """Give the controlled session the required privilege and no transport."""
        self._privileges = [{"scope": "org", "org_id": FailureLimitScope.org_id, "role": "admin"}]
        self._MAX_429_RETRIES = 0
        self.calls = 0

    def mist_get(self, uri: str, **arguments: Any) -> None:
        """Refuse an SDK read instead of contacting a cloud."""
        self.calls += 1
        raise RuntimeError("An SDK read is forbidden in the failure limit journey.")

    def mist_post(self, uri: str, **arguments: Any) -> None:
        """Refuse an SDK write instead of starting firmware work."""
        self.calls += 1
        raise RuntimeError("An SDK write is forbidden in the failure limit journey.")

    def mist_put(self, uri: str, **arguments: Any) -> None:
        """Refuse an SDK update instead of changing cloud state."""
        self.calls += 1
        raise RuntimeError("An SDK update is forbidden in the failure limit journey.")

    def mist_delete(self, uri: str, **arguments: Any) -> None:
        """Refuse an SDK delete instead of changing cloud state."""
        self.calls += 1
        raise RuntimeError("An SDK delete is forbidden in the failure limit journey.")


class FailureLimitPortal:
    """Own the actual application, signed session, plans, and measured boundaries."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Build one isolated portal without a real credential or store."""
        self.run_id = f"issue3326-{uuid4().hex}"
        self.cloud = FailureLimitCloud()
        self.starts = Mock(side_effect=RuntimeError("Firmware work is forbidden in this journey."))
        self.app = self.configure(monkeypatch)
        self.client = self.app.test_client()

    def configure(self, monkeypatch: pytest.MonkeyPatch) -> Flask:
        """Install all isolated dependencies before the actual routes register."""
        for variable in ("MIST_APITOKEN", "MIST_API_TOKEN", "API_TOKEN"):
            monkeypatch.delenv(variable, raising=False)
        monkeypatch.setenv(SECRET_KEY_VARIABLE, secrets.token_hex(32))
        monkeypatch.setenv("CAPTURE_AUTOSTART", "0")
        seams: dict[str, Callable[..., Any]] = dict.fromkeys(FailureLimitScope.facts["actions"], self.starts)
        seams.update(
            options_view=FailureLimitScope.view,
            versions_reader=Mock(return_value=FailureLimitScope.facts["versions"]),
            cloud_reader=FailureLimitScope.read_cloud,
            device_reader=Mock(return_value=[]),
        )
        overrides = build_e2e_overrides(self.run_id, seams)
        built = create_app(overrides)
        service = AggregateUpgradeService()
        monkeypatch.setattr(service, "submit", self.starts)
        built.config.update(
            TESTING=True,
            AGGREGATE_UPGRADE_SERVICE=service,
            ORG_UPGRADE_OPTIONS_VIEW=FailureLimitScope.view,
            ORG_UPGRADE_OPTIONS_BUILDER=self.build,
            MIST_SELF_READER=Mock(return_value={"email": "failure-limit@example.invalid"}),
        )
        return built

    def build(self, cloud_session: Any, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Build the real targets and options at the controlled inventory boundary."""
        del cloud_session
        if org_id != FailureLimitScope.org_id:
            raise ValueError("The fixture received another organization.")
        targets = option_rules.build_targets(FailureLimitScope.devices(site_id), list(body["targets"]))
        return {"targets": targets, "options": asdict(option_rules.build_options(body))}

    def seed(self, strategy: str | None, percentage: int | None = None) -> None:
        """Sign a fresh operator and optionally restore a saved strategy and value."""
        owner = identity.build_owner("failure-limit@example.invalid", identity.issue_browser_id())
        sites = tuple(site["id"] for site in FailureLimitScope.facts["sites"])
        operator = identity.OperatorSession(
            owner=owner,
            cloud_session=self.cloud,
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
            selected_site_ids=sites,
        )
        identity.SESSION_REGISTRY.register(operator)
        self.app.config["FAILURE_LIMIT_OWNER"] = owner
        self.client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
        with self.client.session_transaction() as saved:
            saved.update(
                selected_org_id=FailureLimitScope.org_id,
                selected_upgrade_mode="multi_site",
            )
            saved[identity.SESSION_OWNER_KEY] = owner.key
            if strategy is not None:
                options: dict[str, str | int | list[int]] = {"strategy": strategy, "canary_phases": [1, 10, 50, 100]}
                if percentage is not None:
                    options["max_failure_percentage"] = percentage
                saved[org_upgrade.OPTIONS_SESSION_KEY] = options
                saved[org_upgrade.OPTIONS_ORG_SESSION_KEY] = FailureLimitScope.org_id

    def require_idle(self) -> dict[str, Any]:
        """Report real boundary counts and require every stored record to remain a plan."""
        store = self.app.config["RUN_STORE"]
        plans = store.list_operations(FailureLimitScope.org_id)
        for row in plans:
            record = store.read_run(str(row["operation_id"]))
            assert record["state"] == "planned"
            assert {child["status"] for child in record["children"]} == {"planned"}
            assert record["test_run_id"] == self.run_id
        measured = {
            "run_id": self.run_id,
            "pid": os.getpid(),
            "sdk_calls": self.cloud.calls,
            "start_calls": self.starts.call_count,
            "plan_count": len(plans),
        }
        print("Checked 2 cloud/start boundaries and " + str(len(plans)) + " plan(s): " + json.dumps(measured))
        assert (measured["sdk_calls"], measured["start_calls"]) == (0, 0), "Cloud or firmware calls must remain zero."
        return measured
