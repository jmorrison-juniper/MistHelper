"""Prove the capture route resolves only authenticated request resources."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask

from src.interfaces.portals.upgrade_portal.app import factory, wiring
from src.interfaces.portals.upgrade_portal.app.routes import capture


class FakeMistSession:
    """Block every Mist request while preserving the provider contract."""

    def get(self, *_args: Any, **_kwargs: Any) -> None:
        """Fail if a test attempts a live Mist read."""
        raise AssertionError("The fake Mist session cannot make a request.")

    def post(self, *_args: Any, **_kwargs: Any) -> None:
        """Fail if a test attempts a live Mist write."""
        raise AssertionError("The fake Mist session cannot make a request.")


class FakeDatabaseRouter:
    """Stand in for one request-owned database router."""

    instances: list[FakeDatabaseRouter] = []

    def __init__(self, _config: object) -> None:
        """Record one isolated router without opening a connection."""
        self.closed = False
        self.instances.append(self)

    def close(self) -> None:
        """Record request teardown."""
        self.closed = True


class FakeCaptureService:
    """Record capture dependencies and refuse any external operation."""

    instances: list[FakeCaptureService] = []

    def __init__(self, mist_client: Any, db_router: Any, audit_logger: Any) -> None:
        """Keep the request-owned collaborators for assertions."""
        self.mist_client = mist_client
        self.db_router = db_router
        self.audit_logger = audit_logger
        self.request: dict[str, Any] | None = None
        self.instances.append(self)

    def capture_pre_upgrade(self, **request: Any) -> str:
        """Return a fake capture identifier without contacting Mist or storage."""
        self.request = request
        return "capture-4653"


class FailingDatabaseRouter:
    """Reject database construction without opening a network connection."""

    def __init__(self, _config: object) -> None:
        """Raise the same construction failure the provider must contain."""
        raise OSError("offline database stand-in")


def build_application(
    monkeypatch: pytest.MonkeyPatch,
    operator: Any,
    database_router: type[Any] = FakeDatabaseRouter,
) -> Flask:
    """Build the no-argument factory with every external boundary replaced."""
    FakeDatabaseRouter.instances.clear()  # Keep router evidence local to this test.
    FakeCaptureService.instances.clear()  # Keep service evidence local to this test.
    monkeypatch.setattr(wiring, "DatabaseConfig", SimpleNamespace(from_env=lambda: object()))
    monkeypatch.setattr(wiring, "DatabaseRouter", database_router)
    monkeypatch.setattr(
        wiring,
        "_install_action_repository",
        lambda application: application.config.setdefault("RUN_ACTION_STORE", object()),
    )
    monkeypatch.setattr(wiring, "prepare_storage", lambda: None)
    monkeypatch.setattr(wiring, "current_operator", lambda: operator)
    original_loader = wiring.load_module

    def load_module(name: str) -> Any:
        """Provide a fake capture service and retain other production imports."""
        if name == wiring.CAPTURE_SERVICE_MODULE:
            return SimpleNamespace(CaptureService=FakeCaptureService)
        return original_loader(name)

    monkeypatch.setattr(wiring, "load_module", load_module)
    monkeypatch.setattr(capture, "actor_address", lambda: "offline@example.test")
    return factory.create_app()


def invoke_capture(application: Flask) -> tuple[Any, int]:
    """Call the registered capture handler without its browser-login wrapper."""
    with application.test_request_context(
        "/api/runs/run-1/capture/start",
        method="POST",
        json={"org_id": "org-1", "site_id": "site-1", "device_ids": ["device-1"]},
    ):
        return inspect.unwrap(capture.capture_pre_upgrade_for_run)("run-1")


def test_default_factory_resolves_capture_with_request_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The normal factory must bind capture to the authenticated request graph."""
    session = FakeMistSession()
    operator = SimpleNamespace(cloud_session=session)
    application = build_application(monkeypatch, operator)
    assert capture.CAPTURE_SERVICE_KEY not in application.config
    response, status = invoke_capture(application)
    service = FakeCaptureService.instances[0]
    assert status == 202
    assert response.get_json()["capture_id"] == "capture-4653"
    assert service.mist_client is session
    assert service.db_router is FakeDatabaseRouter.instances[0]
    assert service.request == {
        "run_id": "run-1",
        "org_id": "org-1",
        "site_id": "site-1",
        "device_ids": ["device-1"],
        "user_id": "offline@example.test",
    }
    assert FakeDatabaseRouter.instances[0].closed is True


def test_capture_refuses_missing_operator_before_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An absent identity must fail before router or capture construction."""
    application = build_application(monkeypatch, None)
    response, status = invoke_capture(application)
    assert status == 401
    assert response.get_json() == {
        "error": {"code": "not_authenticated", "message": "The operator session is unavailable."}
    }
    assert FakeDatabaseRouter.instances == []
    assert FakeCaptureService.instances == []


def test_capture_refuses_database_failure_before_service_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A database failure must return service unavailable without capture work."""
    operator = SimpleNamespace(cloud_session=FakeMistSession())
    application = build_application(monkeypatch, operator, FailingDatabaseRouter)
    response, status = invoke_capture(application)
    assert status == 503
    assert response.get_json() == {"error": {"code": "service_unavailable", "message": "CaptureService not available"}}
    assert FakeCaptureService.instances == []


def test_configured_capture_service_override_remains_usable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit service override must remain independent of request construction."""
    application = build_application(monkeypatch, None)  # No operator is needed for an explicit test seam.
    configured_service = FakeCaptureService(object(), object(), object())  # Keep every external boundary local.
    application.config[capture.CAPTURE_SERVICE_KEY] = configured_service  # Preserve the established test override.
    response, status = invoke_capture(application)  # Call only the unwrapped test handler.

    assert status == 202  # An explicit service can still accept the isolated request.
    assert response.get_json()["capture_id"] == "capture-4653"  # Confirm the override served the request.
    assert configured_service.request == {  # Prove the route used the configured service.
        "run_id": "run-1",  # Keep the requested run bound to the override.
        "org_id": "org-1",  # Preserve the organization scope.
        "site_id": "site-1",  # Preserve the site scope.
        "device_ids": ["device-1"],  # Preserve the requested devices.
        "user_id": "offline@example.test",  # Preserve the test actor identity.
    }  # Match the complete capture call.
    assert FakeDatabaseRouter.instances == []  # Do not build request storage for an explicit override.
