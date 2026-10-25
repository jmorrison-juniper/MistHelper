"""Targeted tests for Phase 2 and Phase 3 route connections."""

from __future__ import annotations

import inspect
from unittest.mock import Mock

import pytest
from flask import Flask

from src.interfaces.portals.upgrade_portal.app import factory, wiring
from src.interfaces.portals.upgrade_portal.app.routes import capture, upgrade


def unwrapped(route):
    """Return a route body without the session decorator."""
    return inspect.unwrap(route)


def test_factory_registers_comparison_routes() -> None:
    """The factory must register both comparison endpoints."""
    application = Flask(__name__)
    factory.register_one_blueprint(application, "comparison")
    paths = {rule.rule for rule in application.url_map.iter_rules()}
    assert "/api/runs/<run_id>/comparison/results" in paths
    assert "/api/runs/<run_id>/comparison/approve" in paths


def test_status_route_has_one_owner() -> None:
    """The status path must not have a second Phase 2 service owner."""
    application = Flask(__name__)
    application.register_blueprint(upgrade.upgrade_bp)
    status_rules = [rule for rule in application.url_map.iter_rules() if rule.rule == upgrade.STATUS_PATH]
    assert len(status_rules) == 1


def test_capture_route_passes_service_contract(monkeypatch) -> None:
    """The capture route must pass the complete service argument set."""
    service = Mock(capture_pre_upgrade=Mock(return_value="capture-1"))
    application = Flask(__name__)
    application.config["CAPTURE_SERVICE"] = service
    monkeypatch.setattr(capture, "actor_address", lambda: "operator@example.com")

    with application.test_request_context(
        "/api/runs/run-1/capture/start",
        method="POST",
        json={"org_id": "org-1", "site_id": "site-1", "device_ids": ["device-1"]},
    ):
        response, status = unwrapped(capture.capture_pre_upgrade_for_run)("run-1")

    assert status == 202
    assert response.get_json()["capture_id"] == "capture-1"
    service.capture_pre_upgrade.assert_called_once_with(
        run_id="run-1",
        org_id="org-1",
        site_id="site-1",
        device_ids=["device-1"],
        user_id="operator@example.com",
    )


def test_upgrade_start_route_passes_service_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """The upgrade start route must pass scope and operator identity."""
    service = Mock(start_upgrade=Mock(return_value="run-1"))
    dependencies = Mock()
    dependencies.mutation_services.resolve.return_value = service
    application = Flask(__name__)
    application.config["UPGRADE_SERVICE"] = Mock()
    monkeypatch.setattr(upgrade, "request_dependencies", Mock(return_value=dependencies))
    monkeypatch.setattr(upgrade, "actor_address", lambda: "operator@example.com")
    monkeypatch.setattr(upgrade, "operator_write_refusal", lambda: None)

    with application.test_request_context(
        "/api/runs/run-1/upgrade/start",
        method="POST",
        json={
            "org_id": "org-1",
            "site_id": "site-1",
            "device_ids": ["device-1"],
            "firmware_version": "1.2.3",
            "strategy": "serial",
            "rollback_enabled": True,
        },
    ):
        response, status = unwrapped(upgrade.start_upgrade_via_service)("run-1")

    assert status == 202
    assert response.get_json()["status"] == "pending"
    dependencies.mutation_services.resolve.assert_called_once_with(upgrade.UPGRADE_SERVICE_KEY)
    service.start_upgrade.assert_called_once_with(
        run_id="run-1",
        org_id="org-1",
        site_id="site-1",
        device_ids=["device-1"],
        firmware_version="1.2.3",
        strategy="serial",
        rollback_enabled=True,
        user_id="operator@example.com",
    )


def test_upgrade_cancel_route_passes_operator_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """The upgrade cancel route must pass the operator identity."""
    service = Mock(cancel_upgrade=Mock(return_value=True))
    dependencies = Mock()
    dependencies.mutation_services.resolve.return_value = service
    application = Flask(__name__)
    application.config["UPGRADE_SERVICE"] = Mock()
    monkeypatch.setattr(upgrade, "request_dependencies", Mock(return_value=dependencies))
    monkeypatch.setattr(upgrade, "actor_address", lambda: "operator@example.com")

    with application.test_request_context("/api/runs/run-1/upgrade/cancel", method="POST"):
        response, status = unwrapped(upgrade.cancel_upgrade_via_service)("run-1")

    assert status == 200
    assert response.get_json()["status"] == "cancelled"
    dependencies.mutation_services.resolve.assert_called_once_with(upgrade.UPGRADE_SERVICE_KEY)
    service.cancel_upgrade.assert_called_once_with("run-1", user_id="operator@example.com")


