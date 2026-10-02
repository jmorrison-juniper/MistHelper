"""Require correct saved strategy states before the shared script executes."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from src.upgrade_portal.runtime import identity
from tests.e2e.upgrade_portal.strategy_failure_limit.portal import FailureLimitPortal
from tests.unit.upgrade_portal.strategy_failure_limit.markup import FailureFieldGuard


@pytest.fixture
def failure_portal(monkeypatch: pytest.MonkeyPatch) -> Iterator[FailureLimitPortal]:
    """Own an actual route application with no cloud or firmware transport."""
    portal = FailureLimitPortal(monkeypatch)
    try:
        yield portal
    finally:
        portal.require_idle()
        owner = portal.app.config.get("FAILURE_LIMIT_OWNER")
        if owner is not None:
            identity.SESSION_REGISTRY.drop(owner.key)


class TestInitialFailureLimit:
    """Read the actual controller response instead of a copied template fragment."""

    @pytest.mark.parametrize("strategy", ["canary", "big_bang", "rrm", "serial"])
    @pytest.mark.parametrize("percentage", [0, 5, 23, 100])
    def test_saved_initial_state(self, failure_portal: FailureLimitPortal, strategy: str, percentage: int) -> None:
        """The saved strategy and percentage set the initial hidden and disabled states."""
        failure_portal.seed(strategy, percentage)
        response = failure_portal.client.get("/upgrade/org/options")
        assert response.status_code == 200
        guard = FailureFieldGuard(response.get_data(as_text=True))
        guard.require(strategy, percentage)
        assert guard.checked == 1

    def test_the_unsaved_page_keeps_canary_and_five(self, failure_portal: FailureLimitPortal) -> None:
        """An unsaved page retains the current Canary strategy and default percentage."""
        failure_portal.seed(None)
        response = failure_portal.client.get("/upgrade/org/options")
        assert response.status_code == 200
        text = response.get_data(as_text=True)
        FailureFieldGuard(text).require("canary", 5)
        assert 'for="max-failure-percentage">Maximum failure percentage</label>' in text
