"""Unit tests for ImportInitializationService extraction."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.refactors.serial_cc.import_initialization_service import ImportInitializationService


def _build_manager():
    manager = SimpleNamespace()
    manager._initialization_complete = False
    manager._initialization_success = False
    manager._cached_global_assignments = {}
    manager.auto_upgrade_uv = False
    manager.required_packages = {"json": None}
    manager.optional_packages = {"math": None}
    manager.failed_imports = []
    manager.imports = {"json": object(), "math": object()}
    manager.installed_packages = []
    manager._check_uv_installation = MagicMock(return_value=True)
    manager._install_uv = MagicMock()
    manager._upgrade_uv = MagicMock()
    manager._import_packages_concurrently = MagicMock()
    manager.import_module_safely = MagicMock(return_value=True)
    manager._import_special_modules = MagicMock()
    manager._get_global_assignments = MagicMock(return_value={"ok": True})
    return manager


def test_returns_cached_when_already_initialized():
    manager = _build_manager()
    manager._initialization_complete = True
    manager._initialization_success = True
    manager._cached_global_assignments = {"cached": True}

    result = ImportInitializationService.execute(manager, skip_deps=False)

    assert result == (True, {"cached": True})


def test_initializes_and_caches_results():
    manager = _build_manager()

    success, assignments = ImportInitializationService.execute(manager, skip_deps=False)

    assert success is True
    assert assignments == {"ok": True}
    assert manager._initialization_complete is True
    assert manager._cached_global_assignments == {"ok": True}
    assert manager.import_module_safely.call_count == 2
    manager._import_special_modules.assert_called_once()
