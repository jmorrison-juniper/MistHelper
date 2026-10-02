"""Own one native fixture identity and private capture scenarios for issue #3375."""

from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, ClassVar, NoReturn, Protocol, runtime_checkable
from uuid import uuid4

import pytest
from flask import Flask

from src.upgrade_portal.api.run_controls import E2EFactoryOverrides
from src.upgrade_portal.app.config import SECRET_KEY_VARIABLE
from src.upgrade_portal.app.factory import create_app
from src.upgrade_portal.app.routes import org_upgrade
from src.upgrade_portal.capture import assembly
from src.upgrade_portal.capture.clients import ClientAttachment, ClientIdentity, ClientRecord
from src.upgrade_portal.capture.store import CAPTURE_STATE_FIELD, CaptureState
from src.upgrade_portal.runtime import identity
from tests.support.upgrade_portal_e2e import build_e2e_overrides
from tests.support.upgrade_portal_e2e.records import PortalRecordStore

logger = logging.getLogger(__name__)


class NativeCaptureFixture:
    """Read the single actual fixture identity without a second module load."""

    @runtime_checkable
    class Contract(Protocol):
        """Describe the native callables without a dynamic module cast."""

        def stand_in_capture_index(self) -> dict[str, dict[str, Any]]:
            """Build the five actual global seed documents."""

        stand_in_capture: Callable[[str, str, str, str, str], dict[str, Any]]

        def stand_in_capture_runner(self, job: dict[str, Any]) -> None:
            """Execute the actual native capture runner."""

        def _build_factory_overrides(self) -> E2EFactoryOverrides:
            """Build the actual complete process-owned dependency set."""

        def stand_in_running_versions(self, cloud_session: object, site_id: str) -> dict[str, Any]:
            """Read the actual native running-version metadata."""

    @staticmethod
    def candidates(configuration: pytest.Config) -> list[ModuleType]:
        """Find loaded native modules at the exact repository fixture path."""
        path = Path(__file__).resolve().parents[2] / "e2e" / "upgrade_portal" / "conftest.py"
        plugins = configuration.pluginmanager.get_plugins()
        loaded = [
            module
            for module in (*plugins, *tuple(sys.modules.values()))
            if isinstance(module, ModuleType) and Path(getattr(module, "__file__", "") or "").resolve() == path
        ]
        return list(dict.fromkeys(loaded))

    @classmethod
    def read(cls, configuration: pytest.Config) -> Contract:
        """Require one typed native identity and fail on duplicate identities."""
        logger.info("Read the native capture fixture identity")
        candidates = cls.candidates(configuration)
        if not candidates:
            importlib.import_module("tests.e2e.upgrade_portal.conftest")  # Load the canonical identity only once.
            candidates = cls.candidates(configuration)
        count = len(candidates)
        if count != 1:
            raise AssertionError(f"Checked fixture modules={count}. Expected one native identity.")
        native = candidates[0]
        if not isinstance(native, cls.Contract):
            raise AssertionError("Checked fixture modules=1. The native capture contract is unreadable.")
        logger.debug("Checked native fixture modules=1 typed contracts=1")
        return native


