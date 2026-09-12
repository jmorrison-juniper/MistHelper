"""Verify the HTTP contract for authoritative bulk previews."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.runtime import identity

ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_A = "00000000-0000-0000-0000-0000000000bb"
SITE_B = "00000000-0000-0000-0000-0000000000cc"
PATH = "/api/runs/bulk-actions/preview"
PROBE_EMAIL = "bulk-preview.operator@example.invalid"


class PreviewRunStore:
    """Hold the run records that one contract test can preview."""

    def __init__(self) -> None:
        self.runs = {
            "run-a": {"run_id": "run-a", "org_id": ORG_ID, "site_id": SITE_A},
            "run-b": {"run_id": "run-b", "org_id": ORG_ID, "site_id": SITE_B},
            "run-hidden": {"run_id": "run-hidden", "org_id": "other-org", "site_id": "other-site"},
        }

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        record = self.runs.get(run_id)
        return None if record is None else dict(record)


@pytest.fixture
def preview_client(portal_app: Flask) -> Iterator[FlaskClient]:
    """Return a signed-in client with an isolated run store."""
    portal_app.config["WTF_CSRF_ENABLED"] = False
    portal_app.config["RUN_STORE"] = PreviewRunStore()
    portal_app.config.pop("RUN_CONTROL_PREVIEW_SERVICE", None)
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    identity.SESSION_REGISTRY.register(
        identity.OperatorSession(
            owner=owner,
            cloud_session=object(),
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        )
    )
    try:
        with portal_app.test_client() as client:
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
            with client.session_transaction() as browser_session:
                browser_session[identity.SESSION_OWNER_KEY] = owner.key
                browser_session["selected_org_id"] = ORG_ID
            yield client
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)


def _body(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "action": "cancel",
        "organization_id": ORG_ID,
        "history_scope": "all-sites",
        "run_ids": ["run-a", "run-hidden", "missing", "run-b"],
    }
    body.update(changes)
    return body


def _code(response: Any) -> str:
    return str(response.get_json()["error"]["code"])


def test_preview_returns_authoritative_selection_counts_phrase_and_token(preview_client: FlaskClient) -> None:
    response = preview_client.post(PATH, json=_body())

    assert response.status_code == 200
    body = response.get_json()
    assert body["action"] == "cancel"
    assert body["run_ids"] == ["run-a", "run-b"]
    assert body["removed_run_ids"] == ["run-hidden", "missing"]
    assert body["run_count"] == 2
    assert body["site_count"] == 2
    assert body["site_counts"] == {SITE_A: 1, SITE_B: 1}
    assert body["confirmation"] == "CANCEL 2 RUNS"
    assert body["preview_id"]
    assert body["preview_token"]
    assert body["expires_at"].endswith("Z")


def test_preview_applies_the_requested_history_scope(preview_client: FlaskClient) -> None:
    response = preview_client.post(PATH, json=_body(history_scope=f"site:{SITE_A}"))

    assert response.status_code == 200
    body = response.get_json()
    assert body["run_ids"] == ["run-a"]
    assert body["removed_run_ids"] == ["run-hidden", "missing", "run-b"]


def test_preview_rejects_duplicate_identifiers(preview_client: FlaskClient) -> None:
    response = preview_client.post(PATH, json=_body(run_ids=["run-a", "run-a"]))

    assert response.status_code == 400
    assert _code(response) == "duplicate_run_id"


@pytest.mark.parametrize("run_ids", [[], [f"run-{number}" for number in range(51)]])
def test_preview_rejects_an_unsafe_batch_size(preview_client: FlaskClient, run_ids: list[str]) -> None:
    response = preview_client.post(PATH, json=_body(run_ids=run_ids))

    assert response.status_code == 422
    assert _code(response) == "batch_size_invalid"


def test_preview_rejects_a_different_organization(preview_client: FlaskClient) -> None:
    response = preview_client.post(PATH, json=_body(organization_id="other-org"))

    assert response.status_code == 403
    assert _code(response) == "organization_forbidden"


def test_preview_rejects_an_empty_authoritative_selection(preview_client: FlaskClient) -> None:
    response = preview_client.post(PATH, json=_body(run_ids=["run-hidden", "missing"]))

    assert response.status_code == 422
    assert _code(response) == "preview_empty"
