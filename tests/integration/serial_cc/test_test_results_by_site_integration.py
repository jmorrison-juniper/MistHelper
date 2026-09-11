"""Integration test for test_results_by_site delegator path in MistHelper."""

import importlib


def test_misthelper_test_results_by_site_delegates_to_serial_cc_service(monkeypatch):
    """Legacy test_results_by_site method delegates to extracted serial_cc service."""
    misthelper_module = importlib.import_module("MistHelper")  # Import MistHelper module under test
    called = {"count": 0, "fast": None}  # Invocation counter and fast-flag recorder

    def fake_execute(fast=False):
        called["count"] += 1  # Record one invocation from delegator
        called["fast"] = fast  # Capture the fast flag forwarded by delegator

    serial_cc_module = importlib.import_module("src.refactors.serial_cc.test_results_by_site")  # Target service module
    monkeypatch.setattr(
        serial_cc_module.GatewayTestResultsService, "execute", staticmethod(fake_execute)
    )  # Patch target so no real API calls are made

    misthelper_module.GatewayTestExporter.test_results_by_site()  # Invoke legacy method in standard mode

    assert called["count"] == 1  # Delegator must invoke extracted service exactly once
    assert called["fast"] is False  # Default fast=False must be forwarded correctly


def test_misthelper_test_results_by_site_forwards_fast_flag(monkeypatch):
    """Delegator forwards fast=True to extracted service without modification."""
    misthelper_module = importlib.import_module("MistHelper")  # Import MistHelper module under test
    called = {"count": 0, "fast": None}  # Invocation counter and fast-flag recorder

    def fake_execute(fast=False):
        called["count"] += 1  # Record one invocation from delegator
        called["fast"] = fast  # Capture the fast flag forwarded by delegator

    serial_cc_module = importlib.import_module("src.refactors.serial_cc.test_results_by_site")  # Target service module
    monkeypatch.setattr(
        serial_cc_module.GatewayTestResultsService, "execute", staticmethod(fake_execute)
    )  # Patch target so no real API calls are made

    misthelper_module.GatewayTestExporter.test_results_by_site(fast=True)  # Invoke in fast mode

    assert called["count"] == 1  # Delegator must invoke extracted service exactly once
    assert called["fast"] is True  # fast=True must be forwarded correctly to service
