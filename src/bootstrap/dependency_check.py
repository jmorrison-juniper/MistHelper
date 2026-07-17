"""Early dependency bootstrap orchestrator extracted from MistHelper.py."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing

from collections.abc import Callable  # WHY: Type hint for injected pure-function collaborators
from dataclasses import dataclass  # WHY: Bundle wide constructor + install-context state
from typing import Any  # WHY: Injected stdlib modules are Any-typed for testability

from src.bootstrap.package_installer import PackageInstaller  # WHY: UV/pip installer collaborator

_ENV_DISABLE_AUTO_INSTALL = "DISABLE_AUTO_INSTALL"  # WHY: Env var toggling auto-install off
_ENV_AUTO_UPGRADE_LATEST = "AUTO_UPGRADE_TO_LATEST"  # WHY: Preferred env for latest-version upgrades
_ENV_AUTO_UPGRADE_DEPS = "AUTO_UPGRADE_DEPENDENCIES"  # WHY: Legacy env fallback for upgrade toggle
# Feature 1020: explicit opt-in to install into a non-isolated (system) Python; default is fail-closed.
_ENV_ALLOW_SYSTEM_PYTHON_INSTALL = "MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL"  # WHY: override for system-Python installs
_ENV_VIRTUAL_ENV = "VIRTUAL_ENV"  # WHY: set by venv activation; used only to pick the diagnostic message text

_FLAG_TRUE = "true"  # WHY: Case-normalized truthy sentinel for env flags
_FLAG_FALSE = "false"  # WHY: Case-normalized falsy sentinel for env-flag defaults

_MSG_DISABLED = "Early dependency auto-install disabled via DISABLE_AUTO_INSTALL"  # WHY: Debug log
# Feature 1020: fail-closed diagnostics when the active interpreter is not an isolated virtual environment.
_MSG_SYSTEM_PYTHON_NO_VENV = (  # WHY: Warn log - no venv was ever created/activated (VIRTUAL_ENV unset)
    "Refusing to auto-install dependencies into system Python: no virtual environment is active "
    "(sys.prefix == sys.base_prefix and no .venv detected). Create and activate one "
    "(python -m venv .venv) or set MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL=true to override"
)
_MSG_SYSTEM_PYTHON_BROKEN_VENV = (  # WHY: Warn log - a .venv appears configured but its launcher is not active
    "Refusing to auto-install dependencies into system Python: a virtual environment appears configured "
    "(VIRTUAL_ENV is set) but its launcher is not active (sys.prefix == sys.base_prefix). Recreate/repair "
    "the .venv, or set MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL=true to override"
)
_MSG_SYSTEM_PYTHON_OVERRIDE = (  # WHY: Loud warn log - operator explicitly opted into system-Python installs
    "MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL is set: proceeding with dependency install/upgrade into a "
    "non-isolated (system) Python interpreter - this can modify the base environment"
)
_MSG_NO_REQS = "No packages found in requirements.txt - skipping dependency check"  # WHY: Warn log
_MSG_ALL_OK = "All %s dependencies present and up-to-date"  # WHY: Debug log when nothing to do
_MSG_UV_FOUND = "UV package manager detected: %s (cmd: %s)"  # WHY: Info log for first-pass UV find
_MSG_UV_MISSING = "UV package manager not found in PATH or Python environment"  # WHY: Info log
_MSG_UV_INSTALL_TRY = "Attempting to install UV package manager with pip..."  # WHY: Info log
_MSG_UV_VERIFIED = "UV verified after install: %s (cmd: %s)"  # WHY: Info log post-bootstrap
_MSG_INSTALL_MISSING = "Attempting to auto-install %s missing dependencies..."  # WHY: Info log
_MSG_INSTALL_UV = "Installing %s with UV..."  # WHY: Info log per-package UV install attempt
_MSG_INSTALL_PIP = "Installing %s with pip..."  # WHY: Info log per-package pip fallback attempt
_MSG_INSTALL_OK = "Successfully installed %s"  # WHY: Info log per-package install success
_MSG_INSTALL_FAIL = "Failed to install %s"  # WHY: Error log per-package install failure
_MSG_UPGRADE_OUTDATED = "Attempting to upgrade %s outdated dependencies..."  # WHY: Info log header
_MSG_UPGRADE_UV = "Upgrading %s from %s with UV..."  # WHY: Info log per-package UV upgrade attempt
_MSG_UPGRADE_PIP = "Upgrading %s from %s with pip..."  # WHY: Info log per-package pip fallback
_MSG_UPGRADE_OK = "Successfully upgraded %s"  # WHY: Info log per-package upgrade success
_MSG_UPGRADE_FAIL = "Failed to upgrade %s"  # WHY: Error log per-package upgrade failure


@dataclass(frozen=True, slots=True)  # WHY: Frozen slotted bundle for immutable install-context state
class _InstallContext:  # WHY: Bundles UV routing flags so wide signatures collapse to one arg
    """Frozen bundle of installer-routing state shared by install/upgrade loops."""

    use_uv: bool  # WHY: Whether the UV path is available for install attempts
    uv_cmd: list[str] | None  # WHY: Resolved UV command list (None when unavailable)


@dataclass  # WHY: Dataclass builds __init__ that preserves the historical kwargs API
class DependencyCheckOrchestrator:  # WHY: Public entry-point object called from MistHelper._early_dep_check
    """Run early dependency verification and install/upgrade missing packages."""

    os_module: Any  # WHY: os stdlib injected for env access + testability
    logging_module: Any  # WHY: logging stdlib injected for progress messages
    sys_module: Any  # WHY: sys stdlib injected for interpreter path introspection
    package_import_map: dict[str, str]  # WHY: pip-name -> import-name resolution table
    parse_requirements_file_fn: Callable[[], list[tuple[str, str]]]  # WHY: Parses requirements.txt
    get_installed_version_fn: Callable[[str], str]  # WHY: Reads installed distribution version
    version_satisfies_fn: Callable[[str, str], bool]  # WHY: Version-spec satisfaction predicate
    get_latest_pypi_version_fn: Callable[[str], str]  # WHY: Queries latest PyPI release version
    parse_version_fn: Callable[[str], tuple[int, ...]]  # WHY: Parses version string to tuple
    installer: PackageInstaller  # WHY: UV/pip installer collaborator

    def run(self) -> None:  # WHY: Sole public method invoked by MistHelper at import time
        """Execute dependency checks and perform best-effort remediation."""
        if self._is_auto_install_disabled():  # WHY: Short-circuit when explicitly disabled
            self.logging_module.debug(_MSG_DISABLED)  # WHY: Debug log so operators can audit skips
            return  # WHY: Nothing more to do when disabled
        if not self._install_permitted_for_interpreter():  # WHY: Feature 1020 - block install into system Python
            return  # WHY: Diagnostic already logged; never mutate the base interpreter by default
        all_packages = self.parse_requirements_file_fn()  # WHY: Load the required-package list
        if not all_packages:  # WHY: Empty requirements is not an error - just nothing to do
            self.logging_module.warning(_MSG_NO_REQS)  # WHY: Warn so misconfig is visible in logs
            return  # WHY: No packages to check
        missing, outdated = self._classify_packages(all_packages)  # WHY: Bucket by remediation kind
        if not missing and not outdated:  # WHY: Everything up-to-date, log + exit
            self.logging_module.debug(_MSG_ALL_OK, len(all_packages))  # WHY: Debug summary of noop
            return  # WHY: Nothing to remediate
        context = self._prepare_installer()  # WHY: Resolve UV availability once for both loops
        self._install_missing_packages(missing, context)  # WHY: Fresh installs first
        self._upgrade_outdated_packages(outdated, context)  # WHY: Then upgrades

    def _install_permitted_for_interpreter(self) -> bool:  # WHY: Feature 1020 fail-closed interpreter gate
        """Return True when install/upgrade may proceed for the current interpreter.

        Fails closed for a non-isolated (system) Python: blocks by default and logs an actionable
        diagnostic, unless the operator explicitly opts in via MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL.
        Independent of, and additional to, the DISABLE_AUTO_INSTALL gate checked earlier in run().
        """
        if self._is_running_in_isolated_venv():  # WHY: genuine venv - always permitted, no behavior change
            return True
        if self._is_system_python_install_allowed():  # WHY: explicit operator override for system Python
            self.logging_module.warning(_MSG_SYSTEM_PYTHON_OVERRIDE)  # WHY: loud warn, distinct from routine info
            return True
        self.logging_module.warning(self._non_isolated_diagnostic())  # WHY: surface the block clearly, not silently
        return False  # WHY: fail closed - do not install/upgrade into the base interpreter

    def _is_running_in_isolated_venv(self) -> bool:  # WHY: single boolean predicate, easily unit-tested via DI
        """Return True when the active interpreter is an isolated virtual environment."""
        # WHY: canonical PEP 405 signal - a venv points sys.prefix at the venv dir while base_prefix stays system.
        if self.sys_module.prefix != self.sys_module.base_prefix:
            return True
        # WHY: legacy virtualenv (<20) leaves base_prefix untouched and instead sets sys.real_prefix.
        return getattr(self.sys_module, "real_prefix", None) is not None

    def _is_system_python_install_allowed(self) -> bool:  # WHY: Predicate isolates the override env parse
        """Return True when the operator explicitly opted into system-Python installs."""
        raw = self.os_module.getenv(_ENV_ALLOW_SYSTEM_PYTHON_INSTALL, _FLAG_FALSE)  # WHY: Read env once
        return bool(raw.lower() == _FLAG_TRUE)  # WHY: bool() cast since Any-typed compare

    def _non_isolated_diagnostic(self) -> str:  # WHY: Message-only distinction (research R3), predicate stays simple
        """Pick the diagnostic distinguishing a missing venv from a broken venv launcher."""
        # WHY: VIRTUAL_ENV set while not isolated implies an activated-but-broken launcher fell back to system Python.
        virtual_env = self.os_module.getenv(_ENV_VIRTUAL_ENV, "")  # WHY: read the activation marker once
        if virtual_env:  # WHY: activation happened yet we are not isolated -> launcher looks broken
            return _MSG_SYSTEM_PYTHON_BROKEN_VENV
        return _MSG_SYSTEM_PYTHON_NO_VENV  # WHY: no marker -> no venv was ever created/activated

    def _is_auto_install_disabled(self) -> bool:  # WHY: Predicate isolates DISABLE_AUTO_INSTALL parse
        """Return True when early auto-install behavior is disabled."""
        raw = self.os_module.getenv(_ENV_DISABLE_AUTO_INSTALL, _FLAG_FALSE)  # WHY: Read env once
        return bool(raw.lower() == _FLAG_TRUE)  # WHY: bool() cast since Any-typed compare

    def _is_auto_upgrade_enabled(self) -> bool:  # WHY: Predicate isolates AUTO_UPGRADE parse
        """Return True when latest-version checks should be performed."""
        fallback = self.os_module.getenv(_ENV_AUTO_UPGRADE_DEPS, _FLAG_TRUE)  # WHY: Legacy fallback
        raw = self.os_module.getenv(_ENV_AUTO_UPGRADE_LATEST, fallback)  # WHY: Preferred env first
        return bool(raw.lower() == _FLAG_TRUE)  # WHY: bool() cast since Any-typed compare

    def _classify_packages(  # WHY: Split requirements into install/upgrade buckets
        self,
        all_packages: list[tuple[str, str]],
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str, str]]]:
        """Split packages into missing and outdated buckets."""
        missing: list[tuple[str, str]] = []  # WHY: Accumulator for packages that fail import
        outdated: list[tuple[str, str, str]] = []  # WHY: Accumulator for packages needing upgrade
        auto_upgrade = self._is_auto_upgrade_enabled()  # WHY: Compute once outside the loop
        for name, spec in all_packages:  # WHY: Route each requirement through classification
            self._classify_one(name, spec, auto_upgrade, missing, outdated)  # WHY: Mutates in place
        return missing, outdated  # WHY: Return both buckets to caller

    def _classify_one(  # WHY: Single-package classifier keeps outer loop body one call wide
        self,
        name: str,
        spec: str,
        auto_upgrade: bool,
        missing: list[tuple[str, str]],
        outdated: list[tuple[str, str, str]],
    ) -> None:
        """Classify a single requirement into missing/outdated in-place."""
        import_name = self.package_import_map.get(name.lower(), name)  # WHY: Resolve dist->import
        if not import_name:  # WHY: Empty import means opt-out marker
            return  # WHY: Skip mapped-out packages entirely
        if not self._is_importable(import_name):  # WHY: Missing import triggers fresh install
            missing.append((name, spec))  # WHY: Queue for install path
            return  # WHY: Missing packages skip further version checks
        self._check_installed(name, spec, auto_upgrade, outdated)  # WHY: Route installed packages

    def _is_importable(self, import_name: str) -> bool:  # WHY: Wraps __import__ probe in a bool API
        """Return True when the module name imports successfully."""
        try:
            __import__(import_name)  # WHY: ImportError signals the package is missing
        except ImportError:
            return False  # WHY: Signal caller to enqueue as missing
        return True  # WHY: Import succeeded, package is present

    def _check_installed(  # WHY: Handles installed-package outdated detection separately
        self,
        name: str,
        spec: str,
        auto_upgrade: bool,
        outdated: list[tuple[str, str, str]],
    ) -> None:
        """Route an installed package to outdated when spec/latest indicates a bump."""
        installed = self.get_installed_version_fn(name)  # WHY: Read installed version once
        if not installed:  # WHY: Cannot compare without a version string
            return  # WHY: Skip when we cannot introspect the version
        if not self.version_satisfies_fn(installed, spec):  # WHY: Constraint violation
            outdated.append((name, spec, installed))  # WHY: Queue for upgrade path
            return  # WHY: Constraint-triggered upgrades take priority over latest check
        if auto_upgrade and self._newer_available(name, installed):  # WHY: Optional latest check
            outdated.append((name, spec, installed))  # WHY: Queue newer-available bump

    def _newer_available(self, name: str, installed: str) -> bool:  # WHY: PyPI latest comparator
        """Return True when PyPI has a newer version than installed."""
        latest = self.get_latest_pypi_version_fn(name)  # WHY: Query PyPI once per package
        if not latest:  # WHY: No latest info means no upgrade signal
            return False  # WHY: Fail closed - no signal, no upgrade
        return self.parse_version_fn(latest) > self.parse_version_fn(installed)  # WHY: Tuple compare

    def _prepare_installer(self) -> _InstallContext:  # WHY: Builds one _InstallContext for both loops
        """Resolve preferred installer and bootstrap UV when needed."""
        uv_cmd, uv_version = self.installer.find_uv_executable()  # WHY: First discovery pass
        if uv_cmd:  # WHY: UV already installed and usable
            self.logging_module.info(_MSG_UV_FOUND, uv_version, " ".join(uv_cmd))  # WHY: Announce
            return _InstallContext(use_uv=True, uv_cmd=uv_cmd)  # WHY: Fast-path context ready
        self.logging_module.info(_MSG_UV_MISSING)  # WHY: Announce UV absence
        self.logging_module.info(_MSG_UV_INSTALL_TRY)  # WHY: Announce pip-bootstrap attempt
        return self._bootstrap_uv_via_pip()  # WHY: Delegate the pip-fallback path

    def _bootstrap_uv_via_pip(self) -> _InstallContext:  # WHY: Wraps pip-install-then-reverify flow
        """Attempt to install UV via pip and re-verify the resulting binary."""
        if not self.installer.install_uv_with_pip():  # WHY: pip bootstrap failed
            return _InstallContext(use_uv=False, uv_cmd=None)  # WHY: No UV -> pip-only context
        uv_cmd, uv_version = self.installer.find_uv_executable()  # WHY: Re-check after install
        if not uv_cmd:  # WHY: Bootstrap did not expose a UV binary
            return _InstallContext(use_uv=False, uv_cmd=None)  # WHY: Still pip-only after failure
        self.logging_module.info(_MSG_UV_VERIFIED, uv_version, " ".join(uv_cmd))  # WHY: Confirm ok
        return _InstallContext(use_uv=True, uv_cmd=uv_cmd)  # WHY: UV usable after bootstrap

    def _install_missing_packages(  # WHY: Loop driver for install-side remediation
        self,
        missing: list[tuple[str, str]],
        context: _InstallContext,
    ) -> None:
        """Install missing packages from requirements."""
        if not missing:  # WHY: Nothing to install, skip logging + loop
            return  # WHY: Nothing to install
        self.logging_module.info(_MSG_INSTALL_MISSING, len(missing))  # WHY: Announce install count
        for _name, spec in missing:  # WHY: Attempt install of each missing spec
            self._install_one(spec, context)  # WHY: Per-package install with fallback

    def _install_one(self, spec: str, context: _InstallContext) -> None:  # WHY: UV-then-pip install
        """Install a single spec via UV then pip fallback."""
        installed = self._try_uv_install(spec, context)  # WHY: UV first when available
        if not installed:  # WHY: Fall back to pip when UV missing or UV attempt failed
            self.logging_module.info(_MSG_INSTALL_PIP, spec)  # WHY: Announce pip attempt
            installed = self.installer.install_with_pip(spec, upgrade=False)  # WHY: pip fresh install
        self._log_install_result(spec, installed)  # WHY: Emit success or error log

    def _try_uv_install(self, spec: str, context: _InstallContext) -> bool:  # WHY: Guarded UV install
        """Return True when UV successfully installed the spec."""
        if not context.use_uv:  # WHY: UV route unavailable, skip
            return False  # WHY: Signal pip fallback
        if not context.uv_cmd:  # WHY: Defensive - use_uv implies uv_cmd but keep guard explicit
            return False  # WHY: Signal pip fallback
        self.logging_module.info(_MSG_INSTALL_UV, spec)  # WHY: Announce UV install attempt
        return self.installer.install_with_uv(context.uv_cmd, spec, upgrade=False)  # WHY: Run UV

    def _log_install_result(self, spec: str, installed: bool) -> None:  # WHY: Outcome logger
        """Log install outcome at info or error severity."""
        if installed:  # WHY: Success path emits info-level log
            self.logging_module.info(_MSG_INSTALL_OK, spec)  # WHY: Success info log
            return  # WHY: Success path exits after logging
        self.logging_module.error(_MSG_INSTALL_FAIL, spec)  # WHY: Failure path emits error-level

    def _upgrade_outdated_packages(  # WHY: Loop driver for upgrade-side remediation
        self,
        outdated: list[tuple[str, str, str]],
        context: _InstallContext,
    ) -> None:
        """Upgrade outdated packages from requirements."""
        if not outdated:  # WHY: Nothing to upgrade, skip logging + loop
            return  # WHY: Nothing to upgrade
        self.logging_module.info(_MSG_UPGRADE_OUTDATED, len(outdated))  # WHY: Announce upgrade count
        for name, spec, installed in outdated:  # WHY: Attempt upgrade of each stale package
            self._upgrade_one(name, spec, installed, context)  # WHY: Per-package upgrade

    def _upgrade_one(  # WHY: UV-then-pip upgrade with logging
        self,
        name: str,
        spec: str,
        installed: str,
        context: _InstallContext,
    ) -> None:
        """Upgrade a single spec via UV then pip fallback."""
        upgraded = self._try_uv_upgrade(name, spec, installed, context)  # WHY: UV first when avail
        if not upgraded:  # WHY: Fall back to pip when UV missing or UV attempt failed
            self.logging_module.info(_MSG_UPGRADE_PIP, name, installed)  # WHY: Announce pip upgrade
            upgraded = self.installer.install_with_pip(spec, upgrade=True)  # WHY: pip upgrade attempt
        self._log_upgrade_result(name, upgraded)  # WHY: Emit success or error log

    def _try_uv_upgrade(  # WHY: Guarded UV upgrade path
        self,
        name: str,
        spec: str,
        installed: str,
        context: _InstallContext,
    ) -> bool:
        """Return True when UV successfully upgraded the spec."""
        if not context.use_uv:  # WHY: UV route unavailable, skip
            return False  # WHY: Signal pip fallback
        if not context.uv_cmd:  # WHY: Defensive - use_uv implies uv_cmd but keep guard explicit
            return False  # WHY: Signal pip fallback
        self.logging_module.info(_MSG_UPGRADE_UV, name, installed)  # WHY: Announce UV upgrade
        return self.installer.install_with_uv(context.uv_cmd, spec, upgrade=True)  # WHY: Run UV

    def _log_upgrade_result(self, name: str, upgraded: bool) -> None:  # WHY: Outcome logger
        """Log upgrade outcome at info or error severity."""
        if upgraded:  # WHY: Success path emits info-level log
            self.logging_module.info(_MSG_UPGRADE_OK, name)  # WHY: Success info log
            return  # WHY: Success path exits after logging
        self.logging_module.error(_MSG_UPGRADE_FAIL, name)  # WHY: Failure path emits error-level
