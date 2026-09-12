"""Integration test for SiteClientExporter.client_insights delegator."""

import importlib


def test_client_insights_delegates_to_serial_cc_service(monkeypatch):
    misthelper_module = importlib.import_module("MistHelper")
    serial_cc_module = importlib.import_module("src.refactors.serial_cc.site_client_insights")
    called = {"count": 0}

    def fake_execute():
        called["count"] += 1

    monkeypatch.setattr(serial_cc_module.SiteClientInsightsService, "execute", staticmethod(fake_execute))

    misthelper_module.SiteClientExporter.client_insights()

    assert called["count"] == 1
