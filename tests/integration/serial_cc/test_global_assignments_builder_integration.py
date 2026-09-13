"""Integration test for GlobalImportManager delegator to serial_cc builder service."""

import importlib


def test_global_import_manager_delegates_global_assignment_builder(monkeypatch):
    misthelper_module = importlib.import_module("MistHelper")
    serial_cc_module = importlib.import_module("src.refactors.serial_cc.global_assignments_builder")
    manager = misthelper_module.GlobalImportManager()
    manager.imports = {"foo": object()}
    called = {"count": 0, "imports": None}

    def fake_execute(imports, add_fallbacks_fn):
        called["count"] += 1
        called["imports"] = imports
        return {"ok": True}

    monkeypatch.setattr(serial_cc_module.GlobalAssignmentsBuilderService, "execute", staticmethod(fake_execute))

    result = manager._get_global_assignments()

    assert result == {"ok": True}
    assert called["count"] == 1
    assert called["imports"] is manager.imports
