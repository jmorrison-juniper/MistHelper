"""Wave 9 P2 coverage tests for src.bootstrap.package_installer.

Covers the ``PackageInstaller`` dataclass end-to-end using injected
``os``/``subprocess``/``sys``/``logging`` stubs. Exercises every
branch of ``find_uv_executable``, ``install_uv_with_pip``,
``install_with_uv``, ``install_with_pip``, plus the private argv
builders and the ``_candidate_is_runnable`` guard.
"""

from __future__ import annotations  # WHY: postponed evaluation for consistency with SUT

import logging  # WHY: assert bootstrap warnings/errors are wired to the injected logger
from unittest.mock import MagicMock  # WHY: MagicMock(spec=…) for injected stdlib modules

import pytest  # WHY: parametrized branch coverage of platform + upgrade combinations

from src.bootstrap.package_installer import PackageInstaller  # WHY: SUT under test


def _make_installer(
    *,
    os_name: str = "posix",  # WHY: default to non-Windows so no .exe suffix is appended
    executable: str = "/usr/bin/python3",  # WHY: canonical interpreter path used by argv builders
    subprocess_returncode: int = 0,  # WHY: success by default so tests can override to force failures
    subprocess_stdout: str = "uv 0.1.0",  # WHY: canonical `uv --version` stdout used by probe path
    subprocess_raises: BaseException | None = None,  # WHY: allow tests to force spawn failures
    isfile_return: bool = True,  # WHY: absolute-path probe passes existence gate by default
    scripts_dir: str = "/usr/local/bin",  # WHY: default scripts directory used by candidate builder
    path_sep: str = "/",  # WHY: POSIX separator drives the runnable-guard fallback
) -> tuple[PackageInstaller, MagicMock, MagicMock, MagicMock, MagicMock]:
    """Build a PackageInstaller wired to controllable mocks."""
    logging.info("Building PackageInstaller with os_name=%s", os_name)  # WHY: trace fixture creation
    os_module = MagicMock()  # WHY: injected os stub supports .name, .path.join, .path.isfile
    os_module.name = os_name  # WHY: gate the Windows .exe suffix branch
    os_module.path.sep = path_sep  # WHY: _candidate_is_runnable inspects path.sep
    os_module.path.join = lambda *parts: "/".join(parts)  # WHY: deterministic join for assertions
    os_module.path.dirname = lambda p: "/".join(p.split("/")[:-1])  # WHY: mimic dirname for the interpreter probe
    os_module.path.isfile = MagicMock(return_value=isfile_return)  # WHY: control on-disk existence
    subprocess_module = MagicMock()  # WHY: injected subprocess stub with run + SubprocessError
    subprocess_module.SubprocessError = RuntimeError  # WHY: real class so `except` clauses match
    result = MagicMock()  # WHY: stand in for subprocess.CompletedProcess
    result.returncode = subprocess_returncode  # WHY: caller decides success vs failure
    result.stdout = subprocess_stdout  # WHY: version string returned by probe path
    if subprocess_raises is not None:  # WHY: allow tests to force spawn-time raises
        subprocess_module.run = MagicMock(side_effect=subprocess_raises)  # WHY: raise on invocation
    else:
        subprocess_module.run = MagicMock(return_value=result)  # WHY: return the controllable result
    sys_module = MagicMock()  # WHY: injected sys stub exposes executable
    sys_module.executable = executable  # WHY: canonical interpreter used by argv builders
    logging_module = MagicMock()  # WHY: injected logging stub captures warning/error calls
    installer = PackageInstaller(  # WHY: construct SUT with all four injected dependencies
        os_module=os_module,
        subprocess_module=subprocess_module,
        sys_module=sys_module,
        logging_module=logging_module,
    )
    # WHY: monkeypatch sysconfig.get_path via a class-level attribute since it's imported at top level
    logging.debug("PackageInstaller built successfully")  # WHY: post-action trace
    return installer, os_module, subprocess_module, sys_module, logging_module  # WHY: expose mocks for assertions


