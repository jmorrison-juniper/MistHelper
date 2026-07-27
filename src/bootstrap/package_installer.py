"""Package installation helpers for early dependency bootstrap."""

from __future__ import annotations  # WHY: enable PEP 604 unions and postponed evaluation on 3.9+

import sysconfig  # WHY: locate the interpreter's Scripts/ directory for bundled uv discovery
from dataclasses import dataclass  # WHY: attribute-order dataclass holds injected stdlib modules
from typing import Any  # WHY: injected stdlib modules are duck-typed at call sites

_UV_EXECUTABLE_NAME: str = "uv"  # WHY: name used when probing PATH or interpreter-adjacent locations
_WINDOWS_OS_NAME: str = "nt"  # WHY: os.name value used to gate the ".exe" suffix
_WINDOWS_EXECUTABLE_SUFFIX: str = ".exe"  # WHY: Windows binaries require an .exe suffix
_UV_VERSION_ARG: str = "--version"  # WHY: single argument that both probes uv and returns its version
_UV_VERSION_TIMEOUT: int = 5  # WHY: version probe must be quick; 5s guards a hung binary
_PIP_INSTALL_TIMEOUT: int = 30  # WHY: bounded pip-based uv bootstrap avoids indefinite hangs
_PACKAGE_ACTION_TIMEOUT: int = 60  # WHY: per-package install/upgrade cap keeps startup responsive
_PIP_UPGRADE_FLAG: str = "--upgrade"  # WHY: shared token appended when caller requests an upgrade
_UV_PYTHON_FLAG: str = "--python"  # WHY: uv flag pinning installs to the active interpreter
_UV_PIP_SUBCOMMAND: tuple[str, ...] = ("pip", "install")  # WHY: uv's pip-compatible install path
_PIP_MODULE_ARGS: tuple[str, ...] = ("-m", "pip", "install")  # WHY: run pip via the current interpreter
_UV_MODULE_ARGS: tuple[str, ...] = ("-m", "uv")  # WHY: last-resort uv invocation as a Python module
_UV_INSTALL_TARGET: str = "uv"  # WHY: pip package name used when bootstrapping uv via pip
_LOG_UV_INSTALL_FAILED: str = "Could not install UV: %s"  # WHY: template for pip-based uv install failures
_LOG_UV_ACTION_FAILED: str = "UV package action failed for %s: %s"  # WHY: template for uv install failures
_LOG_PIP_ACTION_FAILED: str = "Pip package action failed for %s: %s"  # WHY: template for pip install failures