def test_upgrade_status_route_uses_request_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """The status route must resolve its service from the active request."""
    service = Mock(get_upgrade_status=Mock(return_value={"devices": []}))  # Supply a safe status stand-in.
    dependencies = Mock()  # Hold the fake request service factory.
    dependencies.mutation_services.resolve.return_value = service  # Return the status stand-in.
    application = Flask(__name__)  # Build a route context without production startup.
    application.config["UPGRADE_SERVICE"] = Mock()  # Ensure the legacy global seam is ignored.
    monkeypatch.setattr(upgrade, "request_dependencies", Mock(return_value=dependencies))  # Use request wiring.

    with application.test_request_context("/api/runs/run-1/upgrade/status"):  # Keep the request context active.
        response, status = unwrapped(upgrade.upgrade_status_via_service)("run-1")  # Exercise the undecorated route.

    assert status == 200  # Return the request service result.
    assert response.get_json() == {"devices": []}  # Keep the status response shape.
    dependencies.mutation_services.resolve.assert_called_once_with(upgrade.UPGRADE_SERVICE_KEY)  # Use the provider.
    service.get_upgrade_status.assert_called_once_with("run-1")  # Read the requested run once.


def test_upgrade_start_refusal_precedes_request_service_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """A refused firmware request must not construct mutation dependencies."""
    dependencies = Mock()  # Detect any request-service construction.
    application = Flask(__name__)  # Build a route context without production startup.
    monkeypatch.setattr(upgrade, "request_dependencies", Mock(return_value=dependencies))  # Track provider access.
    monkeypatch.setattr(
        upgrade,
        "operator_write_refusal",
        lambda: (upgrade.jsonify({"error": "refused"}), 403),
    )  # Refuse before service construction.

    with application.test_request_context(  # Supply a valid request that reaches the authorization gate.
        "/api/runs/run-1/upgrade/start",
        method="POST",
        json={
            "org_id": "org-1",
            "site_id": "site-1",
            "device_ids": ["device-1"],
            "firmware_version": "1.2.3",
            "strategy": "serial",
            "rollback_enabled": True,
        },
    ):
        response, status = unwrapped(upgrade.start_upgrade_via_service)("run-1")  # Exercise the undecorated route.

    assert status == 403  # Preserve the existing authorization refusal.
    assert response.get_json() == {"error": "refused"}  # Keep the refusal response.
    upgrade.request_dependencies.assert_not_called()  # Do not build mutation resources after refusal.


def test_upgrade_start_refuses_when_request_service_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing request service must stop the firmware route before a write."""
    application = Flask(__name__)  # Build a route context without production startup.
    monkeypatch.setattr(upgrade, "operator_write_refusal", lambda: None)  # Pass the existing write guard.
    monkeypatch.setattr(
        upgrade,
        "request_dependencies",
        Mock(side_effect=upgrade.PortalDependencyError("provider unavailable")),
    )  # Make the request dependency boundary fail closed.

    with application.test_request_context(  # Supply a valid upgrade request without a production service.
        "/api/runs/run-1/upgrade/start",
        method="POST",
        json={
            "org_id": "org-1",
            "site_id": "site-1",
            "device_ids": ["device-1"],
            "firmware_version": "1.2.3",
            "strategy": "serial",
            "rollback_enabled": True,
        },
    ):
        response, status = unwrapped(upgrade.start_upgrade_via_service)("run-1")  # Exercise the undecorated route.

    assert status == 503  # Refuse the request because its service is absent.
    assert response.get_json()["error"]["code"] == "service_unavailable"  # Do not claim an upgrade started.


def test_phase_services_install_without_legacy_mistapi(monkeypatch) -> None:
    """Service installers must use configured collaborators instead of the removed module."""
    application = Flask(__name__)
    application.config["MIST_CLIENT"] = Mock()
    application.config["DB_ROUTER"] = Mock()
    loaded = {
        wiring.CAPTURE_SERVICE_MODULE: Mock(CaptureService=Mock()),
        wiring.UPGRADE_SERVICE_MODULE: Mock(UpgradeService=Mock()),
        wiring.SETTLE_GATE_SERVICE_MODULE: Mock(SettleGateService=Mock()),
        wiring.COMPARISON_SERVICE_MODULE: Mock(ComparisonService=Mock()),
    }

    def load_module(name):
        return loaded.get(name)

    monkeypatch.setattr(wiring, "load_module", load_module)
    wiring._install_capture_service(application)
    wiring._install_upgrade_service(application)
    wiring._install_settle_gate_service(application)
    wiring._install_comparison_service(application)

    assert {
        "CAPTURE_SERVICE",
        "UPGRADE_SERVICE",
        "SETTLE_GATE_SERVICE",
        "COMPARISON_SERVICE",
    }.issubset(application.config)
    loaded[wiring.CAPTURE_SERVICE_MODULE].CaptureService.assert_called_once()
    loaded[wiring.UPGRADE_SERVICE_MODULE].UpgradeService.assert_called_once()
    loaded[wiring.SETTLE_GATE_SERVICE_MODULE].SettleGateService.assert_called_once()
    loaded[wiring.COMPARISON_SERVICE_MODULE].ComparisonService.assert_called_once()