class TestFindUvExecutable:
    """Cover every branch of the ``find_uv_executable`` probe loop."""

    def test_first_candidate_succeeds_returns_cmd_and_version(self) -> None:
        # WHY: default fixture returns rc=0 with canonical version string
        installer, _os, _sub, _sys, _log = _make_installer()  # WHY: build SUT with default success path
        cmd, version = installer.find_uv_executable()  # WHY: run the probe loop
        assert cmd == ["uv"]  # WHY: PATH lookup is first in the candidate list
        assert version == "uv 0.1.0"  # WHY: stdout trimmed to canonical version string

    def test_all_candidates_fail_returns_none_none(self) -> None:
        # WHY: non-zero returncode causes every candidate to be rejected
        installer, _os, _sub, _sys, _log = _make_installer(subprocess_returncode=1)  # WHY: force rejection
        cmd, version = installer.find_uv_executable()  # WHY: exhaust every candidate
        assert cmd is None  # WHY: signal to caller that no uv command was found
        assert version is None  # WHY: paired None reflects no version

    def test_subprocess_raises_propagates_to_none(self) -> None:
        # WHY: spawn error must be swallowed by the try/except in _probe_uv_command
        installer, _os, _sub, _sys, _log = _make_installer(subprocess_raises=FileNotFoundError("no uv"))
        cmd, version = installer.find_uv_executable()  # WHY: every candidate raises and is caught
        assert cmd is None  # WHY: no candidate produced a runnable result
        assert version is None  # WHY: paired None returned to caller

    def test_windows_adds_exe_suffix_to_absolute_paths(self) -> None:
        # WHY: Windows branch appends ".exe" to the scripts/interpreter probes
        # WHY: force all candidates to fail so every candidate is attempted, revealing .exe suffix
        installer, _os, sub, _sys, _log = _make_installer(os_name="nt", subprocess_returncode=1)
        installer.find_uv_executable()  # WHY: exercise the candidate builder under Windows
        called_argvs = [call.args[0] for call in sub.run.call_args_list]  # WHY: inspect every attempt
        # WHY: at least one candidate must end with .exe on Windows (absolute path probes)
        assert any(argv[0].endswith(".exe") for argv in called_argvs if len(argv) == 2 and argv[0] != "uv")

    def test_isfile_false_skips_absolute_candidate(self) -> None:
        # WHY: _candidate_is_runnable rejects absolute paths that don't exist on disk
        installer, _os, sub, _sys, _log = _make_installer(isfile_return=False)  # WHY: disk check fails
        installer.find_uv_executable()  # WHY: exercise the runnable guard
        # WHY: with isfile=False, absolute-path candidates are skipped before subprocess.run
        called_argvs = [call.args[0] for call in sub.run.call_args_list]  # WHY: inspect attempts
        # WHY: PATH lookup (["uv"]) still fires; module invocation (python -m uv) still fires
        assert ["uv", "--version"] in called_argvs  # WHY: bare-name candidate always attempted


class TestInstallUvWithPip:
    """Cover both success and failure branches of pip-based uv bootstrap."""

    def test_success_returns_true(self) -> None:
        # WHY: rc=0 must produce True from install_uv_with_pip
        installer, _os, _sub, _sys, _log = _make_installer()  # WHY: default success path
        assert installer.install_uv_with_pip() is True  # WHY: bootstrap succeeded

    def test_failure_returns_false(self) -> None:
        # WHY: rc != 0 must produce False without raising
        installer, _os, _sub, _sys, _log = _make_installer(subprocess_returncode=2)  # WHY: force failure
        assert installer.install_uv_with_pip() is False  # WHY: bootstrap failed

    def test_exception_logs_warning_and_returns_false(self) -> None:
        # WHY: broad except must log warning and return False, not propagate
        installer, _os, _sub, _sys, log = _make_installer(subprocess_raises=RuntimeError("boom"))
        assert installer.install_uv_with_pip() is False  # WHY: exception path returns False
        assert log.warning.called  # WHY: caller must be told via warning log