@dataclass
class PackageInstaller:  # WHY: collaborator injecting stdlib modules for testability
    """Install and upgrade packages using UV with pip fallback."""

    os_module: Any  # WHY: injected os module for path joins and platform checks
    subprocess_module: Any  # WHY: injected subprocess module used to spawn installer processes
    sys_module: Any  # WHY: injected sys module exposing executable and platform
    logging_module: Any  # WHY: injected logging module used for warning/error diagnostics

    def find_uv_executable(self) -> tuple[list[str] | None, str | None]:  # WHY: public probe returns cmd+version tuple
        """Find an executable UV command and return command + version."""
        for candidate in self._uv_candidate_commands():  # WHY: iterate PATH/interpreter/module probes
            probed = self._probe_uv_command(candidate)  # WHY: try each candidate in priority order
            if probed is not None:  # WHY: return the first working command with its version string
                return probed  # WHY: short-circuit on the first successful uv candidate
        return None, None  # WHY: no candidate responded successfully. Signal absence to caller

    def install_uv_with_pip(self) -> bool:  # WHY: bootstrap uv when no candidate command was found
        """Install UV using pip in the active Python environment."""
        pip_command = [self.sys_module.executable, *_PIP_MODULE_ARGS, _UV_INSTALL_TARGET]  # WHY: bootstrap uv via pip
        try:  # WHY: subprocess.run may raise for a wide range of environment issues
            result = self.subprocess_module.run(  # WHY: capture output so failures can be logged if needed
                pip_command,
                capture_output=True,
                text=True,
                timeout=_PIP_INSTALL_TIMEOUT,
            )
            return bool(result.returncode == 0)  # WHY: cast because result is Any-typed from injected module
        except Exception as error:  # WHY: broad catch protects import-time bootstrap from any failure mode
            self.logging_module.warning(_LOG_UV_INSTALL_FAILED, error)  # WHY: surface without aborting startup
            return False  # WHY: signal failure so caller can fall back to pip directly

    def install_with_uv(  # WHY: uv install path invoked by orchestrator
        self,
        uv_cmd: list[str],
        package_spec: str,
        upgrade: bool = False,
    ) -> bool:
        """Install or upgrade a package with UV."""
        command = self._build_uv_install_command(uv_cmd, package_spec, upgrade)  # WHY: compose full uv argv
        return self._run_install(command, package_spec, _LOG_UV_ACTION_FAILED, warn=True)  # WHY: warn on uv errors

    def install_with_pip(self, package_spec: str, upgrade: bool = False) -> bool:  # WHY: pip fallback path
        """Install or upgrade a package with pip."""
        command = self._build_pip_install_command(package_spec, upgrade)  # WHY: compose pip module argv
        # WHY: pip fallback logs at error level because uv already failed by this point.
        return self._run_install(command, package_spec, _LOG_PIP_ACTION_FAILED, warn=False)

    def _uv_candidate_commands(self) -> list[list[str]]:  # WHY: build ordered probe list once per find_uv call
        """Return uv command candidates in priority order."""
        # WHY: append .exe on Windows so absolute-path probes match the actual binary.
        suffix = _WINDOWS_EXECUTABLE_SUFFIX if self.os_module.name == _WINDOWS_OS_NAME else ""
        candidates: list[list[str]] = [[_UV_EXECUTABLE_NAME]]  # WHY: PATH lookup is fastest and most common
        scripts_dir = sysconfig.get_path("scripts")  # WHY: interpreter's Scripts/bin dir may hold bundled uv
        if scripts_dir:  # WHY: sysconfig can return None for unusual installs. Guard before joining
            # WHY: absolute-path probe against interpreter's Scripts directory.
            candidates.append([self.os_module.path.join(scripts_dir, _UV_EXECUTABLE_NAME + suffix)])
        # WHY: virtualenvs place uv beside the python executable, so probe that directory too.
        python_bin_dir = self.os_module.path.dirname(self.sys_module.executable)
        # WHY: absolute-path probe located next to the interpreter binary.
        candidates.append([self.os_module.path.join(python_bin_dir, _UV_EXECUTABLE_NAME + suffix)])
        candidates.append([self.sys_module.executable, *_UV_MODULE_ARGS])  # WHY: fall back to `python -m uv` last
        return candidates  # WHY: caller iterates and short-circuits on first success

    def _probe_uv_command(self, cmd: list[str]) -> tuple[list[str], str] | None:  # WHY: single-candidate runner
        """Return (cmd, version) if the candidate runs successfully, else None."""
        if not self._candidate_is_runnable(cmd):  # WHY: skip absolute paths that do not exist on disk
            return None  # WHY: unreachable binary cannot be probed. Skip to next candidate
        try:  # WHY: subprocess.run may raise FileNotFoundError/OSError/SubprocessError
            result = self.subprocess_module.run(  # WHY: --version is the cheapest way to confirm uv works
                cmd + [_UV_VERSION_ARG],
                capture_output=True,
                text=True,
                timeout=_UV_VERSION_TIMEOUT,
            )
        except (FileNotFoundError, self.subprocess_module.SubprocessError, OSError):  # WHY: swallow spawn errors
            return None  # WHY: any spawn/runtime error means this candidate is unusable
        if result.returncode != 0:  # WHY: non-zero exit indicates uv rejected the invocation
            return None  # WHY: treat non-zero exit as candidate rejection to try the next probe
        return cmd, result.stdout.strip()  # WHY: strip trailing newline from `uv --version` output

    def _candidate_is_runnable(self, cmd: list[str]) -> bool:  # WHY: cheap on-disk check before spawn
        """Reject absolute-path candidates that do not exist on disk."""
        if len(cmd) != 1:  # WHY: only single-arg absolute paths need existence checks
            return True  # WHY: multi-arg commands (for example python -m uv) always attempt to run
        if self.os_module.path.sep not in cmd[0]:  # WHY: bare names rely on PATH resolution, not disk check
            return True  # WHY: bare executable names are always eligible. PATH resolves them at spawn
        return bool(self.os_module.path.isfile(cmd[0]))  # WHY: skip missing binaries before invoking subprocess

    def _build_uv_install_command(  # WHY: uv argv builder shared by install/upgrade paths
        self,
        uv_cmd: list[str],
        package_spec: str,
        upgrade: bool,
    ) -> list[str]:
        """Compose the full uv pip install argv."""
        command = [*uv_cmd, *_UV_PIP_SUBCOMMAND]  # WHY: begin with uv's pip-compatible entrypoint
        if upgrade:  # WHY: --upgrade is optional and only appended when explicitly requested
            command.append(_PIP_UPGRADE_FLAG)  # WHY: append upgrade flag when the caller requested it
        command.extend([_UV_PYTHON_FLAG, self.sys_module.executable, package_spec])  # WHY: pin interpreter and add spec
        return command  # WHY: caller passes this to subprocess.run

    def _build_pip_install_command(self, package_spec: str, upgrade: bool) -> list[str]:  # WHY: pip argv builder
        """Compose the full python -m pip install argv."""
        command = [self.sys_module.executable, *_PIP_MODULE_ARGS]  # WHY: invoke pip via the current interpreter
        if upgrade:  # WHY: --upgrade is optional and only appended when explicitly requested
            command.append(_PIP_UPGRADE_FLAG)  # WHY: append upgrade flag when the caller requested it
        command.append(package_spec)  # WHY: final positional argument is the package spec
        return command  # WHY: caller passes this to subprocess.run

    def _run_install(  # WHY: shared runner drives both uv and pip install paths
        self,
        command: list[str],
        package_spec: str,
        log_template: str,
        warn: bool,
    ) -> bool:
        """Run an install command, log failures via the given template, and coerce result to bool."""
        try:  # WHY: injected subprocess may raise any exception at bootstrap time
            # WHY: bounded run keeps import-time bootstrap from stalling on a slow index or hang.
            result = self.subprocess_module.run(
                command,
                capture_output=True,
                text=True,
                timeout=_PACKAGE_ACTION_TIMEOUT,
            )
            return bool(result.returncode == 0)  # WHY: cast because result is Any-typed from injected module
        except Exception as error:  # WHY: broad catch protects import-time bootstrap from any failure mode
            # WHY: warn for uv (recoverable via pip fallback) and error for pip (final failure).
            logger = self.logging_module.warning if warn else self.logging_module.error
            logger(log_template, package_spec, error)  # WHY: emit diagnostic and return failure
            return False  # WHY: signal install failure so caller can fall back or abort
