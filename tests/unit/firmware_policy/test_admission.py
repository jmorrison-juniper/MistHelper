"""Prove real quota admission, long waits, shared pacing, and request progress."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.foundation.support.utils.rate_limiting import AdaptivePacer
from src.mist.access.api.api_usage_cache import api_usage_cache
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SettingsSession


def test_real_rolling_hour_exhaustion_waits_above_600_seconds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A wall-clock hour change cannot release a still-exhausted rolling quota."""
    session = SettingsSession(tmp_path)
    clock = [3599.0]
    events: list[dict[str, Any]] = []
    original = session.mist_get
    probes = []

    def get(uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Return exhaustion across the wall-clock boundary until real usage decreases."""
        if uri == "/api/v1/self/usage":
            probes.append(clock[0])
            return SimpleNamespace(
                status_code=200,
                data={"requests": 4999 if clock[0] < 4259 else 100, "request_limit": 5000},
            )
        assert clock[0] >= 4259
        return original(uri, query)

    monkeypatch.setattr(session, "mist_get", get)
    monkeypatch.setattr("src.operations.execution.firmware_policy.sdk.time.time", lambda: clock[0])
    monkeypatch.setattr(
        "src.operations.execution.firmware_policy.sdk.time.sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    result = PolicyApi(session, progress=events.append).read("org", ORG_ID)
    assert result["allow_mist"] is False
    assert clock[0] - 3599 == 660
    assert len(probes) == 12
    assert sum(event.get("wait_seconds", 0) for event in events) == 660
    assert api_usage_cache["policy_actual_used"] == 102


@pytest.mark.parametrize("status", [403, 503])
def test_failed_usage_probe_prevents_every_settings_request(tmp_path: Path, status: int) -> None:
    """Unreadable authoritative usage must not degrade into assumed quota availability."""
    session = SettingsSession(tmp_path)
    session.status = status
    session.fail_read = "/api/v1/self/usage"
    with pytest.raises(PolicyError, match=f"HTTP {status}"):
        PolicyApi(session).read("org", ORG_ID)
    assert session.reads == [("/api/v1/self/usage", {})]
    assert session.writes == []


def test_every_request_and_usage_probe_uses_shared_adaptive_pacer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shared pacing remains connected to actual usage and the existing cache."""
    calls = []
    monkeypatch.setattr(AdaptivePacer, "next_delay", lambda self: calls.append(self._api_usage_cache) or 0.0)
    api = PolicyApi(SettingsSession(tmp_path))
    api.read("org", ORG_ID)
    api.sites(ORG_ID)
    assert len(calls) == 3
    assert all(cache is api_usage_cache for cache in calls)
    assert api_usage_cache["policy_actual_used"] == 3


def test_server_quota_wait_above_600_seconds_is_visible_and_rechecked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use a supplied long wait but require another real usage observation afterward."""
    session = SettingsSession(tmp_path)
    clock = [0.0]
    events: list[dict[str, Any]] = []
    original = session.mist_get
    probes = []

    def get(uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Release the fixture quota only after the server-supplied wait passes."""
        if uri == "/api/v1/self/usage":
            probes.append(clock[0])
            return SimpleNamespace(
                status_code=200,
                data={
                    "requests": 4999 if clock[0] < 660 else 100,
                    "request_limit": 5000,
                    "seconds": 660,
                },
            )
        return original(uri, query)

    monkeypatch.setattr(session, "mist_get", get)
    monkeypatch.setattr("src.operations.execution.firmware_policy.sdk.time.time", lambda: clock[0])
    monkeypatch.setattr(
        "src.operations.execution.firmware_policy.sdk.time.sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    assert PolicyApi(session, progress=events.append).read("org", ORG_ID)["allow_mist"] is False
    assert probes == [0, 660]
    assert any(event.get("wait_seconds") == 660 for event in events)
