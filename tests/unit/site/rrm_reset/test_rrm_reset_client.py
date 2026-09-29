"""Tests for the RRM optimize or reset client."""

from __future__ import annotations  # WHY: keep annotations lightweight during tests.

from types import SimpleNamespace  # WHY: build small SDK response doubles.
from typing import Any  # WHY: fake session stores dynamic bodies.

import pytest  # WHY: assert raised API failures.

from src.site.rrm_reset.client import RESET_RRM_PATH, RrmResetClient


class FakePostSession:
    """Record fallback Mist POST calls."""

    def __init__(self) -> None:
        """Create an empty call log."""
        self.calls: list[tuple[str, dict[str, Any]]] = []  # WHY: tests assert the path and body.

    def mist_post(self, uri: str, body: dict[str, Any] | list[Any] | None = None) -> SimpleNamespace:
        """Record the POST call."""
        self.calls.append((uri, dict(body or {})))  # WHY: preserve call order and body for assertions.
        return SimpleNamespace(status_code=200, data={})  # WHY: mimic an accepted SDK response.


def test_rrm_reset_client_reset_uses_documented_fallback_path() -> None:
    """Reset uses mist_post because the installed SDK lacks resetSiteAllApsToUseRrm."""
    session = FakePostSession()  # WHY: fake session records fallback POSTs.
    client = RrmResetClient(session)  # WHY: client under test.
    client.reset("site-1", {"bands": ["24", "5", "6"]})  # WHY: send the documented reset request.
    assert session.calls == [(RESET_RRM_PATH.format(site_id="site-1"), {"bands": ["24", "5", "6"]})]


def test_rrm_reset_client_current_plan_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Current-plan reads reject failing HTTP status codes."""
    client = RrmResetClient(object())  # WHY: patched SDK ignores the session.

    def fake_read(_session: object, _site_id: str) -> SimpleNamespace:
        return SimpleNamespace(status_code=503, data={})  # WHY: simulate cloud failure.

    monkeypatch.setattr("mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning", fake_read)  # WHY: no network.
    with pytest.raises(RuntimeError):  # WHY: caller must stop before destructive requests.
        client.get_current_plan("site-1")  # WHY: failed read should raise.
