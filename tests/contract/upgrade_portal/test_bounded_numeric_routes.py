"""Prove issue #3395 through real picker and capture HTTP requests."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask, Response, jsonify

from src.interfaces.portals.upgrade_portal.app.routes import capture
from src.interfaces.portals.upgrade_portal.runtime import identity
from tests.contract.upgrade_portal.conftest import FakeMistApi

INVALID_TEXT = [
    pytest.param("\u00b2", id="superscript"),
    pytest.param("\u0662", id="arabic-decimal"),
    pytest.param("\uff12", id="fullwidth-decimal"),
    pytest.param("1\u0662", id="mixed-digits"),
    pytest.param("9" * 5000, id="5000-nines"),
    pytest.param("0" * 5000, id="5000-zeros"),
    pytest.param("0" * 5000 + "2", id="5000-leading-zeros"),
    pytest.param("", id="empty"),
    pytest.param("word", id="word"),
    pytest.param("-2", id="minus"),
    pytest.param("++2", id="repeated-plus"),
    pytest.param("2.0", id="fraction"),
    pytest.param("2_0", id="separator"),
]


class NumericRouteProbe:
    """Record work boundaries while the real request readers remain active."""

    def __init__(self, application: Flask, api: FakeMistApi, org_id: str) -> None:
        """Bind offline reads and work recorders to one signed-in client."""
        application.config.update(WTF_CSRF_ENABLED=False, PROPAGATE_EXCEPTIONS=False)
        application.config["MIST_READER"] = api.read
        self.client = application.test_client()
        self.starts: list[tuple[str, str, int, dict[str, Any]]] = []
        self.worker = Mock(name="capture_worker")
        self.firmware = Mock(name="firmware_launcher")
        application.config["RUN_LAUNCHER"] = self.firmware
        self.owner = identity.build_owner("numeric.operator@example.invalid", identity.issue_browser_id())
        self.sign_in(org_id)

    def sign_in(self, org_id: str) -> None:
        """Use the real session guard with a known organization privilege list."""
        privileges = [
            {"scope": "org", "org_id": org_id if index == 0 else f"org-{index:03d}", "name": f"Group {index:03d}"}
            for index in range(60)
        ]
        record = identity.OperatorSession(
            owner=self.owner,
            cloud_session=SimpleNamespace(privileges=privileges),
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        )
        identity.SESSION_REGISTRY.register(record)
        self.client.set_cookie(identity.BROWSER_ID_COOKIE, self.owner.browser_id)
        with self.client.session_transaction() as browser:
            browser[identity.SESSION_OWNER_KEY] = self.owner.key
            browser["selected_org_id"] = org_id

    def launch(self, site: dict[str, Any], org_id: str, tier: int, body: dict[str, Any]) -> tuple[Response, int]:
        """Record the accepted job without a thread, store, or cloud call."""
        self.starts.append((str(site["id"]), org_id, tier, dict(body)))
        return jsonify({"capture_id": "cap-numeric-probe", "status_url": "/api/captures/cap-numeric-probe/status"}), 202

    def close(self) -> None:
        """Remove the session so no later test inherits this operator."""
        identity.SESSION_REGISTRY.drop(self.owner.key)


@pytest.fixture
def numeric_routes(
    portal_app: Flask, fake_mist_api: FakeMistApi, fake_org_id: str, monkeypatch: pytest.MonkeyPatch
) -> Iterator[NumericRouteProbe]:
    """Keep real routes and input readers while replacing only work boundaries."""
    probe = NumericRouteProbe(portal_app, fake_mist_api, fake_org_id)
    monkeypatch.setattr(capture, "launch_capture", probe.launch)
    monkeypatch.setattr(capture, "start_worker", probe.worker)
    try:
        yield probe
    finally:
        probe.close()


class TestPickerNumericRoutes:
    """Check the exact first page and the existing valid page decisions."""

    @pytest.mark.parametrize("raw", INVALID_TEXT)
    def test_damaged_link_opens_first_filtered_page(
        self, numeric_routes: NumericRouteProbe, fake_org_id: str, raw: str
    ) -> None:
        """A damaged link must show the first rows, not a success-shaped empty page."""
        response = numeric_routes.client.get("/select/org", query_string={"offset": raw, "q": "Group"})
        assert response.status_code == 200
        text = response.get_data(as_text=True)
        rows = re.findall(r'data-testid="org-row-([^"]+)"', text)
        assert rows == [fake_org_id, *(f"org-{index:03d}" for index in range(1, 25))]
        assert "This page starts after 0 organizations" in " ".join(text.split())
        assert 'value="Group"' in text
        assert "offset=25&amp;q=Group" in text
        assert numeric_routes.starts == []
        assert numeric_routes.worker.call_count == 0
        assert numeric_routes.firmware.call_count == 0

    @pytest.mark.parametrize(
        ("raw", "offset", "expected_rows"),
        [
            ("0", 0, 25),
            ("25", 25, 25),
            ("0025", 25, 25),
            ("+25", 25, 25),
            (" \t+0025\n", 25, 25),
            ("50", 50, 10),
            ("60", 60, 0),
            ("61", 60, 0),
            (str(sys.maxsize), 60, 0),
            (str(sys.maxsize + 1), 0, 25),
        ],
    )
    def test_valid_page_and_sequence_bound(
        self, numeric_routes: NumericRouteProbe, raw: str, offset: int, expected_rows: int
    ) -> None:
        """Valid offsets still clamp to the final row count after filtering."""
        response = numeric_routes.client.get("/select/org", query_string={"offset": raw, "q": "Group"})
        assert response.status_code == 200
        text = response.get_data(as_text=True)
        rows = re.findall(r'data-testid="org-row-([^"]+)"', text)
        assert len(rows) == expected_rows
        assert f"This page starts after {offset} organizations" in " ".join(text.split())
        if offset == 25:
            assert rows == [f"org-{index:03d}" for index in range(25, 50)]
        assert numeric_routes.starts == []
        assert numeric_routes.firmware.call_count == 0


class TestCaptureNumericRoutes:
    """Keep explicit tier refusal before any capture or firmware work."""

    @pytest.mark.parametrize("raw", INVALID_TEXT)
    @pytest.mark.parametrize("transport", ["json", "form"])
    def test_damaged_tier_has_exact_refusal(
        self, numeric_routes: NumericRouteProbe, fake_site_id: str, raw: str, transport: str
    ) -> None:
        """Both real body readers must refuse invalid tiers without a callback."""
        parameters = {"json": {"tier": raw}} if transport == "json" else {"data": {"tier": raw}}
        response = numeric_routes.client.post(f"/api/sites/{fake_site_id}/captures", **parameters)
        assert response.status_code == 400
        assert response.get_json() == {
            "error": {"code": "bad_tier", "message": "Choose the data tier 2 or the data tier 3."}
        }
        assert numeric_routes.starts == []
        assert numeric_routes.worker.call_count == 0
        assert numeric_routes.firmware.call_count == 0

    @pytest.mark.parametrize("case", [(2, 2), (3, 3), ("2", 2), ("3", 3), ("002", 2), ("003", 3)])
    @pytest.mark.parametrize("transport", ["json", "form"])
    def test_valid_tier_reaches_only_capture_boundary(
        self, numeric_routes: NumericRouteProbe, fake_site_id: str, case: tuple[object, int], transport: str
    ) -> None:
        """Valid JSON and form tiers keep the exact accepted response shape."""
        raw, expected = case
        parameters = {"json": {"tier": raw}} if transport == "json" else {"data": {"tier": raw}}
        response = numeric_routes.client.post(f"/api/sites/{fake_site_id}/captures", **parameters)
        assert response.status_code == 202
        assert response.get_json() == {
            "capture_id": "cap-numeric-probe",
            "status_url": "/api/captures/cap-numeric-probe/status",
        }
        assert numeric_routes.starts == [
            (
                fake_site_id,
                "00000000-0000-0000-0000-0000000000aa",
                expected,
                {"tier": raw if transport == "json" else str(raw)},
            )
        ]
        assert numeric_routes.worker.call_count == 0
        assert numeric_routes.firmware.call_count == 0

    def test_absent_tier_keeps_default(self, numeric_routes: NumericRouteProbe, fake_site_id: str) -> None:
        """An absent field still selects tier 2 through the real body reader."""
        response = numeric_routes.client.post(f"/api/sites/{fake_site_id}/captures", json={})
        assert response.status_code == 202
        assert numeric_routes.starts == [(fake_site_id, "00000000-0000-0000-0000-0000000000aa", 2, {})]
        assert numeric_routes.worker.call_count == 0
        assert numeric_routes.firmware.call_count == 0

    def test_authentication_precedes_tier(self, numeric_routes: NumericRouteProbe, fake_site_id: str) -> None:
        """A damaged tier cannot bypass the real signed-in session guard."""
        with numeric_routes.client.session_transaction() as browser:
            browser.clear()
        response = numeric_routes.client.post(f"/api/sites/{fake_site_id}/captures", json={"tier": "9" * 5000})
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "not_authenticated"
        assert numeric_routes.starts == []
        assert numeric_routes.worker.call_count == 0
        assert numeric_routes.firmware.call_count == 0

    def test_site_scope_precedes_tier(self, numeric_routes: NumericRouteProbe) -> None:
        """A damaged tier cannot disclose a site outside the chosen organization."""
        response = numeric_routes.client.post("/api/sites/site-outside-scope/captures", json={"tier": "9" * 5000})
        assert response.status_code == 404
        assert response.get_json() == {
            "error": {"code": "site_not_found", "message": "The portal found no such site in this organization."}
        }
        assert numeric_routes.starts == []
        assert numeric_routes.worker.call_count == 0
        assert numeric_routes.firmware.call_count == 0
