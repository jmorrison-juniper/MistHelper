"""Targeted tests for Phase 2 and Phase 3 route connections."""

from __future__ import annotations

import inspect
from unittest.mock import Mock

from flask import Flask

from src.upgrade_portal.app import factory, wiring
from src.upgrade_portal.app.routes import capture, upgrade


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


def test_upgrade_start_route_passes_service_contract(monkeypatch) -> None:
    """The upgrade start route must pass scope and operator identity."""
    service = Mock(start_upgrade=Mock(return_value="run-1"))
    application = Flask(__name__)
    application.config["UPGRADE_SERVICE"] = service
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


def test_upgrade_cancel_route_passes_operator_identity(monkeypatch) -> None:
    """The upgrade cancel route must pass the operator identity."""
    service = Mock(cancel_upgrade=Mock(return_value=True))
    application = Flask(__name__)
    application.config["UPGRADE_SERVICE"] = service
    monkeypatch.setattr(upgrade, "actor_address", lambda: "operator@example.com")

    with application.test_request_context("/api/runs/run-1/upgrade/cancel", method="POST"):
        response, status = unwrapped(upgrade.cancel_upgrade_via_service)("run-1")

    assert status == 200
    assert response.get_json()["status"] == "cancelled"
    service.cancel_upgrade.assert_called_once_with("run-1", user_id="operator@example.com")


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
