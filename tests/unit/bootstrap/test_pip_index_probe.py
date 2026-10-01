"""Cover the pip index probe of scripts/bootstrap_worktree.py (issue #2000).

The bootstrap inherits the machine-global pip configuration. An unreachable
index mirror makes pip retry 5 times with a 15 second timeout for each package,
so a 60 second bootstrap costs close to 50 minutes and reads as a hang.

These tests cover the decision that avoids that cost:

- ``PipIndexProbe._parse_index_url``: the global line, the install line, a line
  with no separator, an empty value, and a report that names no index.
- ``PipIndexProbe.reaches``: a host that answers, a host that refuses, and a
  URL that carries no host.
- ``PipIndexProbe.fallback_index``: no configured index, the public index, a
  reachable mirror, and an unreachable mirror.
- ``WorktreeBootstrapper._install_environment``: the retry limits, the index
  override, and the promise that the global pip configuration stays unchanged.

Every test stubs the probe result, so no test opens a real socket to a mirror.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.13.

import logging  # WHY: caplog checks the Caution line that the user reads.
import os  # Keep caller and child environment checks separate.
import socket  # WHY: the reaches test replaces socket.create_connection.
import subprocess  # Build local process results without starting an installer.
from collections.abc import Iterator  # Describe the controlled result and clock sequences.
from contextlib import AbstractContextManager, nullcontext  # Substitute connections without network access.
from itertools import count, repeat  # Supply deterministic clocks and default successful results.
from pathlib import Path, PureWindowsPath  # Prove native and literal Windows argument shapes without Windows IO.
from typing import Any  # WHY: annotate the monkeypatch stub signatures.
from unittest.mock import Mock  # Substitute environment creation without changing a real environment.

import pytest  # WHY: monkeypatch, caplog, and parametrize fixtures.

from scripts import bootstrap_worktree  # Replace external actions at their actual bootstrap boundary.
from scripts.bootstrap_worktree import (  # WHY: direct imports of the code under test.
    PUBLIC_INDEX_URL,
    PipIndexProbe,
    WorktreeBootstrapper,
)

MIRROR_URL = "http://192.168.1.73:3141/root/pypi/+simple/"  # WHY: the URL that issue #2000 measured.


class TestParseIndexUrl:
    """Cover every branch of the pip config report parser."""

    @pytest.mark.parametrize(
        ("report", "expected"),
        [
            ("global.index-url='http://mirror/simple/'", "http://mirror/simple/"),
            ("install.index-url='https://other/simple/'", "https://other/simple/"),
            ('global.index-url="http://quoted/simple/"', "http://quoted/simple/"),
            ("global.index-url=''", None),
            ("global.trusted-host='192.168.1.73'", None),
            ("a line with no separator", None),
            ("", None),
        ],
    )
    def test_parse_index_url(self, report: str, expected: str | None) -> None:
        """The parser returns the index value, or None when the report names none."""
        assert PipIndexProbe._parse_index_url(report) == expected

    def test_the_parser_reads_the_index_among_other_settings(self) -> None:
        """The parser finds the index line inside a full pip config report."""
        report = "\n".join(  # WHY: reproduce the measured report of issue #2000.
            [
                f"global.index-url='{MIRROR_URL}'",
                "global.extra-index-url='https://pypi.org/simple/'",
                "global.trusted-host='192.168.1.73'",
            ]
        )
        assert PipIndexProbe._parse_index_url(report) == MIRROR_URL


class TestReaches:
    """Cover the TCP probe of the index host."""

    def test_a_host_that_answers_reports_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A mirror that accepts the connection stays in use."""

        class FakeConnection:  # WHY: the probe uses the result as a context manager.
            def __enter__(self) -> FakeConnection:
                return self

            def __exit__(self, *args: Any) -> bool:
                return False

        monkeypatch.setattr(socket, "create_connection", lambda *a, **k: FakeConnection())
        assert PipIndexProbe(Path("python")).reaches(MIRROR_URL) is True

    def test_a_host_that_refuses_reports_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A dead mirror reports false, so the caller can choose the public index."""

        def refuse(*args: Any, **kwargs: Any) -> None:
            raise OSError("connection timed out")  # WHY: the measured failure of issue #2000.

        monkeypatch.setattr(socket, "create_connection", refuse)
        assert PipIndexProbe(Path("python")).reaches(MIRROR_URL) is False

    def test_the_probe_uses_the_short_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The probe waits 3 seconds, not the 15 second pip default."""
        recorded: dict[str, Any] = {}

        def record(address: tuple[str, int], timeout: float | None = None) -> None:
            recorded["address"] = address  # WHY: prove the host and the port that the probe used.
            recorded["timeout"] = timeout  # WHY: prove the probe stays cheap.
            raise OSError("refused")

        monkeypatch.setattr(socket, "create_connection", record)
        PipIndexProbe(Path("python")).reaches(MIRROR_URL)
        assert recorded["address"] == ("192.168.1.73", 3141)
        assert recorded["timeout"] == 3.0

    @pytest.mark.parametrize(
        ("url", "expected_port"),
        [("http://mirror/simple/", 80), ("https://mirror/simple/", 443)],
    )
    def test_the_probe_uses_the_scheme_default_port(
        self, monkeypatch: pytest.MonkeyPatch, url: str, expected_port: int
    ) -> None:
        """A URL with no port uses the default port of its scheme."""
        recorded: dict[str, Any] = {}

        def record(address: tuple[str, int], timeout: float | None = None) -> None:
            recorded["address"] = address
            raise OSError("refused")

        monkeypatch.setattr(socket, "create_connection", record)
        PipIndexProbe(Path("python")).reaches(url)
        assert recorded["address"] == ("mirror", expected_port)

    def test_a_url_with_no_host_reports_true(self) -> None:
        """The script never overrides a value that it cannot read."""
        assert PipIndexProbe(Path("python")).reaches("not-a-url") is True


