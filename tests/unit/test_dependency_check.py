"""Unit tests for extracted dependency bootstrap orchestrator."""

from unittest.mock import MagicMock

from src.bootstrap.dependency_check import DependencyCheckOrchestrator
from src.bootstrap.package_installer import PackageInstaller


def _build_orchestrator(requirements):
    """Create orchestrator with lightweight mocks for deterministic tests."""
    os_module = MagicMock()
    os_module.getenv.return_value = "false"
    logging_module = MagicMock()
    sys_module = MagicMock()
    subprocess_module = MagicMock()
    installer = PackageInstaller(
        os_module=os_module,
        subprocess_module=subprocess_module,
        sys_module=sys_module,
        logging_module=logging_module,
    )
    installer.find_uv_executable = MagicMock(return_value=(None, None))
    installer.install_uv_with_pip = MagicMock(return_value=False)
    installer.install_with_uv = MagicMock(return_value=False)
    installer.install_with_pip = MagicMock(return_value=True)
    orchestrator = DependencyCheckOrchestrator(
        os_module=os_module,
        logging_module=logging_module,
        sys_module=sys_module,
        package_import_map={},
        parse_requirements_file_fn=lambda: requirements,
        get_installed_version_fn=lambda _name: "",
        version_satisfies_fn=lambda _installed, _spec: False,
        get_latest_pypi_version_fn=lambda _name: "",
        parse_version_fn=lambda _value: (0,),
        installer=installer,
    )
    return orchestrator, installer, os_module


def test_dependency_check_installs_missing_packages() -> None:
    """Missing package path triggers install attempts via pip fallback."""
    orchestrator, installer, _os_module = _build_orchestrator([("pkg-one", "pkg-one>=1.0")])
    orchestrator.run()
    assert installer.install_with_pip.called


def test_dependency_check_skips_when_disabled() -> None:
    """DISABLE_AUTO_INSTALL=true short-circuits orchestration."""
    orchestrator, installer, os_module = _build_orchestrator([("pkg-one", "pkg-one>=1.0")])
    os_module.getenv.side_effect = lambda key, default="": "true" if key == "DISABLE_AUTO_INSTALL" else default
    orchestrator.run()
    assert not installer.install_with_pip.called