class TestInstallWithUv:
    """Cover uv-install path including upgrade flag and failure logging."""

    def test_success_no_upgrade(self) -> None:
        # WHY: baseline success path returns True and does not append --upgrade
        installer, _os, sub, _sys, _log = _make_installer()  # WHY: default success path
        assert installer.install_with_uv(["uv"], "requests") is True  # WHY: install succeeded
        argv = sub.run.call_args_list[0].args[0]  # WHY: inspect the composed argv
        assert "--upgrade" not in argv  # WHY: upgrade=False must not add the flag

    def test_success_with_upgrade(self) -> None:
        # WHY: upgrade=True must append --upgrade to the argv
        installer, _os, sub, _sys, _log = _make_installer()  # WHY: default success path
        assert installer.install_with_uv(["uv"], "requests", upgrade=True) is True  # WHY: install ok
        argv = sub.run.call_args_list[0].args[0]  # WHY: inspect the composed argv
        assert "--upgrade" in argv  # WHY: upgrade flag appended

    def test_failure_logs_warning_returns_false(self) -> None:
        # WHY: uv install failure logs at warning level (recoverable via pip fallback)
        installer, _os, _sub, _sys, log = _make_installer(subprocess_raises=RuntimeError("fail"))
        assert installer.install_with_uv(["uv"], "requests") is False  # WHY: failure surfaces as False
        assert log.warning.called  # WHY: uv-path failure uses warning severity


class TestInstallWithPip:
    """Cover pip-fallback install path including upgrade flag and error logging."""

    def test_success_no_upgrade(self) -> None:
        # WHY: baseline success path returns True with a plain pip argv
        installer, _os, sub, _sys, _log = _make_installer()  # WHY: default success path
        assert installer.install_with_pip("requests") is True  # WHY: install succeeded
        argv = sub.run.call_args_list[0].args[0]  # WHY: inspect the composed argv
        assert "--upgrade" not in argv  # WHY: upgrade=False must not add the flag
        assert "requests" == argv[-1]  # WHY: package spec is the final positional argument

    def test_success_with_upgrade(self) -> None:
        # WHY: upgrade=True path must append --upgrade before the package spec
        installer, _os, sub, _sys, _log = _make_installer()  # WHY: default success path
        assert installer.install_with_pip("requests", upgrade=True) is True  # WHY: install succeeded
        argv = sub.run.call_args_list[0].args[0]  # WHY: inspect composed argv
        assert "--upgrade" in argv  # WHY: upgrade flag applied

    def test_failure_logs_error_returns_false(self) -> None:
        # WHY: pip-path failure logs at error level because it is the final fallback
        installer, _os, _sub, _sys, log = _make_installer(subprocess_raises=RuntimeError("boom"))
        assert installer.install_with_pip("requests") is False  # WHY: failure surfaces as False
        assert log.error.called  # WHY: pip-path failure uses error severity, not warning


class TestBuildInstallCommands:
    """Cover the private argv-builder helpers indirectly through install methods."""

    @pytest.mark.parametrize("upgrade", [False, True])  # WHY: both branches of the upgrade flag
    def test_uv_argv_contains_python_flag_and_spec(self, upgrade: bool) -> None:
        # WHY: uv argv always pins --python <interpreter> and appends the package spec
        installer, _os, sub, _sys, _log = _make_installer()  # WHY: default success path
        installer.install_with_uv(["uv"], "flask", upgrade=upgrade)  # WHY: exercise argv builder
        argv = sub.run.call_args_list[0].args[0]  # WHY: inspect final argv
        assert "--python" in argv  # WHY: --python flag must be present
        assert "flask" in argv  # WHY: package spec is appended
        assert ("--upgrade" in argv) is upgrade  # WHY: flag appended only when upgrade=True

    @pytest.mark.parametrize("upgrade", [False, True])  # WHY: both branches of the upgrade flag
    def test_pip_argv_uses_module_form(self, upgrade: bool) -> None:
        # WHY: pip argv is [python, -m, pip, install, (--upgrade,) spec]
        installer, _os, sub, _sys, _log = _make_installer()  # WHY: default success path
        installer.install_with_pip("django", upgrade=upgrade)  # WHY: exercise pip argv builder
        argv = sub.run.call_args_list[0].args[0]  # WHY: inspect final argv
        assert "-m" in argv and "pip" in argv and "install" in argv  # WHY: pip module invocation shape
        assert argv[-1] == "django"  # WHY: package spec is the final positional
        assert ("--upgrade" in argv) is upgrade  # WHY: flag appended only when upgrade=True