class TestFallbackIndex:
    """Cover the decision that selects the index for one bootstrap run."""

    @staticmethod
    def _probe(monkeypatch: pytest.MonkeyPatch, index_url: str | None, reachable: bool) -> PipIndexProbe:
        """Build a probe with a stubbed configuration read and a stubbed socket."""
        probe = PipIndexProbe(Path("python"))  # WHY: no test starts a real interpreter.
        monkeypatch.setattr(probe, "read_index_url", lambda: index_url)
        monkeypatch.setattr(probe, "reaches", lambda url: reachable)
        return probe

    def test_no_configured_index_needs_no_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The pip default already points at the public index."""
        assert self._probe(monkeypatch, None, True).fallback_index() is None

    @pytest.mark.parametrize(
        "index_url",
        ["https://pypi.org/simple", "https://pypi.org/simple/", "https://files.pythonhosted.org/simple"],
    )
    def test_the_public_index_needs_no_probe(self, monkeypatch: pytest.MonkeyPatch, index_url: str) -> None:
        """A configured public index needs no override and no socket."""
        probe = PipIndexProbe(Path("python"))
        monkeypatch.setattr(probe, "read_index_url", lambda: index_url)

        def fail(url: str) -> bool:
            raise AssertionError("The probe must not open a socket for the public index.")

        monkeypatch.setattr(probe, "reaches", fail)
        assert probe.fallback_index() is None

    def test_a_reachable_mirror_stays_in_use(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A mirror that answers is faster than the public index, so it stays."""
        assert self._probe(monkeypatch, MIRROR_URL, True).fallback_index() is None

    def test_an_unreachable_mirror_selects_the_public_index(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A dead mirror hands the run to the public index."""
        assert self._probe(monkeypatch, MIRROR_URL, False).fallback_index() == PUBLIC_INDEX_URL

    def test_an_unreachable_mirror_prints_a_caution_that_names_the_host(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The user reads a signal word, the host, and the consequence."""
        with caplog.at_level(logging.WARNING, logger="bootstrap_worktree"):
            self._probe(monkeypatch, MIRROR_URL, False).fallback_index()
        message = caplog.text
        assert "Caution:" in message  # WHY: the writing guide demands a signal word.
        assert "192.168.1.73" in message  # WHY: the message must name the unreachable host.
        assert "not changed" in message  # WHY: the message must state that the change is local.


class TestInstallEnvironment:
    """Cover the environment that the pip subprocess reads."""

    def test_the_environment_bounds_the_retries_and_the_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A partly reachable mirror cannot cost 75 seconds for each package."""
        monkeypatch.delenv("PIP_INDEX_URL", raising=False)
        environment = WorktreeBootstrapper(Path("root"))._install_environment()
        assert environment["PIP_RETRIES"] == "1"
        assert environment["PIP_TIMEOUT"] == "15"

    def test_no_override_leaves_the_index_alone(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A reachable mirror keeps its own index setting."""
        monkeypatch.delenv("PIP_INDEX_URL", raising=False)
        bootstrapper = WorktreeBootstrapper(Path("root"))
        assert "PIP_INDEX_URL" not in bootstrapper._install_environment()

    def test_the_override_replaces_the_index_and_drops_the_extra_index(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The override must beat the inherited extra index of the machine."""
        monkeypatch.setenv("PIP_EXTRA_INDEX_URL", "http://192.168.1.73:3141/simple/")
        bootstrapper = WorktreeBootstrapper(Path("root"))
        bootstrapper.index_override = PUBLIC_INDEX_URL
        environment = bootstrapper._install_environment()
        assert environment["PIP_INDEX_URL"] == PUBLIC_INDEX_URL
        assert "PIP_EXTRA_INDEX_URL" not in environment

    def test_the_override_does_not_change_the_process_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The script must not write the global pip configuration of the user."""
        import os  # WHY: read the real process environment for the comparison.

        monkeypatch.delenv("PIP_INDEX_URL", raising=False)
        bootstrapper = WorktreeBootstrapper(Path("root"))
        bootstrapper.index_override = PUBLIC_INDEX_URL
        bootstrapper._install_environment()
        assert "PIP_INDEX_URL" not in os.environ

    class TestUvBootstrap:  # Keep the new contract cases within the existing test hierarchy.
        """Prove installer behavior with local substitutes for every external action."""

        @pytest.fixture
        def offline(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
        ) -> (
            TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun
        ):  # Share one explicitly typed deterministic recorder.
            """Prepare temporary files and reject unplanned processes or connections."""
            logging.info("Preparing the offline bootstrap.")  # Trace fixture setup without printing caller values.
            root = tmp_path / "Worktree with spaces"  # Prove that argument lists preserve complete paths.
            root.mkdir()  # Keep all simulated setup writes outside the real worktree environment.
            offline = TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun(root)  # Keep each case independent.
            offline.setup.prepare_files()  # Give ordinary scenarios both requirement files.
            monkeypatch.setattr(os, "environ", {})  # Remove host settings without retaining real credentials.
            monkeypatch.setattr(bootstrap_worktree, "REPOSITORY_ROOT", root)  # Keep main inside the temporary worktree.
            monkeypatch.setattr(bootstrap_worktree.subprocess, "run", offline.setup.process)  # Start no real process.
            monkeypatch.setattr(bootstrap_worktree.shutil, "which", offline.which)  # Make tool discovery deterministic.
            monkeypatch.setattr(bootstrap_worktree.socket, "create_connection", offline.connect)  # Open no real socket.
            monkeypatch.setattr(bootstrap_worktree.time, "monotonic", lambda: next(offline.clock))  # Remove real waits.
            monkeypatch.setattr(bootstrap_worktree.venv, "EnvBuilder", offline.setup.builder)  # Create no real venv.
            monkeypatch.setattr(bootstrap_worktree.shutil, "rmtree", offline.setup.remove)  # Delete no real venv.
            caplog.set_level(logging.DEBUG, logger="bootstrap_worktree")  # Capture safe source and timing reports.
            logging.debug("Prepared the offline bootstrap.")  # Confirm that all external boundaries have substitutes.
            return offline  # Let tests inspect original child objects as well as their snapshots.

        class TestCommands:  # Separate command and report observations from source-policy tests.
            """Check installer commands and successful reports."""

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            def test_installer_commands(
                self, offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun, installer: str
            ) -> None:  # Observe commands directly, including the permitted pip configuration read.
                """Both files use one selected executable and the explicit worktree interpreter."""
                logging.info("Checking installer command shapes.")  # Trace the offline contract exercise.
                executable = str(offline.root / "UV tools" / "uv")  # Use an independent expected resolved path.
                offline.uv = executable if installer == "uv" else None  # Control absence without inspecting the host.
                target = str(offline.bootstrapper.interpreter)  # Assert the existing virtual environment layout.
                prefix = [target, "-m", "pip", "install"]  # Require interpreter pip when discovery reports absence.
                if installer == "uv":  # Require the resolved executable rather than a second discovery.
                    prefix = [executable, "pip", "install", "--python", target]  # Keep the target explicit.
                names = ["requirements.txt", "requirements-dev.txt"]  # Assert file order independently of the source.
                expected = [[target, "-m", "pip", "config", "list"]]  # Permit discovery but no pip installation retry.
                expected.extend(prefix + ["-r", str(offline.root / name)] for name in names)  # Preserve full paths.
                installed = offline.bootstrapper.install_requirements()  # Exercise real selection and dispatch.
                logging.debug("Recorded %s install attempts.", len(offline.environments))  # Report only the count.
                assert offline.calls == expected  # Reject extra probes, version commands, upgrades, or uv installation.
                assert offline.options[1:] == [{"check": False}, {"check": False}]  # Require visible shell-free output.
                assert offline.discoveries == ["uv"]  # One discovery result must serve both files.
                assert installed == names  # Record only successfully installed files in their original order.
                for child in offline.environments:  # Keep retry limits effective for the absent-uv path.
                    assert child["PIP_RETRIES"] == "1" and child["PIP_TIMEOUT"] == "15"  # Bound pip waits.

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            def test_success_reports(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                installer: str,
            ) -> None:  # Measure reports without waiting or relying on real installation speed.
                """Successful attempts identify the installer and use one-decimal durations."""
                logging.info("Checking successful install reports.")  # Trace before the controlled invocation.
                offline.uv = offline.uv if installer == "uv" else None  # Exercise both documented installer choices.
                offline.clock = iter((0.0, 1.0, 2.26, 3.0, 5.04, 7.06))  # Fix file and total timer boundaries.
                installed = offline.bootstrapper.install_requirements()  # Keep actual reporting under test.
                logging.debug("Completed %s controlled file attempts.", len(installed))  # Confirm success safely.
                assert installed == ["requirements.txt", "requirements-dev.txt"]  # Both attempts must finish first.
                selection = "Using uv for dependency installation."  # Require identification before installation.
                if installer == "pip":  # Absence is the only permitted automatic fallback.
                    selection = "uv is absent. Using pip for dependency installation."  # Require the reason.
                assert selection in caplog.text  # Require an explicit installer choice.
                for name, duration in (("requirements.txt", "1.3"), ("requirements-dev.txt", "2.0")):  # Bound timing.
                    assert f"The {installer} install of {name} took {duration} seconds." in caplog.text  # Time files.
                assert "The install took 7.1 seconds." in caplog.text  # Total timing excludes discovery and the probe.
                assert caplog.text.isascii()  # Keep new bootstrap reports portable across terminal encodings.

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize(
                "platform",
                (("win32", "Scripts", "python.exe"), ("linux", "bin", "python"), ("darwin", "bin", "python")),
            )
            def test_platform_paths(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                monkeypatch: pytest.MonkeyPatch,
                installer: str,
                platform: tuple[str, str, str],
            ) -> None:  # Prove path selection and transport separately.
                """Windows and non-Windows keep the complete worktree interpreter argument."""
                logging.info("Checking platform-specific interpreter paths.")  # Trace before platform substitution.
                name, directory, filename = platform  # Specify the existing layout independently.
                monkeypatch.setattr(bootstrap_worktree.sys, "platform", name)  # Use no host platform assumptions.
                target: Path | PureWindowsPath = offline.bootstrapper.interpreter  # Check the native layout first.
                assert target == offline.root / ".venv" / directory / filename  # Preserve the platform layout.
                if name == "win32":  # Also prove literal backslashes and spaces survive argument transport.
                    target = PureWindowsPath(r"C:\Work tree\.venv\Scripts\python.exe")  # Keep spaces.
                    monkeypatch.setattr(  # Preserve the complete Windows argument.
                        WorktreeBootstrapper, "interpreter", property(lambda self: target)  # Preserve the full target.
                    )
                offline.uv = offline.uv if installer == "uv" else None  # Keep absence as the sole pip-selection reason.
                installed = offline.bootstrapper.install_requirements()  # Run real command construction.
                logging.debug("Checked %s file attempts.", len(installed))  # Report the count.
                assert installed == ["requirements.txt", "requirements-dev.txt"]  # Require both present files.
                assert offline.calls[0][0] == str(target)  # Configuration must also target the worktree interpreter.
                for command in offline.calls[1:]:  # Both installs must retain the complete target argument.
                    assert command[4 if installer == "uv" else 0] == str(target)  # Do not split paths at spaces.

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize(
                "present",
                (("requirements.txt", "requirements-dev.txt"), ("requirements.txt",), ("requirements-dev.txt",), ()),
            )
            def test_missing_files(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                installer: str,
                present: tuple[str, ...],
            ) -> None:  # Observe every file-presence combination without a real package installation.
                """Absent files are skipped and an empty successful run still reports total duration."""
                for name in ("requirements.txt", "requirements-dev.txt"):  # Keep the independent declared order.
                    if name not in present:  # Remove only a local fixture file.
                        logging.info("Removing local requirement fixture %s.", name)  # Trace before deletion.
                        (offline.root / name).unlink()  # Model a worktree that lacks this requirement file.
                        logging.debug("Removed local requirement fixture %s.", name)  # Confirm the safe file name.
                offline.uv = offline.uv if installer == "uv" else None  # Keep both installer paths covered.
                if not present:  # An empty run consumes only its total start and end clock values.
                    offline.clock = iter((0.0, 1.26))  # Require a one-decimal empty-run duration.
                logging.info("Checking present requirement files.")  # Trace before actual dispatch.
                installed = offline.bootstrapper.install_requirements()  # Exercise presence checks and return ordering.
                logging.debug("Installed %s files.", len(installed))  # Count only success.
                assert installed == list(present)  # Return exactly the successful present names.
                assert offline.events == ["config"] + ["install:" + name for name in present]  # Keep file order.
                assert len(offline.calls) == len(present) + 1 and offline.discoveries == ["uv"]  # Discover once.
                if not present:  # No file attempt may hide an empty-run total.
                    assert "The install took 1.3 seconds." in caplog.text  # Keep empty success observable.

            @pytest.mark.parametrize(
                "scenario",
                (([], False, False), ([], True, False), (["--recreate"], True, True), (["--recreate"], False, True)),
            )
            def test_environment_options(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                scenario: tuple[list[str], bool, bool],
            ) -> None:
                """Existing reuse and --recreate keep pip availability and the same virtual environment target."""
                logging.info("Checking environment creation options.")  # Trace before local creation substitutes.
                arguments, existing, recreate = scenario  # Specify command-line and existing-environment decisions.
                if existing:  # Create only a harmless dummy interpreter under the temporary worktree.
                    offline.setup.prepare_files(interpreter=offline.bootstrapper.interpreter)  # Install no Python.
                options = bootstrap_worktree.build_parser().parse_args(arguments)  # Exercise the unchanged parser.
                offline.bootstrapper.create_environment(recreate=options.recreate)  # Exercise actual reuse decisions.
                logging.debug("Checked local environment creation.")  # Confirm the operation without a real venv.
                assert options.recreate is recreate  # Preserve the existing external option.
                expected_deletions = [offline.bootstrapper.venv_dir] if existing and recreate else []  # Fixed target.
                assert offline.setup.deletions == expected_deletions  # Never delete another environment.
                if existing and not recreate:  # Reuse must not instantiate another environment builder.
                    assert offline.setup.builder.call_args is None  # Prove no redundant creation.
                else:  # Both new and recreated environments retain the existing pip seed policy.
                    assert offline.setup.builder.call_args.kwargs == {"with_pip": True, "upgrade_deps": False}  # Seed.
                    assert offline.setup.builder.created_directory == offline.bootstrapper.venv_dir  # Same target.

        class TestIndexes:  # Keep source-policy cases and their local recorder under a compliant parent.
            """Check effective package sources without reading saved configuration."""

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize(
                "scenario",
                [
                    (
                        {},
                        "global.index-url='https://global.example.invalid/simple'\n"
                        "global.extra-index-url='https://extra-one.invalid/simple https://extra-two.invalid/simple'\n",
                        (
                            "https://global.example.invalid/simple",
                            "https://extra-one.invalid/simple https://extra-two.invalid/simple",
                        ),
                    ),
                    (
                        {"PIP_CONFIG_FILE": "caller-pip.cfg", "UV_CONFIG_FILE": "caller-uv.toml", "UV_NO_CONFIG": "0"},
                        "global.index-url='https://global.example.invalid/simple'\n"
                        "global.extra-index-url='https://global-extra.invalid/simple'\n"
                        "install.index-url='https://install.example.invalid/simple'\n"
                        "install.extra-index-url='https://install-one.invalid/simple https://install-two.invalid/simple'\n",
                        (
                            "https://install.example.invalid/simple",
                            "https://install-one.invalid/simple https://install-two.invalid/simple",
                        ),
                    ),
                    (
                        {
                            "PIP_INDEX_URL": "https://caller.invalid/simple",
                            "PIP_EXTRA_INDEX_URL": "https://caller-extra.invalid/simple",
                        },
                        "global.index-url='https://global.example.invalid/simple'\n"
                        "install.index-url='https://install.example.invalid/simple'\n"
                        "install.extra-index-url='https://install-extra.invalid/simple'\n",
                        ("https://caller.invalid/simple", "https://caller-extra.invalid/simple"),
                    ),
                    (
                        {"PIP_INDEX_URL": "https://caller.invalid/simple", "PIP_EXTRA_INDEX_URL": ""},
                        "global.index-url='https://global.example.invalid/simple'\n"
                        "global.extra-index-url='https://global-extra.invalid/simple'\n"
                        "install.extra-index-url='https://install-extra.invalid/simple'\n",
                        ("https://caller.invalid/simple", "https://install-extra.invalid/simple"),
                    ),
                    (
                        {"PIP_INDEX_URL": "", "PIP_EXTRA_INDEX_URL": "https://caller-extra.invalid/simple"},
                        "global.index-url='https://global.example.invalid/simple'\n"
                        "install.index-url='https://install.example.invalid/simple'\n",
                        ("https://install.example.invalid/simple", "https://caller-extra.invalid/simple"),
                    ),
                    (
                        {"PIP_INDEX_URL": "", "PIP_EXTRA_INDEX_URL": ""},
                        "global.index-url='https://global.example.invalid/simple'\n"
                        'global.extra-index-url="https://global-extra.invalid/simple"\n'
                        "install.index-url=''\ninstall.extra-index-url=''\n",
                        ("https://global.example.invalid/simple", "https://global-extra.invalid/simple"),
                    ),
                    (
                        {
                            "UV_INDEX": "https://wrong.invalid/simple",
                            "UV_DEFAULT_INDEX": "https://wrong.invalid/simple",
                            "UV_INDEX_URL": "https://wrong.invalid/simple",
                            "UV_EXTRA_INDEX_URL": "https://wrong.invalid/simple",
                        },
                        "global.extra-index-url='https://extra-one.invalid/simple https://extra-two.invalid/simple'\n",
                        (None, "https://extra-one.invalid/simple https://extra-two.invalid/simple"),
                    ),
                ],
            )
            def test_working_sources(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                installer: str,
                scenario: tuple[dict[str, str], str, tuple[str | None, str | None]],
            ) -> None:  # Compare real child sources with independent precedence expectations.
                """uv preserves effective pip sources while ordinary pip retains its caller and configuration."""
                logging.info("Checking working package sources.")  # Trace without printing source values.
                caller, report, expected = scenario  # Keep primary and extra-source expectations separate.
                caller = offline.configure_sources(caller, report)  # Supply caller and file settings locally.
                offline.uv = offline.uv if installer == "uv" else None  # Exercise both installation paths.
                installed = offline.bootstrapper.install_requirements()  # Use the actual parser and environment mapper.
                logging.debug("Checked %s installed files.", len(installed))  # Report only the observed count.
                assert installed == ["requirements.txt", "requirements-dev.txt"]  # Reject empty-loop source checks.
                assert offline.bootstrapper.index_override is None  # A working source must never force public fallback.
                assert offline.events.count("config") == 1 and len(offline.connections) <= 1  # Keep discovery bounded.
                for child in offline.environments:  # Each present file must receive the same effective source choices.
                    if installer == "uv":  # uv cannot infer the existing pip configuration safely.
                        assert (child.get("UV_INDEX_URL"), child.get("UV_EXTRA_INDEX_URL")) == expected  # Keep sources.
                        assert "UV_INDEX" not in child and "UV_DEFAULT_INDEX" not in child  # Remove competing aliases.
                        assert child["UV_NO_CONFIG"] == "1" and "UV_CONFIG_FILE" not in child  # Keep uv local.
                    else:  # The ordinary pip path must not receive new source or configuration controls.
                        assert all(child[key] == value for key, value in caller.items())  # Keep pip settings.
                assert os.environ == caller  # Source mapping must remain local to installation children.

            @pytest.mark.parametrize(
                "scenario",
                [
                    (
                        "global.index-url='https://global.invalid/simple'\n"
                        "global.extra-index-url='https://global-extra.invalid/simple'\n"
                        "install.index-url='https://install.invalid/simple'\n"
                        "install.extra-index-url='https://install-extra.invalid/simple'\n",
                        "https://global.invalid/simple",
                        {
                            "global.index-url": "https://global.invalid/simple",
                            "global.extra-index-url": "https://global-extra.invalid/simple",
                            "install.index-url": "https://install.invalid/simple",
                            "install.extra-index-url": "https://install-extra.invalid/simple",
                        },
                    ),
                    (
                        "global.index-url=''\ninstall.index-url='https://install.invalid/simple'\n"
                        "global.extra-index-url=\"\"\ninstall.extra-index-url='https://extra.invalid/simple'\n",
                        None,
                        {
                            "global.index-url": "",
                            "install.index-url": "https://install.invalid/simple",
                            "global.extra-index-url": "",
                            "install.extra-index-url": "https://extra.invalid/simple",
                        },
                    ),
                    (
                        "install.index-url='https://install.invalid/simple'\nglobal.index-url='https://global.invalid/simple'\n",
                        "https://install.invalid/simple",
                        {
                            "install.index-url": "https://install.invalid/simple",
                            "global.index-url": "https://global.invalid/simple",
                        },
                    ),
                    (
                        "a line without a separator\nglobal.trusted-host='ignored'\n install.index-url = \"https://install.invalid/simple\"\n",
                        "https://install.invalid/simple",
                        {"install.index-url": "https://install.invalid/simple"},
                    ),
                    ("", None, {}),
                ],
            )
            def test_configuration_snapshot(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                scenario: tuple[str, str | None, dict[str, str]],
            ) -> None:  # Prove the complete snapshot without adding another subprocess read.
                """One configuration read captures four source keys and retains the first primary result."""
                logging.info("Checking configuration source capture.")  # Trace before the controlled read.
                report, expected, settings = scenario  # Keep probe precedence distinct from install precedence.
                offline.configuration = report  # Supply quoted, empty, and unrelated report lines locally.
                probe = PipIndexProbe(offline.bootstrapper.interpreter)  # Exercise the actual run-local probe.
                result = probe.read_index_url()  # Read through the existing interpreter pip command.
                logging.debug("Read one local source report.")  # Keep source values out of test logs.
                assert result == expected  # Preserve first-primary behavior, including an empty first value.
                assert vars(probe).get("source_settings") == settings  # Fail by assertion before the new field exists.
                target = str(offline.bootstrapper.interpreter)  # Keep configuration tied to the worktree.
                assert offline.calls == [[target, "-m", "pip", "config", "list"]]  # Read once.
                read_options = {"check": False, "capture_output": True, "text": True, "timeout": 30}  # Bound discovery.
                assert offline.options == [read_options]  # Preserve the existing read options.
                assert offline.connections == []  # Source capture must not add a connection itself.

            @pytest.mark.parametrize(
                "scenario",
                (
                    (
                        "uv",
                        os.devnull,
                        {
                            "PIP_INDEX_URL": PUBLIC_INDEX_URL,
                            "PIP_EXTRA_INDEX_URL": None,
                            "UV_INDEX": None,
                            "UV_DEFAULT_INDEX": None,
                            "UV_INDEX_URL": PUBLIC_INDEX_URL,
                            "UV_EXTRA_INDEX_URL": None,
                        },
                    ),
                    (
                        "pip",
                        os.devnull,
                        {
                            "PIP_INDEX_URL": PUBLIC_INDEX_URL,
                            "PIP_EXTRA_INDEX_URL": None,
                            "UV_INDEX": None,
                            "UV_DEFAULT_INDEX": None,
                            "UV_INDEX_URL": None,
                            "UV_EXTRA_INDEX_URL": None,
                        },
                    ),
                    (
                        "uv",
                        "nul",
                        {
                            "PIP_INDEX_URL": PUBLIC_INDEX_URL,
                            "PIP_EXTRA_INDEX_URL": None,
                            "UV_INDEX": None,
                            "UV_DEFAULT_INDEX": None,
                            "UV_INDEX_URL": PUBLIC_INDEX_URL,
                            "UV_EXTRA_INDEX_URL": None,
                        },
                    ),
                    (
                        "pip",
                        "nul",
                        {
                            "PIP_INDEX_URL": PUBLIC_INDEX_URL,
                            "PIP_EXTRA_INDEX_URL": None,
                            "UV_INDEX": None,
                            "UV_DEFAULT_INDEX": None,
                            "UV_INDEX_URL": None,
                            "UV_EXTRA_INDEX_URL": None,
                        },
                    ),
                ),
            )
            @pytest.mark.parametrize(
                "caller",
                [
                    {
                        "PIP_INDEX_URL": "https://failed.invalid/simple",
                        "PIP_EXTRA_INDEX_URL": "https://failed-extra.invalid/simple",
                        "UV_INDEX": "https://wrong.invalid/simple",
                        "UV_DEFAULT_INDEX": "https://wrong.invalid/simple",
                        "UV_INDEX_URL": "https://wrong.invalid/simple",
                        "UV_EXTRA_INDEX_URL": "https://wrong-extra.invalid/simple",
                    }
                ],
            )
            def test_public_override(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                monkeypatch: pytest.MonkeyPatch,
                caller: dict[str, str],
                scenario: tuple[str, str, dict[str, str | None]],
            ) -> None:  # Include Windows's null configuration path without using a Windows filesystem.
                """Public fallback removes competing sources and never writes saved configuration."""
                installer, null_device, expected = scenario  # Specify sources independently.
                offline.uv = offline.uv if installer == "uv" else None  # Select one installer for both files.
                caller = offline.configure_sources(caller, saved=True, reachable=False)  # Use saved failed sources.
                monkeypatch.setattr(os, "devnull", null_device)  # Model the child control value for each platform.
                installed = offline.bootstrapper.install_requirements()  # Exercise real fallback and mapping.
                assert installed == ["requirements.txt", "requirements-dev.txt"]  # Reject empty-loop policy checks.
                configuration = caller["PIP_CONFIG_FILE"] if installer == "uv" else null_device  # Keep controls local.
                for child in offline.environments:  # Both files must use the same exclusive override.
                    assert {key: child.get(key) for key in expected} == expected  # Reject every failed source.
                    assert child["PIP_CONFIG_FILE"] == configuration  # Keep controls child-only.
                    if installer == "uv":  # Saved uv files must not restore any source.
                        assert child["UV_NO_CONFIG"] == "1" and "UV_CONFIG_FILE" not in child  # Keep uv local.
                logging.info("Checking unchanged caller and saved settings.")  # Trace before the sentinel read.
                assert os.environ == caller  # No child override may reach the caller.
                saved = Path(caller["PIP_CONFIG_FILE"]).read_text(encoding="utf-8")  # Read the sentinel.
                assert saved == offline.configuration  # Keep saved settings intact.
                logging.debug("Checked unchanged caller and saved settings.")  # Confirm the read without its contents.

            @pytest.mark.parametrize(
                "scenario",
                [
                    pytest.param(("", None, True, None, None), id="absent"),
                    pytest.param(("global.index-url=''\n", None, False, None, None), id="empty"),
                    pytest.param(
                        ("global.index-url='https://pypi.org/simple'\n", None, False, None, None), id="public"
                    ),
                    pytest.param(
                        ("global.index-url='https://files.pythonhosted.org/simple'\n", None, False, None, None),
                        id="public-files",
                    ),
                    pytest.param(("global.index-url='not-a-url'\n", None, False, None, None), id="unusable"),
                    pytest.param(("", OSError("fake-source-password"), False, None, None), id="read-oserror"),
                    pytest.param(
                        ("", subprocess.SubprocessError("fake-source-password"), False, None, None),
                        id="read-process-error",
                    ),
                    pytest.param(
                        (
                            "global.index-url='https://mirror.invalid/simple'\n",
                            None,
                            True,
                            ("mirror.invalid", 443),
                            None,
                        ),
                        id="reachable",
                    ),
                    pytest.param(
                        (
                            "global.index-url='https://mirror.invalid/simple'\n",
                            None,
                            False,
                            ("mirror.invalid", 443),
                            PUBLIC_INDEX_URL,
                        ),
                        id="unreachable",
                    ),
                    pytest.param(
                        (
                            "global.index-url='https://reader:fake-source-password@mirror.invalid/simple'\n",
                            None,
                            True,
                            ("mirror.invalid", 443),
                            None,
                        ),
                        id="credential-host",
                    ),
                    pytest.param(
                        ("global.index-url='file:fake-source-password'\n", None, True, None, None),
                        id="credential-no-host",
                    ),
                ],
            )
            def test_probe_outcomes(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                scenario: tuple[
                    str, OSError | subprocess.SubprocessError | None, bool, tuple[str, int] | None, str | None
                ],
            ) -> None:  # Preserve existing probe decisions and verify safe bootstrap-owned reports.
                """Every invocation reads once, probes at most once, and reports no source credentials."""
                logging.info("Checking bounded package-source discovery.")  # Trace without source URL values.
                report, error, reachable, address, override = scenario  # Keep outcomes independent.
                offline.configuration, offline.configuration_error = report, error  # Use local input.
                offline.reachable = reachable  # Exercise the actual probe's existing decision.
                installed = offline.bootstrapper.install_requirements()  # Install through real command construction.
                logging.debug("Checked %s local file attempts.", len(installed))  # Confirm nonempty observations.
                assert installed == ["requirements.txt", "requirements-dev.txt"]  # Require both files.
                assert offline.events.count("config") == 1  # Installer selection must not add configuration reads.
                expected_connections = [] if address is None else [(address, 3.0)]  # Retain the three-second boundary.
                assert offline.connections == expected_connections  # Reject per-file probes.
                assert offline.bootstrapper.index_override == override  # Preserve every existing edge decision.
                assert "fake-source-password" not in caplog.text  # Never report credentials from URLs or read faults.
                assert caplog.text.isascii()  # Keep new source reports portable.

            class OfflineRun:  # Own the mutable scenario inputs and direct observations.
                """Record installer commands, discovery, connections, clocks, and setup actions."""

                def __init__(self, root: Path) -> None:  # Reset every scenario before its first invocation.
                    """Store independent inputs and observations for one test."""
                    logging.info("Preparing local run records.")  # Trace state creation without secret values.
                    self.root = root  # Keep every requirement path within the temporary worktree.
                    self.bootstrapper = WorktreeBootstrapper(root)  # Exercise the real installation methods.
                    self.uv: str | None = str(root / "UV tools" / "uv")  # Include spaces in the resolved executable.
                    self.configuration = ""  # Keep the default probe free of network actions.
                    self.configuration_error: OSError | subprocess.SubprocessError | None = None  # Model read faults.
                    self.configuration_code = 0  # Permit explicit unreadable configuration scenarios.
                    self.reachable = True  # Retain a working source unless a scenario changes this decision.
                    self.codes: Iterator[int] = repeat(0)  # Model successful installs without real package changes.
                    self.launch_error: OSError | None = None  # Distinguish launch failure from tool absence.
                    self.clock: Iterator[float] = count(100.0, 1.0)  # Make every reported duration repeatable.
                    self.calls: list[list[str]] = []  # Retain complete arguments, including paths with spaces.
                    self.options: list[dict[str, object]] = []  # Detect captured output or shell-based execution.
                    self.environments: list[dict[str, str]] = []  # Retain objects to prevent identity reuse.
                    self.snapshots: list[dict[str, str]] = []  # Detect later changes to an earlier child.
                    self.discoveries: list[str] = []  # Prove once-per-invocation uv selection.
                    self.probe_overrides: list[str | None] = []  # Observe reset before each configuration read.
                    self.connections: list[tuple[tuple[str, int], float]] = []  # Prove bounded probe counts.
                    self.events: list[str] = []  # Observe real main decisions without replacing installation.
                    self.setup = self.Setup(self)  # Own non-install subprocess and filesystem substitutes.
                    logging.debug("Prepared local run records.")  # Confirm an independent empty record set.

                def which(self, name: str) -> str | None:  # Simulate only the tools that bootstrap already uses.
                    """Return controlled executable choices and record each discovery."""
                    logging.info("Recording executable discovery.")  # Avoid reporting caller paths or values.
                    self.discoveries.append(name)  # Count uv separately from the preserved account tools.
                    logging.debug("Recorded discovery for %s.", name)  # Report the safe tool identifier.
                    if name == "uv":  # Only this result can select the preferred installer.
                        return self.uv  # Repeated invocations can deliberately change availability.
                    if name in ("git", "gh"):  # Preserve existing account behavior through local substitutes.
                        return None if name in self.setup.absent_tools else name  # Simulate missing account tools.
                    raise AssertionError("Unexpected executable discovery.")  # Reject added external setup actions.

                def connect(
                    self, address: tuple[str, int], timeout: float
                ) -> AbstractContextManager[None]:  # Make a refused connection distinct from absent configuration.
                    """Record one probe without opening a socket."""
                    logging.info("Recording the local connection decision.")  # Trace the simulated network boundary.
                    self.connections.append((address, timeout))  # Observe the host, port, count, and timeout.
                    logging.debug("Recorded connection outcome %s.", self.reachable)  # Report only a safe decision.
                    if not self.reachable:  # Simulate the existing public-fallback trigger.
                        raise OSError("The simulated mirror did not answer.")  # Keep failure detail credential-free.
                    return nullcontext()  # Support the real probe's context manager without network access.

                def configure_sources(
                    self, caller: dict[str, str], report: str | None = None, saved: bool = False, reachable: bool = True
                ) -> dict[str, str]:  # Prepare source inputs without reading a real configuration file.
                    """Prepare caller settings and an optional saved-configuration sentinel."""
                    logging.info("Preparing local package sources.")  # Trace before source and caller changes.
                    if report is None:  # Public cases save the caller's failed primary and extra sources.
                        primary = caller.get("PIP_INDEX_URL", "")  # Keep caller choices explicit.
                        extra = caller.get("PIP_EXTRA_INDEX_URL", "")  # Preserve the saved extra source.
                        report = f"global.index-url='{primary}'\nglobal.extra-index-url='{extra}'\n"  # Model pip.
                    if saved:  # A sentinel proves that fallback never writes saved configuration.
                        path = self.root / "saved-source.cfg"  # Keep the sentinel within this test's temporary files.
                        logging.info("Writing the local source sentinel.")  # Trace before the temporary write.
                        path.write_text(report, encoding="utf-8")  # Store only the fake configuration report.
                        logging.debug("Wrote the local source sentinel.")  # Report no source URLs.
                        caller = {  # Preserve unrelated values while adding saved-source sentinels.
                            **caller,  # Keep unrelated caller settings.
                            "PIP_CONFIG_FILE": str(path),  # Model saved pip configuration.
                            "UV_CONFIG_FILE": str(path),  # Model saved uv configuration.
                        }
                    os.environ.update(caller)  # Change only the fixture's caller environment.
                    self.configuration, self.reachable = report, reachable  # Supply the controlled read and probe.
                    snapshot = dict(os.environ)  # Include pytest's own harmless per-test marker.
                    logging.debug("Prepared %s caller fields.", len(snapshot))  # Keep source and token values private.
                    return snapshot  # Let tests prove caller isolation after real installation decisions.

                class Setup:  # Separate environment and account substitutes from installer decisions.
                    """Substitute setup actions that must not reach the real worktree or cloud."""

                    def __init__(
                        self, owner: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun
                    ) -> None:  # Keep scenario records explicitly typed.
                        """Prepare creation and non-install process substitutes."""
                        logging.info("Preparing local setup substitutes.")  # Trace safe fixture initialization.
                        self.owner = owner  # Share the scenario's direct observations.
                        self.results: dict[str, int] = {}  # Permit browser, health, and account status scenarios.
                        self.errors: dict[str, OSError | subprocess.SubprocessError] = {}  # Model launch faults.
                        self.absent_tools: set[str] = set()  # Test missing Git and gh without changing PATH.
                        self.account = "jmorrison-juniper"  # Keep the existing repository account contract.
                        self.browser_environment: dict[str, str] | None = None  # Observe browser isolation directly.
                        self.browser_caller = {  # Keep conflicting browser inputs outside assertion functions.
                            "UV_LINK_MODE": "hardlink",  # Challenge the package-only copy setting.
                            "UV_NATIVE_TLS": "0",  # Challenge the old package-only trust setting.
                            "UV_SYSTEM_CERTS": "0",  # Challenge the modern package-only trust setting.
                            "UV_NO_CONFIG": "0",  # Preserve caller configuration controls for the browser.
                            "UV_CONFIG_FILE": "caller-uv.toml",  # Preserve the browser's unrelated configuration value.
                            "PIP_CONFIG_FILE": "caller-pip.cfg",  # Exclude installation-only null configuration.
                        }
                        self.deletions: list[Path] = []  # Prove recreation deletes only the temporary environment.
                        self.builder = Mock()  # Record exact existing EnvBuilder arguments.
                        self.builder.return_value.create.side_effect = self.create  # Create no real environment.
                        self.process = self.ProcessRecorder(self)  # Handle only known bootstrap subprocess shapes.
                        logging.debug("Prepared local setup substitutes.")  # Confirm all substitutes are ready.

                    def prepare_files(
                        self, interpreter: Path | None = None
                    ) -> None:  # Keep local filesystem preparation separate from installer assertions.
                        """Write requirement fixtures or a harmless dummy interpreter."""
                        if interpreter is not None:  # A dummy file proves reuse without creating a real environment.
                            logging.info("Creating the dummy interpreter directory.")  # Trace before the local write.
                            interpreter.parent.mkdir(parents=True)  # Keep the dummy interpreter in its expected layout.
                            logging.debug("Created the dummy interpreter directory.")  # Confirm only local preparation.
                            logging.info("Writing the dummy interpreter.")  # Trace before the fixture file write.
                            interpreter.write_text(  # Create no executable interpreter.
                                "offline dummy\n", encoding="utf-8"  # Start no interpreter or installer.
                            )
                            logging.debug("Wrote one dummy interpreter.")  # Report only a file count.
                            return  # Keep environment-option preparation separate from requirement fixtures.
                        for name in ("requirements.txt", "requirements-dev.txt"):  # Retain the declared file order.
                            logging.info("Writing local requirement fixture %s.", name)  # Trace each temporary write.
                            path = self.owner.root / name  # Keep writes inside the scenario's temporary directory.
                            path.write_text("# Offline requirement fixture.\n", encoding="utf-8")  # Install no package.
                            logging.debug("Wrote local requirement fixture %s.", name)  # Confirm the safe file name.

                    def create(self, directory: Path) -> None:  # Replace EnvBuilder's filesystem operation.
                        """Record environment creation without installing Python or pip."""
                        logging.info("Recording local environment creation.")  # Trace the substituted write.
                        self.owner.events.append("create_environment")  # Prove main creates before installing.
                        self.builder.created_directory = directory  # Retain the actual environment target.
                        logging.debug("Recorded local environment creation.")  # Confirm the creation observation.

                    def remove(self, directory: Path) -> None:  # Never delete a real worktree environment.
                        """Record recreation and remove only a temporary dummy interpreter."""
                        logging.info("Recording local environment deletion.")  # Trace the safe deletion substitute.
                        self.deletions.append(directory)  # Prove the existing --recreate target remains unchanged.
                        self.owner.bootstrapper.interpreter.unlink(missing_ok=True)  # Remove only the fixture file.
                        logging.debug("Recorded local environment deletion.")  # Confirm no real venv was removed.

                    class ProcessRecorder:  # Keep each process dispatcher within the changed-function limits.
                        """Accept known non-install commands and reject every other command."""

                        def __init__(
                            self, setup: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun.Setup
                        ) -> None:  # Keep setup observations explicitly typed.
                            """Store exact existing command shapes and their action names."""
                            logging.info("Preparing the local command allowlist.")  # Trace the bounded dispatch policy.
                            self.setup = setup  # Use the same controlled results as the surrounding scenario.
                            root = str(setup.owner.root)  # Preserve a path with spaces as one argument.
                            self.labels = {  # Match complete argument tails rather than permissive command prefixes.
                                ("-m", "pip", "config", "list"): "config",  # Permit the one configuration read.
                                ("-m", "misthelper_devtools.venv_health"): "check_environment_health",  # Local guard.
                                ("-m", "playwright", "install", "chromium"): "install_browser_driver",  # Fixed browser.
                                ("api", "user", "--jq", ".login"): "warn_on_mismatch",  # Existing account read.
                                (
                                    "-C",  # Keep the account command within the temporary worktree.
                                    root,  # Preserve the complete path with spaces.
                                    "config",  # Permit only the existing account configuration action.
                                    "--local",  # Prevent writes to shared user configuration.
                                    "credential.https://github.com.username",  # Preserve the existing credential key.
                                    "jmorrison-juniper",  # Reject another account during the offline run.
                                ): "configure_git_username",  # Reject another repository or username.
                            }
                            logging.debug(  # Confirm the bounded command allowlist.
                                "Prepared %s permitted setup commands.", len(self.labels)  # Report the bounded scope.
                            )

                        def setup_result(
                            self, command: list[str], environment: dict[str, str] | None, label: str
                        ) -> subprocess.CompletedProcess[str]:  # Model only preserved non-install setup behavior.
                            """Return the configured outcome for a known setup command."""
                            logging.info("Recording local setup action %s.", label)  # Trace the safe action name.
                            owner = self.setup.owner  # Share the direct scenario observations.
                            owner.events.append(label)  # Keep creation and setup order observable.
                            if label in self.setup.errors:  # A simulated launch fault exercises the actual boundary.
                                raise self.setup.errors[label]  # Start no process when the scenario models failure.
                            if label == "config":  # Permit the existing pip discovery read for either installer.
                                owner.probe_overrides.append(owner.bootstrapper.index_override)  # Observe reset.
                                if owner.configuration_error is not None:  # Simulate a discovery read fault.
                                    raise owner.configuration_error  # Exercise the actual probe exception boundary.
                                result = subprocess.CompletedProcess(  # Supply only the local configuration report.
                                    command, owner.configuration_code, owner.configuration, ""  # Supply only fake text.
                                )
                            else:  # Supply only existing browser, health, and account outcomes.
                                if label == "install_browser_driver":  # The browser needs its own environment.
                                    self.setup.browser_environment = environment  # Retain the original child.
                                output = self.setup.account if label == "warn_on_mismatch" else ""  # Fake the login.
                                result = subprocess.CompletedProcess(  # Preserve existing non-install statuses.
                                    command, self.setup.results.get(label, 0), output, "simulated failure"
                                )  # Keep existing status behavior.
                            logging.debug("Recorded status %s.", result.returncode)  # Keep values private.
                            return result  # Let unchanged source methods decide whether setup continues.

                        def install(
                            self, command: list[str], environment: dict[str, str] | None
                        ) -> subprocess.CompletedProcess[str]:  # Record real dispatch at the process boundary.
                            """Record one simulated installation and supply its controlled result."""
                            logging.info("Recording the local install attempt.")  # Trace before fake execution.
                            owner = self.setup.owner  # Keep installer records within this scenario.
                            if environment is None or command[-2] != "-r":  # Reject another installer operation.
                                raise AssertionError("Unexpected installer arguments.")  # Start no unplanned process.
                            path = Path(command[-1])  # Check the target independently of installer selection.
                            if path not in (owner.root / "requirements.txt", owner.root / "requirements-dev.txt"):
                                raise AssertionError("Unexpected requirement file.")  # Keep installs inside this case.
                            owner.environments.append(environment)  # Retain the exact mutable child object.
                            owner.snapshots.append(dict(environment))  # Observe values before a later mutation.
                            owner.events.append("install:" + path.name)  # Prove file order and failure stopping.
                            if owner.launch_error is not None:  # A resolved executable can still fail to start.
                                raise owner.launch_error  # Exercise source handling rather than mock installation.
                            result = subprocess.CompletedProcess(command, next(owner.codes), "", "")  # Local result.
                            logging.debug("Recorded install result %s.", result.returncode)  # Report only status.
                            return result  # Let production code make the success or failure decision.

                        def __call__(
                            self, command: list[str], env: dict[str, str] | None = None, **options: object
                        ) -> subprocess.CompletedProcess[str]:  # Record subprocess options without external actions.
                            """Record each command and return only a permitted local result."""
                            logging.info("Recording a local bootstrap process.")  # Trace before simulated execution.
                            owner = self.setup.owner  # Keep installer and setup order in the same record.
                            owner.calls.append(list(command))  # Preserve full executable and path arguments.
                            owner.options.append(dict(options))  # Observe check, capture, text, timeout, and shell.
                            installing = command[1:4] == ["-m", "pip", "install"] or command[1:3] == ["pip", "install"]
                            if installing:  # Execute only a local installation substitute.
                                result = self.install(command, env)  # Exercise the real install decision.
                            else:  # Permit only the existing configuration, health, browser, and account commands.
                                label = self.labels.get(tuple(command[1:]))  # Reject added commands deterministically.
                                if label is None:  # An unexpected command must never escape the fixture.
                                    raise AssertionError("Unexpected bootstrap process.")  # Start no external action.
                                result = self.setup_result(command, env, label)  # Keep setup real.
                            logging.debug("Recorded local process result %s.", result.returncode)  # Summarize safely.
                            return result  # Let the unchanged production sequence evaluate each result.

                        def configure_check(self, scenario: tuple[str, int, str, str | None, str]) -> None:
                            """Prepare a preserved health or account outcome without real credentials."""
                            logging.info("Preparing the local compatibility outcome.")  # Trace before input changes.
                            action, code, account, failure, _ = scenario  # Separate input from the expected report.
                            self.setup.results[action], self.setup.account = code, account  # Control status and login.
                            if failure == "absent":  # Tool absence must retain the existing nonblocking behavior.
                                tool = "git" if action == "configure_git_username" else "gh"  # Select the absent tool.
                                self.setup.absent_tools.add(tool)  # Start no process for that tool.
                            elif failure == "oserror":  # Simulate a launch fault without a real subprocess.
                                self.setup.errors[action] = OSError("simulated unavailable tool")  # Keep detail safe.
                            elif failure == "process":  # Exercise the existing subprocess-error account boundary.
                                self.setup.errors[action] = subprocess.SubprocessError("simulated failed tool")  # Fail.
                            os.environ.update(  # Test warnings with fake credentials only.
                                {"GH_TOKEN": "fake-health-token", "GITHUB_TOKEN": "fake-account-token"}  # Fake tokens.
                            )
                            logging.debug("Prepared the local outcome for %s.", action)  # Keep values private.

        class TestIsolation:  # Group child and invocation isolation without adding top-level tests.
            """Check child environments and independent later invocations."""

            @pytest.mark.parametrize(
                "caller",
                [
                    {
                        "UV_LINK_MODE": "hardlink",
                        "UV_NATIVE_TLS": "0",
                        "UV_SYSTEM_CERTS": "0",  # Force conflicting values.
                        "UV_HTTP_RETRIES": "5",
                        "UV_HTTP_TIMEOUT": "75",
                        "HTTPS_PROXY": "http://proxy.example.invalid:8080",
                        "SSL_CERT_FILE": "root.pem",  # Preserve trust.
                        "REQUESTS_CA_BUNDLE": "requests.pem",
                        "NODE_OPTIONS": "--max-old-space-size=4096",  # Keep runtime data.
                        "GH_TOKEN": "fake-private-token",
                        "GITHUB_TOKEN": "fake-other-token",  # Keep values private.
                    }
                ],
            )
            def test_uv_child_settings(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                caller: dict[str, str],
            ) -> None:  # Inspect both children rather than trusting a helper's return value.
                """uv gets copy mode and system trust without changing unrelated caller settings."""
                logging.info("Checking uv child settings.")  # Trace environment setup without its values.
                os.environ.update(caller)  # Change only the fixture's substitute caller environment.
                caller = dict(os.environ)  # Include pytest's own harmless per-test marker in the caller snapshot.
                unrelated = {key: value for key, value in caller.items() if not key.startswith("UV_")}  # Keep caller.
                offline.bootstrapper.install_requirements()  # Build real per-file child environments.
                logging.debug("Recorded %s uv child environments.", len(offline.environments))  # Summarize the action.
                assert len(offline.environments) == 2  # Reject an empty-loop success.
                for child in offline.environments:  # Both files must receive the forced settings.
                    assert child["UV_LINK_MODE"] == "copy"  # Avoid hardlinks on worktree storage.
                    assert child["UV_NATIVE_TLS"] == child["UV_SYSTEM_CERTS"] == "1"  # Keep old and modern trust names.
                    assert child["UV_HTTP_RETRIES"] == "1"
                    assert child["UV_HTTP_TIMEOUT"] == "15"
                    assert all(child[key] == value for key, value in unrelated.items())  # Preserve caller values.
                assert os.environ == caller  # Child overrides must not reach the caller.
                tokens = ("fake-private-token", "fake-other-token")  # Use no real credentials.
                assert all(token not in caplog.text for token in tokens)  # Never expose credentials.

            def test_separate_environments(
                self, offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun
            ) -> None:  # Retain original objects so object-ID reuse cannot produce a false pass.
                """A change to one install child affects neither the next child nor the caller."""
                logging.info("Checking independent child environments.")  # Trace before the actual installations.
                caller = {"CUSTOM_SETTING": "unchanged"}  # Use a harmless unrelated caller value.
                os.environ.update(caller)  # Change only the local fixture's caller settings.
                caller = dict(os.environ)  # Include the test runner's own marker before checking isolation.
                offline.bootstrapper.install_requirements()  # Create both real child dictionaries.
                logging.debug("Recorded %s child environments.", len(offline.environments))  # Confirm two observations.
                assert len(offline.environments) == 2  # Prevent an empty-loop isolation pass.
                first, second = offline.environments  # Retain both original objects.
                assert first is not second  # Each requirement file needs a fresh copy.
                logging.info("Changing the first child environment.")  # Trace the deliberate isolation challenge.
                first["CUSTOM_SETTING"] = first["UV_LINK_MODE"] = "changed-first-child"  # Mutate only the first child.
                logging.debug("Changed only the first child environment.")  # Report the mutation without its values.
                assert second == offline.snapshots[1]  # The second child must retain its initial values.
                assert second["CUSTOM_SETTING"] == "unchanged"  # The unrelated caller value must remain available.
                assert os.environ == caller  # Neither install nor later mutation may change the caller.

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize("first_fails", (False, True))
            def test_fresh_invocations(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                installer: str,
                first_fails: bool,
            ) -> None:
                """A reused bootstrapper discards prior installer and index state, including after failure."""
                logging.info("Checking fresh installation invocations.")  # Trace before the first source decision.
                offline.uv = offline.uv if installer == "uv" else None  # Select the first installer.
                offline.configuration = "global.index-url='https://failed.invalid/simple'\n"  # Fail this mirror.
                offline.reachable = False  # Model a dead mirror without a real connection.
                offline.codes = iter((17,)) if first_fails else repeat(0)  # Include an incomplete first invocation.
                failure = pytest.raises(RuntimeError, match="code 17")  # Require actual failure handling.
                context = failure if first_fails else nullcontext()  # Also cover first-run success.
                with context:  # Keep installation methods real.
                    offline.bootstrapper.install_requirements()  # Finish or fail the first actual dispatch path.
                earlier = [dict(child) for child in offline.environments]  # Preserve first-run values independently.
                offline.uv = None if installer == "uv" else str(offline.root / "uv")  # Change availability.
                offline.configuration = "global.index-url='https://working.invalid/simple'\n"  # Keep this mirror.
                offline.reachable, offline.codes = True, repeat(0)  # Let the next invocation succeed.
                installed = offline.bootstrapper.install_requirements()  # Reuse the actual bootstrapper object.
                assert installed == ["requirements.txt", "requirements-dev.txt"]  # Require both files.
                assert offline.discoveries == ["uv", "uv"]  # Discover each invocation.
                assert offline.probe_overrides == [None, None]  # Reset before each read.
                assert len(offline.connections) == 2 and offline.events.count("config") == 2  # Bound probes.
                assert offline.environments[: len(earlier)] == earlier  # A later run must not mutate earlier children.
                expected = "https://working.invalid/simple" if installer == "pip" else None  # Select the later source.
                for child in offline.environments[-2:]:  # Both later files must use only the fresh decision.
                    assert child.get("PIP_INDEX_URL") is None  # Remove stale public mapping.
                    assert child.get("UV_INDEX_URL") == expected  # Reject stale source snapshots.

            @pytest.mark.parametrize("scenario", (("uv", 0), ("uv", 1), ("pip", 0), ("pip", 1)))
            @pytest.mark.parametrize(
                "expected",
                [
                    (
                        "create_environment",
                        "config",
                        "install:requirements.txt",
                        "install:requirements-dev.txt",
                        "check_environment_health",
                        "install_browser_driver",
                        "configure_git_username",
                        "warn_on_mismatch",
                    )
                ],
            )
            def test_successful_main(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                scenario: tuple[str, int],
                expected: tuple[str, ...],
            ) -> None:  # Keep health, browser, readiness, and account actions real behind local process substitutes.
                """Successful dependency installation preserves setup order and nonblocking browser failure."""
                logging.info("Checking successful bootstrap sequencing.")  # Trace before actual main decisions.
                installer, browser_code = scenario  # Specify both preserved outcomes.
                offline.uv = offline.uv if installer == "uv" else None  # Exercise both documented installer choices.
                offline.setup.results["install_browser_driver"] = browser_code  # Preserve nonblocking browser failure.
                result = bootstrap_worktree.main([])  # Start no real installer, browser, Git, or cloud request.
                logging.debug("The local bootstrap returned status %s.", result)  # Confirm the real success decision.
                assert result == 0  # A browser fault must not erase successful dependency setup.
                assert offline.events == list(expected)  # Preserve the complete action sequence.
                assert caplog.text.index("The environment is ready.") < caplog.text.index("Configuring Git credentials")
                assert "Installed requirement files: requirements.txt, requirements-dev.txt" in caplog.text  # Name.
                assert "The active GitHub account is jmorrison-juniper." in caplog.text  # Keep the expected account.
                assert ("A skip reads as a pass." in caplog.text) is (browser_code != 0)  # Preserve the repair report.
                assert offline.discoveries == ["uv", "git", "gh"]  # Discover each tool.

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize(
                "scenario",
                (
                    (None, 0, "--use-system-ca"),
                    (None, 1, "--use-system-ca"),
                    (
                        '--require "C:\\tools\\hook dir\\hook.js"',
                        0,
                        '--require "C:\\tools\\hook dir\\hook.js" --use-system-ca',
                    ),
                    (
                        '--require "C:\\tools\\hook dir\\hook.js"',
                        1,
                        '--require "C:\\tools\\hook dir\\hook.js" --use-system-ca',
                    ),
                    ("--max-old-space-size=4096 --use-system-ca", 0, "--max-old-space-size=4096 --use-system-ca"),
                    ("--max-old-space-size=4096 --use-system-ca", 1, "--max-old-space-size=4096 --use-system-ca"),
                ),
            )
            def test_browser_isolation(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                installer: str,
                scenario: tuple[str | None, int, str],
            ) -> None:  # Inspect the actual browser subprocess environment after a public-index installation.
                """Browser trust retains caller settings and excludes every newly forced installer control."""
                logging.info("Checking browser child isolation.")  # Trace before setup.
                options, code, expected = scenario  # Specify exact Node text independently.
                caller = dict(offline.setup.browser_caller)  # Keep per-case caller values independent.
                if options is not None:  # Preserve caller text, including quoted paths with spaces.
                    caller["NODE_OPTIONS"] = options  # Supply only a local test value.
                report = "global.index-url='https://failed.invalid/simple'\n"  # Model a failed mirror.
                caller = offline.configure_sources(caller, report)  # Preserve caller inputs.
                offline.uv = offline.uv if installer == "uv" else None  # Select the installer.
                offline.reachable = False  # Select public fallback.
                offline.setup.results["install_browser_driver"] = code  # Test successful and failed downloads locally.
                offline.bootstrapper.install_requirements()  # Apply real installer-only overrides first.
                ready = offline.bootstrapper.install_browser_driver()  # Exercise unchanged browser trust and repair.
                logging.debug("Recorded local browser status %s.", ready)  # Report no caller values.
                child = offline.setup.browser_environment  # Inspect the original browser child.
                assert isinstance(child, dict)  # Require an actual environment observation.
                assert all(child[key] == value for key, value in caller.items() if key != "NODE_OPTIONS")  # Retain.
                assert child["NODE_OPTIONS"] == expected  # Preserve quoted paths and existing options exactly.
                assert os.environ == caller  # Neither package nor browser settings may reach the caller.

        class TestFailures:  # Separate installation failures from unchanged nonblocking setup behavior.
            """Check installation stopping and contextual failure reports."""

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize("failed_file", (0, 1))
            def test_nonzero_results(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                installer: str,
                failed_file: int,
            ) -> None:
                """A nonzero result raises with installer, file, and status without another install."""
                logging.info("Checking nonzero installation results.")  # Trace before the controlled failure.
                offline.uv = offline.uv if installer == "uv" else None  # Retain one installer.
                names = ["requirements.txt", "requirements-dev.txt"]  # Specify file order independently of production.
                offline.codes = iter([0] * failed_file + [19])  # Fail exactly the chosen file.
                message = f"The {installer} install of {names[failed_file]} failed with code 19."  # Identify failure.
                with pytest.raises(RuntimeError) as error:  # Installation failure is not a recoverable setup result.
                    offline.bootstrapper.install_requirements()  # Exercise actual dispatch and failure handling.
                logging.debug("Recorded %s failed-run attempts.", len(offline.environments))  # Report only the count.
                assert str(error.value) == message  # Identify the selected installer, failed file, and returned code.
                assert len(offline.environments) == failed_file + 1  # Do not attempt another file after failure.
                assert offline.events == ["config"] + ["install:" + name for name in names[: failed_file + 1]]  # Stop.
                assert offline.discoveries == ["uv"]  # Never rediscover or switch installers after a nonzero result.
                assert len(offline.calls) == failed_file + 2  # Permit one configuration read and no retry.
                for command in offline.calls[1:]:  # Distinguish configuration pip from forbidden pip installation.
                    executable = offline.uv if installer == "uv" else str(offline.bootstrapper.interpreter)  # Fix tool.
                    assert command[0] == executable  # Permit no installer retry.

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize("failed_file", (0, 1))
            def test_main_failure(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                installer: str,
                failed_file: int,
            ) -> None:  # Observe the real main boundary rather than a mocked installation result.
                """A failed file returns status one and suppresses every later setup action."""
                logging.info("Checking failed bootstrap sequencing.")  # Trace before actual main decisions.
                offline.uv = offline.uv if installer == "uv" else None  # Exercise uv and the absence-only pip path.
                names = ["requirements.txt", "requirements-dev.txt"]  # Keep the expected sequence independent.
                offline.codes = iter([0] * failed_file + [19])  # Fail before any later health or browser action.
                result = bootstrap_worktree.main([])  # Substitute external actions, not the implementation under test.
                logging.debug("The local bootstrap returned status %s.", result)  # Confirm the real exit decision.
                assert result == 1  # An incomplete environment must never appear ready.
                assert offline.events == ["create_environment", "config"] + [  # Suppress every later setup action.
                    "install:" + name for name in names[: failed_file + 1]
                ]  # Exclude health, browser, and both account actions.
                assert offline.discoveries == ["uv"]  # Git and gh must remain undiscovered after install failure.
                assert "The environment is ready." not in caplog.text  # Suppress the readiness report.
                assert f"The {installer} install of {names[failed_file]} failed with code 19." in caplog.text  # Name.

            @pytest.mark.parametrize(
                "launch_error",
                (OSError("launch failed"), FileNotFoundError(2, "missing uv"), OSError("fake-launch-secret")),
            )
            def test_uv_launch_failure(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                launch_error: OSError,
                caplog: pytest.LogCaptureFixture,
            ) -> None:
                """A discovered executable that cannot start raises contextual failure without pip retry."""
                logging.info("Checking a discovered uv launch failure.")  # Trace before the fake process fault.
                offline.launch_error = launch_error  # Raise only at the subprocess boundary.
                launch_error.__cause__ = ValueError("fake-chained-secret")
                with pytest.raises(RuntimeError) as error:  # Require explicit installer and file context.
                    offline.bootstrapper.install_requirements()  # Keep discovery, mapping, and dispatch real.
                logging.debug("Recorded %s launch attempts.", len(offline.environments))  # Confirm no retry.
                assert "The uv install of requirements.txt could not start" in str(error.value)  # Give failure context.
                assert type(launch_error).__name__ in str(error.value)  # Report safe launch detail.
                assert error.value.__cause__ is launch_error  # Preserve the original failure for direct callers.
                assert offline.events == ["config", "install:requirements.txt"]  # Stop before the second file.
                assert len(offline.calls) == 2 and offline.calls[1][0] == offline.uv  # Permit no pip installation.
                assert offline.discoveries == ["uv"]  # A launch failure is not executable absence.
                assert "Traceback" in caplog.text and "_run" in caplog.text
                assert "fake-launch-secret" not in caplog.text and "fake-chained-secret" not in caplog.text

            @pytest.mark.parametrize("installer", ("uv", "pip"))
            @pytest.mark.parametrize("failure", ("nonzero", "launch"))
            def test_failed_reports(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                installer: str,
                failure: str,
            ) -> None:  # Control failure clocks and keep fake launch detail out of console reports.
                """Every attempted failure reports one-decimal time but no successful total or readiness."""
                logging.info("Checking failed-attempt reports.")  # Trace before the controlled main invocation.
                offline.uv = offline.uv if installer == "uv" else None  # Retain the selected tool across failure.
                offline.clock = iter((10.0, 12.0, 15.26))  # Require a 3.3-second failed attempt.
                offline.codes = iter((19,))  # Supply a nonzero status unless launch fails first.
                offline.launch_error = OSError("fake-private-token") if failure == "launch" else None  # Test launch.
                result = bootstrap_worktree.main([])  # Exercise the preserved failure-to-exit boundary.
                logging.debug("Recorded failed bootstrap status %s.", result)  # Confirm failure without raw error text.
                assert result == 1  # Failure must propagate to the script caller.
                assert f"The {installer} install of requirements.txt took 3.3 seconds." in caplog.text  # Time failure.
                assert "The install took" not in caplog.text and "The environment is ready." not in caplog.text  # Stop.
                assert "fake-private-token" not in caplog.text  # Never log credential-bearing launch detail.
                assert offline.events == ["create_environment", "config", "install:requirements.txt"]  # Stop setup.

            @pytest.mark.parametrize(
                "scenario",
                (
                    (
                        "check_environment_health",
                        1,
                        "jmorrison-juniper",
                        None,
                        "Checking virtual environment package install records.",
                    ),
                    ("check_environment_health", 2, "jmorrison-juniper", None, "health check exited with code 2"),
                    ("check_environment_health", 0, "jmorrison-juniper", "oserror", "health check failed"),
                    ("configure_git_username", 0, "jmorrison-juniper", "absent", "Git is absent"),
                    ("configure_git_username", 1, "jmorrison-juniper", None, "Git credential configuration failed"),
                    (
                        "configure_git_username",
                        0,
                        "jmorrison-juniper",
                        "oserror",
                        "Git credential configuration failed",
                    ),
                    (
                        "configure_git_username",
                        0,
                        "jmorrison-juniper",
                        "process",
                        "Git credential configuration failed",
                    ),
                    ("warn_on_mismatch", 0, "jmorrison-juniper", "absent", "The gh command is absent"),
                    ("warn_on_mismatch", 1, "jmorrison-juniper", None, "account read returned code 1"),
                    ("warn_on_mismatch", 0, "jmorrison-juniper", "oserror", "account read failed"),
                    ("warn_on_mismatch", 0, "jmorrison-juniper", "process", "account read failed"),
                    ("warn_on_mismatch", 0, "", None, "active GitHub account is unknown"),
                    (
                        "warn_on_mismatch",
                        0,
                        "other-account",
                        None,
                        "These variables override the stored login: GH_TOKEN, GITHUB_TOKEN",
                    ),
                    (
                        "warn_on_mismatch",
                        0,
                        "jmorrison-juniper",
                        None,
                        "The active GitHub account is jmorrison-juniper.",
                    ),
                ),
            )
            def test_nonblocking_checks(
                self,
                offline: TestInstallEnvironment.TestUvBootstrap.TestIndexes.OfflineRun,
                caplog: pytest.LogCaptureFixture,
                scenario: tuple[str, int, str, str | None, str],
            ) -> None:  # Prove preserved account and health decisions without editing those production methods.
                """Existing health and account warnings retain readiness without exposing credential values."""
                logging.info("Checking nonblocking setup warnings.")  # Trace before actual main sequencing.
                offline.setup.process.configure_check(scenario)  # Prepare only local external outcomes.
                result = bootstrap_worktree.main([])  # Exercise unchanged health and account behavior.
                logging.debug("Checked the warning path with status %s.", result)  # Report only the exit decision.
                action, _, _, failure, expected = scenario  # Keep independent report and process expectations.
                assert result == 0 and "The environment is ready." in caplog.text  # Keep warnings nonblocking.
                assert expected in caplog.text  # Require the existing detailed warning or account report.
                assert (action in offline.events) is (failure != "absent")  # Missing tools must start no process.
                assert "fake-health-token" not in caplog.text and "fake-account-token" not in caplog.text  # Hide.
                assert bootstrap_worktree.EXPECTED_GITHUB_ACCOUNT == "jmorrison-juniper"  # Preserve account ownership.