class PrivateScenarioReads:
    """Keep every private scenario read and forbidden action inside one process."""

    def __init__(self, base: E2EFactoryOverrides, sites: tuple[dict[str, str], ...]) -> None:
        """Retain native builders and two private site rows."""
        self.base = base
        self.sites = sites
        self.actions: list[str] = []
        self.cloud_calls: list[str] = []

    def cloud_reader(self, name: str, **parameters: Any) -> Any:
        """Expose only the private sites while retaining native non-site reads."""
        logger.info("Read private scenario cloud rows for %s", name)
        self.cloud_calls.append(name)
        result = (
            deepcopy(list(self.sites))
            if name == "listOrgSites"
            else self.base.external.cloud_reader(name, **parameters)
        )
        logger.debug("Checked private scenario cloud reads=%d", len(self.cloud_calls))
        return result

    def options_builder(self, cloud_session: object, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Use the actual native options builder without an SDK inventory read."""
        del cloud_session, org_id
        logger.info("Build private scenario options for one site")
        result: dict[str, Any] = self.base.actions.options_builder({"site_id": site_id}, body)
        logger.debug("Built private scenario target rows=%d", len(result["targets"]))
        return result

    def reject_action(self, action: str, *arguments: object, **parameters: object) -> NoReturn:
        """Fail instead of running an upgrade, stop, or capture callback."""
        del arguments, parameters
        self.actions.append(action)
        logger.error("Checked private scenario forbidden callbacks=%d action=%s", len(self.actions), action)
        raise AssertionError(f"Private scenario reached forbidden callback {action!r}.")

    @staticmethod
    def unmatched_client(device_index: dict[str, dict[str, Any]], client_mac: str) -> dict[str, Any]:
        """Build one genuinely unmatched client through the native name join."""
        record = ClientRecord(
            client_mac,
            ClientIdentity(hostname="Private unmatched client"),
            ClientAttachment(device_mac="001122334455"),
        )
        rows = assembly.fill_device_names([record], device_index)
        return rows[0]


class PrivateScenarioSession:
    """Own one signed operator and its private Flask client."""

    def __init__(self, app: Flask, site_ids: tuple[str, ...], org_id: str) -> None:
        """Register only this scenario's fake operator."""
        self.owner = identity.build_owner("e2e.3375.operator@example.invalid", identity.issue_browser_id())
        operator = identity.OperatorSession(
            self.owner, object(), identity.CredentialMode.ENVIRONMENT_TOKEN, selected_site_ids=site_ids
        )
        identity.SESSION_REGISTRY.register(operator)
        self.client = app.test_client()
        self.client.set_cookie(identity.BROWSER_ID_COOKIE, self.owner.browser_id)
        with self.client.session_transaction() as session:
            session[identity.SESSION_OWNER_KEY] = self.owner.key
            session["selected_org_id"] = org_id
            session["selected_upgrade_mode"] = "multi_site"

    def save_plan(self) -> None:
        """Save the actual native plan through the current Flask options route."""
        logger.info("Save one private multi-site options plan")
        body = {
            "selected_types": ["ap", "gateway", "switch"],
            "targets": [{"mac": f"00000000000{number}", "version_target": "0.15.1"} for number in range(1, 4)],
            "strategy": "big_bang",
        }
        response = self.client.post("/api/org-upgrades/options", json=body)
        if response.status_code != 200:
            raise AssertionError(f"Private options save returned HTTP {response.status_code}: {response.get_json()!r}")
        logger.debug("Saved private options plan HTTP=200 site rows=2")

    def close(self) -> None:
        """Remove only this scenario's operator record."""
        logger.info("Remove the private scenario operator")
        removed = identity.SESSION_REGISTRY.drop(self.owner.key)
        if not removed:
            raise AssertionError("Checked private operator records=1. Its owned record disappeared before cleanup.")
        logger.debug("Removed private operator records=1")


class PrivateCaptureScenario:
    """Build private records and the actual Flask application without shared seed mutation."""

    class Identifiers:
        """Name only this scenario's private sites, captures, and unmatched client."""

        SITE_ID: ClassVar[str] = "33750000-0000-0000-0000-000000000001"
        PENDING_SITE_ID: ClassVar[str] = "33750000-0000-0000-0000-000000000002"
        CAPTURE_ID: ClassVar[str] = "e2e-3375-private-partial"
        PENDING_CAPTURE_ID: ClassVar[str] = "e2e-3375-private-pending"
        UNMATCHED_CLIENT_MAC: ClassVar[str] = "aabbcc337599"

    def __init__(self, native: NativeCaptureFixture.Contract, patcher: pytest.MonkeyPatch) -> None:
        """Create fresh scenario stores and retain every accepted global seed."""
        identifiers = self.Identifiers
        base = native._build_factory_overrides()
        captures = native.stand_in_capture_index()
        self.original = deepcopy(captures)
        private, pending = self.private_captures(captures)
        sites = (
            {"id": identifiers.SITE_ID, "name": "Private partial site", "org_id": private["org_id"]},
            {"id": identifiers.PENDING_SITE_ID, "name": "Private pending site", "org_id": private["org_id"]},
        )
        self.reads = PrivateScenarioReads(base, sites)
        seams = self.seams(base, [*captures.values(), private, pending])
        self.overrides = build_e2e_overrides(f"e2e-3375-{uuid4().hex}", seams)
        self.app = self.application(patcher, native)
        records = self.app.config["CAPTURE_STORE"]
        if not isinstance(records, PortalRecordStore):
            raise TypeError("The private scenario must use the process-owned PortalRecordStore.")
        self.records = records
        self.session = PrivateScenarioSession(
            self.app, (identifiers.SITE_ID, identifiers.PENDING_SITE_ID), str(private["org_id"])
        )

    @classmethod
    def private_captures(cls, captures: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Derive private partial and pending records from the actual native documents."""
        identifiers = cls.Identifiers
        logger.info("Build private partial and pending captures from native seeds")
        private = deepcopy(captures["e2e-capture-tier3-0001"])
        private.update(
            capture_id=identifiers.CAPTURE_ID, run_id="", site_id=identifiers.SITE_ID, site_name="Private partial site"
        )
        private["clients"]["wireless"].append(
            PrivateScenarioReads.unmatched_client(private["device_index"], identifiers.UNMATCHED_CLIENT_MAC)
        )
        sections = assembly.CaptureSections(
            device_index=private["device_index"], devices=private["devices"], clients=private["clients"]
        )
        private["counts"] = assembly.build_counts(sections)
        private["capture_status"] = assembly.resolve_status(sections, private["partial_reasons"])
        pending = deepcopy(captures["e2e-capture-pre-0001"]) | {
            "capture_id": identifiers.PENDING_CAPTURE_ID,
            "run_id": "",
            "site_id": identifiers.PENDING_SITE_ID,
            "site_name": "Private pending site",
            CAPTURE_STATE_FIELD: CaptureState.PENDING.value,
        }
        logger.debug("Built private documents=2 unmatched client rows=1 native count fields=18")
        return private, pending

    def seams(self, base: E2EFactoryOverrides, captures: list[dict[str, Any]]) -> dict[str, Any]:
        """Assemble complete process-owned seams without a production fallback."""
        from functools import partial

        return {
            "captures": captures,
            "capture_runner": partial(self.reads.reject_action, "capture"),
            "run_launcher": partial(self.reads.reject_action, "upgrade"),
            "stop_runner": partial(self.reads.reject_action, "cancel"),
            "options_builder": base.actions.options_builder,
            "options_view": base.actions.options_view,
            "versions_reader": base.actions.versions_reader,
            "cloud_reader": self.reads.cloud_reader,
            "device_reader": base.external.device_reader,
        }

    def application(self, patcher: pytest.MonkeyPatch, native: NativeCaptureFixture.Contract) -> Flask:
        """Build the current shipped application with explicit test-only dependencies."""
        logger.info("Build the private scenario Flask application")
        patcher.setenv(SECRET_KEY_VARIABLE, "e2e-3375-cookie-signing-only")
        app = create_app(self.overrides)
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        app.config[org_upgrade.OPTIONS_VIEW_CONFIG_KEY] = self.overrides.actions.options_view
        app.config[org_upgrade.OPTIONS_BUILDER_CONFIG_KEY] = self.reads.options_builder
        app.config[org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY] = native.stand_in_running_versions
        logger.debug("Built private Flask applications=1 process-owned override groups=4")
        return app
