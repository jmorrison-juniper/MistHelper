"""Prove rejected counts through owned durable records and the shipped status routes."""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from copy import deepcopy
from html import unescape
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
import requests
from flask.testing import FlaskClient

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app import wiring
from src.upgrade_portal.app.factory import create_app
from src.upgrade_portal.app.routes import org_upgrade
from src.upgrade_portal.runtime import identity
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck, build_child_environment, build_e2e_overrides
from tests.unit.upgrade_portal.test_issue_3329_rejected_child_counts import MACS, CountSeeds
from tests.unit.upgrade_portal.test_org_child_controls import ORG_ID, SITE_ONE, SITE_TWO


class CountPortal:
    """Own every record, external seam, and signed operator of one read-only proof."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, test_run_id: str | None = None) -> None:
        """Construct isolated records before the production factory registers its routes."""
        self.test_run_id = test_run_id or f"e2e-issue3329-{uuid4().hex}"
        names = ("cloud", "startup", "job", "plan", "start", "cancel", "retry")
        self.callbacks = {name: Mock(side_effect=AssertionError(f"The count proof called {name}.")) for name in names}
        scrubbed = build_child_environment(os.environ)
        for name in tuple(os.environ):
            if name not in scrubbed:
                monkeypatch.delenv(name)
        for name in ("ARANGO_HOST", "REDIS_HOST", "REDIS_PORT", "CAPTURE_AUTOSTART", "MISTHELPER_STANDALONE"):
            monkeypatch.setenv(name, "true" if name == "MISTHELPER_STANDALONE" else scrubbed[name])
        monkeypatch.setattr(requests.Session, "request", self.callbacks["cloud"])
        monkeypatch.setattr(wiring, "prepare_storage", self.callbacks["startup"])
        monkeypatch.setattr(wiring, "start_upgrade_run", self.callbacks["job"])
        self.aggregate = Mock(spec=AggregateUpgradeService)
        self.aggregate.status.side_effect = lambda cloud_session, record, store: record
        self.owner = identity.build_owner("count.operator@example.invalid", identity.issue_browser_id())
        self.app, self.store = self._application()
        operator = identity.OperatorSession(
            owner=self.owner,
            cloud_session=SimpleNamespace(),
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
            selected_site_ids=(SITE_ONE, SITE_TWO),
        )
        identity.SESSION_REGISTRY.register(operator)

    def _application(self) -> tuple[Any, Any]:
        """Install complete test dependencies and count actual mutation-route callbacks."""
        seams = {
            "capture_runner": self.callbacks["job"],
            "run_launcher": self.callbacks["start"],
            "stop_runner": self.callbacks["cancel"],
            "options_builder": self.callbacks["plan"],
            "options_view": self.callbacks["plan"],
            "versions_reader": self.callbacks["cloud"],
            "cloud_reader": self.callbacks["cloud"],
            "device_reader": self.callbacks["cloud"],
        }
        built = create_app(build_e2e_overrides(self.test_run_id, seams))
        built.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        built.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY] = self.aggregate
        built.config[org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY] = self.callbacks["cloud"]
        CascadeSeamStandIn().install(built.config)
        self.mutations = {
            rule.endpoint: Mock(wraps=built.view_functions[rule.endpoint])
            for rule in built.url_map.iter_rules()
            if set(rule.methods or ()) & {"POST", "PUT", "PATCH", "DELETE"}
        }
        built.view_functions.update(self.mutations)
        return built, built.config["RUN_STORE"]

    def client(self, operation: dict[str, Any]) -> FlaskClient:
        """Seed one owned durable operation and sign its existing browser context."""
        stored = deepcopy(operation)
        stored["owner"] = self.owner.key
        assert self.store.write_run(stored) is True
        assert self.store.read_run(stored["run_id"])["test_run_id"] == self.test_run_id
        client = self.app.test_client()
        client.set_cookie(identity.BROWSER_ID_COOKIE, self.owner.browser_id)
        with client.session_transaction() as session:
            session[identity.SESSION_OWNER_KEY] = self.owner.key
            session["selected_org_id"] = ORG_ID
            session["selected_upgrade_mode"] = "multi_site"
        return client

    def require_quiet(self) -> None:
        """Check every counted external and mutation callback, not a fixed safety header."""
        assert {name: callback.call_count for name, callback in self.callbacks.items()} == dict.fromkeys(
            self.callbacks, 0
        )
        assert sum(callback.call_count for callback in self.mutations.values()) == 0
        for name in ("build", "submit", "cancel", "reschedule", "reconcile", "record_device_versions"):
            assert getattr(self.aggregate, name).call_count == 0, f"The count proof called aggregate {name}."
        print(f"Checked {len(self.callbacks)} forbidden seams and {len(self.mutations)} mutation callbacks. Calls: 0.")

    def close(self) -> None:
        """Drop only the operator owned by this isolated proof."""
        identity.SESSION_REGISTRY.drop(self.owner.key)


class RenderedCounts:
    """Read the actual shipped table and count fields without changing the template."""

    CELL_FIELDS = (
        "site_name",
        "device_family",
        "status",
        "total",
        "upgraded",
        "failed",
        "id",
        "error",
        "cancellation_text",
    )

    @staticmethod
    def require(page: str, summary: dict[str, Any]) -> None:
        """Check every summary count and all nine cells of each child row."""
        for field in ("total", "upgraded_count", "failed_count"):
            match = re.search(rf'data-org-upgrade-field="{field}">([^<]*)<', page)
            assert match is not None and match.group(1) == str(summary[field]), f"The page lost {field}."
        table = re.search(r"<tbody data-org-upgrade-sites>(.*?)</tbody>", page, re.DOTALL)
        assert table is not None and "data-org-upgrade-sites" in table.group(0)
        rows = re.findall(r"<tr>(.*?)</tr>", table.group(1), re.DOTALL)
        assert len(rows) == len(summary["children"])
        for markup, expected in zip(rows, summary["children"], strict=True):
            cells = [
                unescape(re.sub(r"<[^>]*>", "", cell)).strip()
                for cell in re.findall(r"<(?:th|td)\b[^>]*>(.*?)</(?:th|td)>", markup, re.DOTALL)
            ]
            assert cells == [
                str(expected[name] or "") if name not in ("total", "upgraded", "failed") else str(expected[name])
                for name in RenderedCounts.CELL_FIELDS
            ]
        print(f"Checked 3 rendered count fields and {len(rows)} rendered child rows.")


@pytest.fixture
def count_portal(monkeypatch: pytest.MonkeyPatch) -> Iterator[CountPortal]:
    """Retain strict seams and release the owned operator even when a proof fails."""
    portal = CountPortal(monkeypatch)
    try:
        yield portal
    finally:
        portal.close()
        portal.require_quiet()


class TestRejectedCountRoutes:
    """Drive actual GET routes without a submission, a firmware callback, or a cloud read."""

    @pytest.mark.parametrize(
        ("status", "count"), [("rejected", 1), ("not_submitted", 2), ("rejected", 0), ("not_submitted", 0)]
    )
    def test_known_failed_targets_match_the_rendered_page(
        self, count_portal: CountPortal, status: str, count: int
    ) -> None:
        """The status response and initial page expose the same known target failures."""
        operation = CountSeeds.operation([CountSeeds.child(status, count)])
        client = count_portal.client(operation)
        response = client.get(f"/api/org-upgrades/{operation['operation_id']}")
        assert response.status_code == 200
        summary = response.get_json()
        CountSeeds.require_counts(summary, [(count, 0, count)])
        assert summary["status"] == "failed"
        assert summary["children"][0]["status"] == status
        assert summary["children"][0]["error"] == operation["children"][0]["error"]
        page = client.get(f"/upgrade/org/jobs/{operation['operation_id']}")
        assert page.status_code == 200
        RunOwnerHeaderCheck(count_portal.test_run_id).require(page.headers)
        RenderedCounts.require(page.get_data(as_text=True), summary)
        assert count_portal.store.read_run(operation["operation_id"])["children"] == operation["children"]

    def test_mixed_children_keep_counts_order_and_cancellation_text(self, count_portal: CountPortal) -> None:
        """Three child families contribute once and retain their exact reason and cancellation text."""
        operation = CountSeeds.mixed()
        client = count_portal.client(operation)
        response = client.get(f"/api/org-upgrades/{operation['operation_id']}")
        assert response.status_code == 200
        summary = response.get_json()
        CountSeeds.require_counts(summary, [(2, 2, 0), (1, 0, 1), (2, 0, 2)])
        assert [row["status"] for row in summary["children"]] == ["completed", "rejected", "not_submitted"]
        assert [row["mac"] for row in summary["devices"]] == list(MACS[:5])
        assert "The cloud created no child job." in summary["children"][1]["cancellation_text"]
        page = client.get(f"/upgrade/org/jobs/{operation['operation_id']}")
        assert page.status_code == 200
        RenderedCounts.require(page.get_data(as_text=True), summary)
        assert count_portal.store.read_run(operation["operation_id"])["children"] == operation["children"]

    @pytest.mark.parametrize(
        "status",
        [
            "unknown",
            "submission_unknown",
            "read_unknown",
            "planned",
            "submission_claimed",
            "accepted",
            "running",
            "cancelled",
        ],
    )
    def test_uncertain_or_active_jobs_keep_zero_inferred_failures(self, count_portal: CountPortal, status: str) -> None:
        """The real status route preserves uncertain, waiting, active, and cancellation outcomes."""
        operation = CountSeeds.operation([CountSeeds.child(status, 1)], "attention_required")
        client = count_portal.client(operation)
        response = client.get(f"/api/org-upgrades/{operation['operation_id']}")
        assert response.status_code == 200
        summary = response.get_json()
        CountSeeds.require_counts(summary, [(1, 0, 0)])
        assert summary["status"] == "attention_required"
        assert summary["children"][0]["status"] == status
        page = client.get(f"/upgrade/org/jobs/{operation['operation_id']}")
        assert page.status_code == 200
        RenderedCounts.require(page.get_data(as_text=True), summary)

    @pytest.mark.parametrize("raw_status", [None, 200, 503])
    def test_legacy_rejected_words_do_not_fail_uncertain_targets(
        self, count_portal: CountPortal, raw_status: int | None
    ) -> None:
        """A malformed success or server error remains unknown despite its legacy rejected status."""
        row = CountSeeds.child("rejected", 1)
        row["raw_status"] = raw_status
        row["error"] = (
            f"The cloud answered status {raw_status}."
            if raw_status is not None
            else "The submission response has no HTTP status."
        )
        operation = CountSeeds.operation([row], "attention_required")
        client = count_portal.client(operation)
        response = client.get(f"/api/org-upgrades/{operation['operation_id']}")
        assert response.status_code == 200
        summary = response.get_json()
        CountSeeds.require_counts(summary, [(1, 0, 0)])
        assert summary["children"][0]["status"] == "rejected"

    def test_completed_proof_and_native_nested_ap_counts_survive(self, count_portal: CountPortal) -> None:
        """The response retains native nested failures and proof counts beside known no-submission targets."""
        nested = CountSeeds.child("running", 3, "ap")
        nested["status_data"] = {
            "upgrades": [
                {"site_id": SITE_ONE, "upgrade": {"targets": {"upgraded": list(MACS[:2]), "failed": [MACS[2]]}}}
            ]
        }
        proven = CountSeeds.child("completed", 2, "switch", 3)
        proven["reconciliation"] = {"proven": True}
        refused = CountSeeds.child("not_submitted", 1, "gateway", 5)
        operation = CountSeeds.operation([nested, proven, refused], "running")
        client = count_portal.client(operation)
        response = client.get(f"/api/org-upgrades/{operation['operation_id']}")
        assert response.status_code == 200
        summary = response.get_json()
        CountSeeds.require_counts(summary, [(3, 2, 1), (2, 2, 0), (1, 0, 1)])
        assert summary["children"][0]["status"] == "running"
        page = client.get(f"/upgrade/org/jobs/{operation['operation_id']}")
        assert page.status_code == 200
        RenderedCounts.require(page.get_data(as_text=True), summary)
