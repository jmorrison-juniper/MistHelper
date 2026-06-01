"""Early dependency bootstrap orchestrator extracted from MistHelper.py."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.bootstrap.package_installer import PackageInstaller


@dataclass
class DependencyCheckOrchestrator:
    """Run early dependency verification and install/upgrade missing packages."""

    os_module: Any
    logging_module: Any
    sys_module: Any
    package_import_map: dict[str, str]
    parse_requirements_file_fn: Callable[[], list[tuple[str, str]]]
    get_installed_version_fn: Callable[[str], str]
    version_satisfies_fn: Callable[[str, str], bool]
    get_latest_pypi_version_fn: Callable[[str], str]
    parse_version_fn: Callable[[str], tuple[int, ...]]
    installer: PackageInstaller

    def run(self) -> None:
        """Execute dependency checks and perform best-effort remediation."""
        if self._is_auto_install_disabled():
            self.logging_module.debug("Early dependency auto-install disabled via DISABLE_AUTO_INSTALL")
            return
        all_packages = self.parse_requirements_file_fn()
        if not all_packages:
            self.logging_module.warning("No packages found in requirements.txt - skipping dependency check")
            return
        missing_packages, outdated_packages = self._classify_packages(all_packages)
        if not missing_packages and not outdated_packages:
            self.logging_module.debug("All %s dependencies present and up-to-date", len(all_packages))
            return
        use_uv, uv_cmd = self._prepare_installer()
        self._install_missing_packages(missing_packages, use_uv, uv_cmd)
        self._upgrade_outdated_packages(outdated_packages, use_uv, uv_cmd)

    def _is_auto_install_disabled(self) -> bool:
        """Return True when early auto-install behavior is disabled."""
        return self.os_module.getenv("DISABLE_AUTO_INSTALL", "false").lower() == "true"

    def _is_auto_upgrade_enabled(self) -> bool:
        """Return True when latest-version checks should be performed."""
        return (
            self.os_module.getenv(
                "AUTO_UPGRADE_TO_LATEST",
                self.os_module.getenv("AUTO_UPGRADE_DEPENDENCIES", "true"),
            ).lower()
            == "true"
        )

    def _classify_packages(
        self,
        all_packages: list[tuple[str, str]],
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str, str]]]:
        """Split packages into missing and outdated buckets."""
        missing_packages: list[tuple[str, str]] = []
        outdated_packages: list[tuple[str, str, str]] = []
        auto_upgrade = self._is_auto_upgrade_enabled()
        for package_name, package_spec in all_packages:
            import_name = self.package_import_map.get(package_name.lower(), package_name)
            if not import_name:
                continue
            try:
                __import__(import_name)
                installed_version = self.get_installed_version_fn(package_name)
                if installed_version and not self.version_satisfies_fn(installed_version, package_spec):
                    outdated_packages.append((package_name, package_spec, installed_version))
                    continue
                if auto_upgrade and installed_version:
                    latest = self.get_latest_pypi_version_fn(package_name)
                    if latest and self.parse_version_fn(latest) > self.parse_version_fn(installed_version):
                        outdated_packages.append((package_name, package_spec, installed_version))
            except ImportError:
                missing_packages.append((package_name, package_spec))
        return missing_packages, outdated_packages

    def _prepare_installer(self) -> tuple[bool, list[str] | None]:
        """Resolve preferred installer and bootstrap UV when needed."""
        use_uv = False
        uv_cmd, uv_version = self.installer.find_uv_executable()
        if uv_cmd:
            use_uv = True
            self.logging_module.info("UV package manager detected: %s (cmd: %s)", uv_version, " ".join(uv_cmd))
            return use_uv, uv_cmd
        self.logging_module.info("UV package manager not found in PATH or Python environment")
        self.logging_module.info("Attempting to install UV package manager with pip...")
        if self.installer.install_uv_with_pip():
            uv_cmd, uv_version = self.installer.find_uv_executable()
            if uv_cmd:
                use_uv = True
                self.logging_module.info("UV verified after install: %s (cmd: %s)", uv_version, " ".join(uv_cmd))
        return use_uv, uv_cmd

    def _install_missing_packages(
        self,
        missing_packages: list[tuple[str, str]],
        use_uv: bool,
        uv_cmd: list[str] | None,
    ) -> None:
        """Install missing packages from requirements."""
        if not missing_packages:
            return
        self.logging_module.info("Attempting to auto-install %s missing dependencies...", len(missing_packages))
        for _, package_spec in missing_packages:
            installed = False
            if use_uv and uv_cmd:
                self.logging_module.info("Installing %s with UV...", package_spec)
                installed = self.installer.install_with_uv(uv_cmd, package_spec, upgrade=False)
            if not installed:
                self.logging_module.info("Installing %s with pip...", package_spec)
                installed = self.installer.install_with_pip(package_spec, upgrade=False)
            if installed:
                self.logging_module.info("Successfully installed %s", package_spec)
            else:
                self.logging_module.error("Failed to install %s", package_spec)

    def _upgrade_outdated_packages(
        self,
        outdated_packages: list[tuple[str, str, str]],
        use_uv: bool,
        uv_cmd: list[str] | None,
    ) -> None:
        """Upgrade outdated packages from requirements."""
        if not outdated_packages:
            return
        self.logging_module.info("Attempting to upgrade %s outdated dependencies...", len(outdated_packages))
        for package_name, package_spec, installed_version in outdated_packages:
            upgraded = False
            if use_uv and uv_cmd:
                self.logging_module.info("Upgrading %s from %s with UV...", package_name, installed_version)
                upgraded = self.installer.install_with_uv(uv_cmd, package_spec, upgrade=True)
            if not upgraded:
                self.logging_module.info("Upgrading %s from %s with pip...", package_name, installed_version)
                upgraded = self.installer.install_with_pip(package_spec, upgrade=True)
            if upgraded:
                self.logging_module.info("Successfully upgraded %s", package_name)
            else:
                self.logging_module.error("Failed to upgrade %s", package_name)
