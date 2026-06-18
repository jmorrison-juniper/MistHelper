"""Integration test for GlobalImportManager.initialize_all_imports delegator."""

import importlib


def test_initialize_all_imports_delegates_to_service(monkeypatch):
    misthelper_module = importlib.import_module("MistHelper")
    serial_cc_module = importlib.import_module("src.refactors.serial_cc.import_initialization_service")
    manager = misthelper_module.GlobalImportManager()
    called = {"count": 0, "manager": None, "skip_deps": None}

    def fake_execute(passed_manager, skip_deps=False):
        called["count"] += 1
        called["manager"] = passed_manager
        called["skip_deps"] = skip_deps
        return True, {"ok": True}

    monkeypatch.setattr(serial_cc_module.ImportInitializationService, "execute", staticmethod(fake_execute))

    result = manager.initialize_all_imports(skip_deps=True)

    assert result == (True, {"ok": True})
    assert called["count"] == 1
    assert called["manager"] is manager
    assert called["skip_deps"] is True
