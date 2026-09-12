"""Integration test for offender #9 delegator path in MistHelper."""

import importlib


def test_misthelper_sle_metrics_delegates_to_serial_cc_service(monkeypatch):
    """Legacy SLE export method delegates to extracted serial_cc service."""
    misthelper_module = importlib.import_module("MistHelper")
    called = {"count": 0, "fast": None}

    def fake_execute(fast=False):
        called["count"] += 1
        called["fast"] = fast

    serial_cc_module = importlib.import_module("src.refactors.serial_cc.sle_metrics")
    monkeypatch.setattr(serial_cc_module.SLEMetricsService, "execute", staticmethod(fake_execute))

    misthelper_module.OrgExportUtils.sle_metrics(False)

    assert called["count"] == 1
    assert called["fast"] is False
