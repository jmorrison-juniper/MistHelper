"""Keep offline policy tests fast while retaining real request admission."""

from collections.abc import Iterator

import pytest

from src.foundation.support.utils.rate_limiting import AdaptivePacer
from src.mist.access.api.api_usage_cache import api_usage_cache


@pytest.fixture(autouse=True)
def offline_pacing(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Mock only the clock delay and isolate the process-wide quota cache."""
    previous = dict(api_usage_cache)
    api_usage_cache.clear()
    monkeypatch.setattr(AdaptivePacer, "next_delay", lambda self: 0.0)
    monkeypatch.setattr("src.operations.execution.firmware_policy.sdk.time.sleep", lambda seconds: None)
    yield
    api_usage_cache.clear()
    api_usage_cache.update(previous)
