"""Integration test for switch_vc_stats delegator path in MistHelper."""

import importlib


def test_misthelper_switch_vc_stats_delegates_to_serial_cc_service(monkeypatch):
    """Legacy switch_vc_stats method delegates to extracted serial_cc service."""
    misthelper_module = importlib.import_module("MistHelper")  # Import MistHelper module under test
    called = {"count": 0}  # Invocation counter for delegator verification

    def fake_execute():
        called["count"] += 1  # Record one invocation from delegator

    serial_cc_module = importlib.import_module("src.refactors.serial_cc.switch_vc_stats")  # Target service module
    monkeypatch.setattr(serial_cc_module.SwitchVcStatsService, "execute", staticmethod(fake_execute))  # Patch call

    misthelper_module.OrgDeviceStatsExporter.switch_vc_stats()  # Invoke legacy method under test

    assert called["count"] == 1  # Delegator must invoke extracted service exactly once
