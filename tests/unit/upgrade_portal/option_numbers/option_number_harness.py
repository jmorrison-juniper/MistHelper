"""Isolated synthetic records for actual option routes and renderers."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from unittest.mock import Mock

import mistapi
import pytest
from flask.testing import FlaskClient

from src.upgrade_portal.app.factory import create_app
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.upgrade import options
from tests.support.lock_store_double import FakeLockStore
from tests.support.sdk_pages import JSON_TYPE, build_sdk_answer
from tests.support.upgrade_portal_e2e import build_e2e_overrides

ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"
SECOND_SITE = "00000000-0000-0000-0000-0000000000dd"
MAC = "0011223344a1"
VERSION = "0.15.1"
DEVICE = {"mac": MAC, "name": "Synthetic access point", "type": "ap", "model": "AP45", "version": "0.14.1"}


class MemoryPlans:
    """Count every persistent plan write without a production store."""

    def __init__(self) -> None:
        """Create synthetic record storage and a write counter."""
        self.records: dict[str, dict[str, Any]] = {}
        self.writes = 0

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return a detached record so an unsaved edit cannot alter stored state."""
        return deepcopy(self.records.get(run_id))

    def write_run(self, record: dict[str, Any]) -> bool:
        """Record an attempted persistent write."""
        self.writes += 1
        self.records[str(record["run_id"])] = deepcopy(record)
        return True


class RouteHarness:
    """Drive native routes while replacing only cloud and store boundaries."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Build an owned application with synthetic cloud reads and counted writes."""
        monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
        self.store = MemoryPlans()
        self.worker = Mock(side_effect=AssertionError("A refused plan started a worker."))
        self.cloud_write = Mock(side_effect=AssertionError("A refused plan wrote to the cloud."))
        self.firmware = Mock(side_effect=AssertionError("A refused plan submitted firmware."))
        overrides = build_e2e_overrides(
            "issue3388-native-routes",
            {
                "capture_runner": self.worker,
                "run_launcher": self.worker,
                "stop_runner": self.worker,
                "options_builder": options.build_options_record,
                "options_view": options.build_options_view,
                "versions_reader": options.read_model_versions,
                "cloud_reader": self.site_read,
                "device_reader": self.site_read,
            },
        )
        self.app = create_app(overrides)
        self.configure()
        self.install_cloud(monkeypatch)

    def configure(self) -> None:
        """Replace external resource boundaries without replacing the mapper."""
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RUN_STORE=self.store,
            ORG_UPGRADE_WRITES_ENABLED=True,
            RUN_LAUNCHER=self.worker,
            UPGRADE_OPTIONS_BUILDER=None,
            UPGRADE_OPTIONS_VIEW=None,
            UPGRADE_VERSIONS=None,
            LOCK_STORE_CLIENT=FakeLockStore(),
            SITE_LOCK_READER=lambda org, sites: dict.fromkeys(sites),
            MIST_READER=self.site_read,
        )

    def install_cloud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Supply SDK responses and fail if a firmware endpoint receives a call."""
        monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", self.inventory)
        monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteAvailableDeviceVersions", self.versions)
        monkeypatch.setattr(mistapi.api.v1.sites.devices, "upgradeSiteDevices", self.cloud_write)
        monkeypatch.setattr(mistapi.api.v1.sites.devices, "upgradeDevice", self.firmware)
        monkeypatch.setattr(mistapi.api.v1.orgs.devices, "upgradeOrgDevices", self.cloud_write)

    @staticmethod
    def fail_inventory(monkeypatch: pytest.MonkeyPatch, answer: Any) -> None:
        """Supply a failed transport answer at the existing SDK boundary."""
        monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", lambda *args, **kwargs: answer)

    @staticmethod
    def inventory(session: Any, org_id: str, **parameters: Any) -> Any:
        """Return one actual SDK answer containing only a synthetic device."""
        return build_sdk_answer(200, json.dumps([DEVICE]).encode(), JSON_TYPE, "https://api.example.invalid/inventory")

    @staticmethod
    def versions(session: Any, site_id: str, **parameters: Any) -> Any:
        """Return an offered version through the real firmware version reader."""
        return build_sdk_answer(
            200, b'[{"model":"AP45","version":"0.15.1"}]', JSON_TYPE, "https://api.example.invalid/versions"
        )

    @staticmethod
    def site_read(name: str, **parameters: Any) -> list[dict[str, str]]:
        """Return the selected synthetic sites without an external read."""
        rows = [
            {"id": SITE_ID, "name": "Synthetic site", "org_id": ORG_ID},
            {"id": SECOND_SITE, "name": "Second synthetic site", "org_id": ORG_ID},
        ]
        return rows if name == "listOrgSites" else []

    def sign_in(self, client: FlaskClient, mode: str) -> identity.SessionOwner:
        """Register one isolated owner and select its synthetic sites."""
        owner = identity.build_owner("option-numbers@example.invalid", identity.issue_browser_id())
        identity.SESSION_REGISTRY.register(
            identity.OperatorSession(
                owner=owner,
                cloud_session=object(),
                credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
                selected_site_ids=(SITE_ID, SECOND_SITE),
            )
        )
        client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
        with client.session_transaction() as session:
            session.update(
                {
                    identity.SESSION_OWNER_KEY: owner.key,
                    "selected_org_id": ORG_ID,
                    "selected_site_id": SITE_ID,
                    "selected_upgrade_mode": mode,
                }
            )
        return owner

    @staticmethod
    def payload(field: str, value: str) -> dict[str, Any]:
        """Build an actual browser request with one invalid numeric choice."""
        body: dict[str, Any] = {
            "selected_types": ["ap"],
            "targets": [{"mac": MAC, "version_target": VERSION}],
            "version_ap": VERSION,
            "strategy": "canary",
            "canary_phases": "100",
        }
        if field.startswith("rrm_"):
            body.update(strategy="rrm", canary_phases="")
        body[field] = value
        return body

    def assert_no_actions(self) -> None:
        """Measure each forbidden effect instead of inferring it from status."""
        assert self.store.writes == 0
        self.worker.assert_not_called()
        self.cloud_write.assert_not_called()
        self.firmware.assert_not_called()
