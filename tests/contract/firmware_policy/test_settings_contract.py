"""Prove SDK endpoint parity, status checks, pagination, and credential redaction."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import mistapi
import pytest

from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError, PolicyResponse
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID, SettingsSession


@pytest.mark.parametrize("status_code", [400, 403, 500, 503])
def test_http_4xx_and_5xx_fail_without_response_body_leak(tmp_path: Path, caplog: Any, status_code: int) -> None:
    """Status failures must not disclose settings credentials in messages or logs."""
    session = SettingsSession(tmp_path)
    session.status = status_code
    session.fail_read = f"/api/v1/orgs/{ORG_ID}/setting"
    with caplog.at_level(logging.DEBUG), pytest.raises(PolicyError, match=f"HTTP {status_code}") as failure:
        PolicyApi(session).read("org", ORG_ID)
    assert "private-fixture" not in str(failure.value)
    assert "private-fixture" not in caplog.text
    assert session.writes == []


def test_real_sdk_read_endpoint_parity_uses_supplied_session(tmp_path: Path) -> None:
    """Read both settings scopes through actual SDK methods and the supplied session."""
    session = SettingsSession(tmp_path)
    api = PolicyApi(session)
    assert api.read("org", ORG_ID)["allow_mist"] is False
    assert api.read("site", SITE_ID)["allow_mist"] is True
    assert session.reads == [
        ("/api/v1/self/usage", {}),
        (f"/api/v1/orgs/{ORG_ID}/setting", {}),
        (f"/api/v1/sites/{SITE_ID}/setting", {}),
    ]
    assert session.writes == []


@pytest.mark.parametrize("status_code", [403, 503])
def test_failed_second_page_cannot_become_a_partial_site_list(monkeypatch: Any, status_code: int) -> None:
    """Every SDK page must pass its status check before planning continues."""
    first = SimpleNamespace(status_code=200, data=[{"id": SITE_ID}], next="next-page")
    failed = SimpleNamespace(status_code=status_code, data={"error": "private-fixture"}, next=None)
    monkeypatch.setattr(mistapi, "get_next", lambda session, response: failed)
    with pytest.raises(PolicyError, match=f"HTTP {status_code}"):
        PolicyResponse.collect(object(), lambda: first, "List organization sites", ORG_ID)


def test_repeated_pagination_link_fails(monkeypatch: Any) -> None:
    """A repeated SDK next link cannot create an unbounded page loop."""
    first = SimpleNamespace(status_code=200, data=[], next="same")
    monkeypatch.setattr(mistapi, "get_next", lambda session, response: first)
    with pytest.raises(PolicyError, match="repeated pagination"):
        PolicyResponse.collect(object(), lambda: first, "List organization sites", ORG_ID)


def test_api_admits_every_sdk_site_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The next-page SDK helper must pass through the same request admission path."""
    session = SettingsSession(tmp_path)
    original = session.mist_get
    first = SimpleNamespace(status_code=200, data=[{"id": SITE_ID}], next="page-two")
    second = SimpleNamespace(status_code=200, data=[], next=None)
    pages = []

    def get(uri: str, query: dict[str, str] | None = None) -> Any:
        """Return an admitted paginated site list and actual fixture usage."""
        return first if uri.endswith("/sites") else original(uri, query)

    monkeypatch.setattr(session, "mist_get", get)
    monkeypatch.setattr(mistapi, "get_next", lambda supplied, response: pages.append(response) or second)
    api = PolicyApi(session)
    requests = []
    checked = api.guard.request

    def admitted(call: Any, action: str, identifier: str) -> Any:
        """Observe admission without replacing status or quota checks."""
        requests.append((action, identifier))
        return checked(call, action, identifier)

    monkeypatch.setattr(api.guard, "request", admitted)
    assert api.sites(ORG_ID) == [{"id": SITE_ID}]
    assert pages == [first]
    assert requests == [("List organization sites", ORG_ID)] * 2


@pytest.mark.parametrize("value", [None, [], "unreadable"])
def test_invalid_settings_shape_fails(value: Any) -> None:
    """Malformed settings cannot become an empty successful snapshot."""
    with pytest.raises(PolicyError, match="not an object"):
        PolicyResponse.mapping(value)


@pytest.mark.parametrize("identifier", ["", "not-a-uuid", None, {}])
def test_bad_scope_stops_before_sdk_request(tmp_path: Path, identifier: Any) -> None:
    """Validate scope input before invoking any external transport."""
    session = SettingsSession(tmp_path)
    with pytest.raises(PolicyError, match="UUID"):
        PolicyApi(session).read("org", identifier)
    assert session.reads == []
    assert session.writes == []


def test_transport_exception_redacts_credential_text(caplog: Any) -> None:
    """An SDK exception can contain credentials and must not be logged verbatim."""

    def failed_request() -> Any:
        """Simulate an SDK exception containing confidential response details."""
        raise RuntimeError("conductor_token=private-fixture")

    with caplog.at_level(logging.DEBUG), pytest.raises(PolicyError, match="RuntimeError") as failure:
        PolicyResponse.request(failed_request, "Read org settings", ORG_ID)
    assert "private-fixture" not in str(failure.value)
    assert "private-fixture" not in caplog.text
