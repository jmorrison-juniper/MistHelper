"""Test request resource caching, isolation, and ownership."""

from __future__ import annotations

import pytest  # The tests replace each external construction boundary.

from src.interfaces.portals.upgrade_portal.app import wiring  # The provider under test.
from tests.integration.upgrade_portal.issue_3834.test_default_provider import (
    FakeCloudSession,
    FakeDatabaseConfig,
    FakeDatabaseRouter,
    build_application,
    build_operator,
)


def test_repeated_resolution_reuses_one_router(monkeypatch: pytest.MonkeyPatch) -> None:
    """Repeated resolution in one request returns one resource graph."""
    application = build_application(monkeypatch)  # Register normal request teardown.
    cloud_session = FakeCloudSession()  # Keep borrowed-session ownership visible.
    operator = build_operator(cloud_session)  # Build one valid identity record.
    monkeypatch.setattr(wiring, "current_operator", lambda: operator)  # Authenticate the request.
    with application.test_request_context("/"):  # Open one request cache.
        first = wiring.request_dependencies()  # Construct the request graph.
        second = wiring.request_dependencies()  # Read the cached graph.
        assert second is first  # The request owns one immutable graph.
        assert len(FakeDatabaseRouter.instances) == 1  # The second read opens no router.
        router = first.database_router  # Keep the handle for teardown evidence.
    assert router.close_count == 1  # Teardown closes the cached router once.
    assert cloud_session.close_count == 0  # Teardown does not close the registry session.


def test_two_request_contexts_receive_distinct_routers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two request contexts own distinct routers and close each router once."""
    application = build_application(monkeypatch)  # Register normal request teardown.
    cloud_session = FakeCloudSession()  # Both requests borrow the same registry-owned session.
    operator = build_operator(cloud_session)  # Build one valid identity record.
    monkeypatch.setattr(wiring, "current_operator", lambda: operator)  # Authenticate both requests.
    routers: list[FakeDatabaseRouter] = []  # Preserve each owned handle after its context closes.
    for path in ("/first", "/second"):  # Open two independent Flask request contexts.
        with application.test_request_context(path):  # Start one request lifecycle.
            dependencies = wiring.request_dependencies()  # Construct that request router.
            routers.append(dependencies.database_router)  # Keep cleanup evidence.
    assert FakeDatabaseConfig.calls == 2  # Each request resolves its own configuration.
    assert len(FakeDatabaseRouter.instances) == 2  # Each request constructs one router.
    assert routers[0] is not routers[1]  # No request-owned router crosses the context boundary.
    assert [router.close_count for router in routers] == [1, 1]  # Teardown closes each router exactly once.
    assert cloud_session.close_count == 0  # Both requests leave the borrowed Mist session open.
