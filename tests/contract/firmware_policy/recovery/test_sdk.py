"""Prove settings-only SDK calls, diagnostic privacy, and disabled write retries."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import mistapi
import pytest
from requests import Request, Response

from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID
from tests.unit.firmware_policy.recovery.fakes import RestoreSession


@pytest.mark.parametrize("status", [400, 403, 429, 500, 503])
def test_private_sdk_write_diagnostics_and_retry_control(
    tmp_path: Path, monkeypatch: Any, caplog: Any, status: int
) -> None:
    """Guard the SDK body logger before it can emit a full settings body."""
    session = RestoreSession(tmp_path)
    session._MAX_429_RETRIES = 4
    attempts = []

    def put(uri: str, body: dict[str, Any]) -> Any:
        """Exercise the SDK logger and observe the retry value at the write boundary."""
        attempts.append(uri)
        assert session._MAX_429_RETRIES == 0
        logging.getLogger("mistapi").debug("apirequest:mist_put:Request body:%s", body)
        logging.getLogger("mistapi").error("SDK exception contains private-fixture", exc_info=True)
        return SimpleNamespace(status_code=status, data={"error": "private-fixture"})

    monkeypatch.setattr(session, "mist_put", put)
    with caplog.at_level(logging.DEBUG), pytest.raises(PolicyError, match=f"HTTP {status}"):
        PolicyApi(session).write("org", ORG_ID, {"ssr": {"conductor_token": "private-fixture"}})
    assert attempts == [f"/api/v1/orgs/{ORG_ID}/setting"]
    assert session._MAX_429_RETRIES == 4
    assert "private-fixture" not in caplog.text
    assert "diagnostic redacted" in caplog.text


def test_all_restore_requests_use_actual_settings_sdk_methods(tmp_path: Path) -> None:
    """The fake refuses any non-settings write while the real SDK chooses the URLs."""
    session = RestoreSession(tmp_path)
    result = session.workflow().apply(session.prepare(), "RESTORE")
    assert len(result.completed) == 2
    assert all(uri.endswith("/setting") for uri, _ in session.writes)
    assert all(uri.endswith(("/setting", "/sites")) for uri, _ in session.reads)


def test_real_sdk_429_write_is_attempted_once_and_console_stays_private(
    monkeypatch: Any, caplog: Any, capsys: Any
) -> None:
    """Execute the real SDK retry loop with a local response and no network socket."""
    from mistapi.__api_response import console

    sdk = object.__new__(mistapi.APISession)
    sdk._token_lock = threading.Lock()
    sdk._count = 0
    calls: list[str] = []
    response = Response()
    response.status_code = 429
    response._content = b'{"error":"private-fixture"}'
    response.request = Request("PUT", "https://api.mist.com/offline").prepare()

    def offline_put(url: str, **kwargs: Any) -> Response:
        """Return a rate-limit response while counting actual transport attempts."""
        calls.append(url)
        return response

    monkeypatch.setattr(sdk, "_session", SimpleNamespace(put=offline_put), raising=False)
    monkeypatch.setattr(sdk, "_url", lambda uri: "https://api.mist.com" + uri)
    monkeypatch.setattr(sdk, "_log_proxy", lambda: None)
    monkeypatch.setattr(console, "level", 10)
    with caplog.at_level(logging.DEBUG), pytest.raises(PolicyError, match="HTTP 429"):
        PolicyApi(sdk).write("org", ORG_ID, {"ssr": {"conductor_token": "private-fixture"}})
    assert calls == [f"https://api.mist.com/api/v1/orgs/{ORG_ID}/setting"]
    assert console.level == 10
    assert "private-fixture" not in caplog.text + capsys.readouterr().out
