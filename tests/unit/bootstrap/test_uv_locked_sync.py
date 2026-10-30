"""Verify that the worktree bootstrap uses the project lock.

The locked sync must remain the only project dependency installation path.
These tests stub every subprocess and network boundary.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path

import pytest

from scripts import bootstrap_worktree
from scripts.bootstrap_worktree import PipIndexProbe, WorktreeBootstrapper

MIRROR_URL = "https://mirror.example.invalid/simple/"


class TestLockedSync:
    """Cover the locked command and the missing-UV path."""

    def test_existing_uv_runs_one_locked_sync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The bootstrap uses the lock and the development extra from the project root."""
        calls: list[tuple[list[str], dict[str, object]]] = []  # Record the subprocess boundary without execution.
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: "/tools/uv")  # Select a fixed executable.
        monkeypatch.setattr(PipIndexProbe, "fallback_index", lambda probe: None)  # Keep the test offline.
        monkeypatch.setattr(
            bootstrap_worktree.subprocess,
            "run",
            lambda command, **options: calls.append((command, options))
            or subprocess.CompletedProcess(command, 0),  # Return a successful process record.
        )

        WorktreeBootstrapper(tmp_path).sync_dependencies()  # Exercise the production sync path.

        assert len(calls) == 1  # One locked operation replaces two requirements-file installs.
        assert calls[0][0] == ["/tools/uv", "sync", "--locked", "--extra", "dev"]  # Verify lock and dev group.
        assert calls[0][1]["cwd"] == tmp_path  # Resolve the lock from the worktree root.

    def test_missing_uv_installs_outside_the_project_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing UV tool is installed for the base interpreter before the sync."""
        calls: list[tuple[list[str], dict[str, object]]] = []  # Record UV setup and the project sync.
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: None)  # Model a missing UV command.
        monkeypatch.setattr(PipIndexProbe, "fallback_index", lambda probe: None)  # Keep the test offline.
        monkeypatch.setattr(sys, "_base_executable", "/base/python", raising=False)  # Isolate the user interpreter.
        monkeypatch.setattr(
            bootstrap_worktree.subprocess,
            "run",
            lambda command, **options: calls.append((command, options))
            or subprocess.CompletedProcess(command, 0),  # Return a successful process record.
        )

        WorktreeBootstrapper(tmp_path).sync_dependencies()  # Exercise the missing-tool branch.

        assert [call[0] for call in calls] == [  # Require the tool installation before the locked sync.
            ["/base/python", "-m", "pip", "install", "--user", "uv"],
            ["/base/python", "-m", "uv", "sync", "--locked", "--extra", "dev"],
        ]
        assert calls[1][1]["cwd"] == tmp_path  # Run the sync from the repository root.

    def test_uv_install_failure_stops_before_sync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed UV installation must not run a non-locked fallback."""
        commands: list[list[str]] = []  # Record commands so no fallback can hide the failure.
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: None)  # Model a missing UV command.
        monkeypatch.setattr(PipIndexProbe, "fallback_index", lambda probe: None)  # Keep the test offline.
        monkeypatch.setattr(sys, "_base_executable", "/base/python", raising=False)  # Isolate the user interpreter.
        monkeypatch.setattr(
            bootstrap_worktree.subprocess,
            "run",
            lambda command, **options: commands.append(command)
            or subprocess.CompletedProcess(command, 1),  # Report a failed tool installation.
        )

        with pytest.raises(RuntimeError, match="uv tool installation failed with code 1"):  # Require clear failure.
            WorktreeBootstrapper(tmp_path).sync_dependencies()  # Do not attempt an unlocked fallback.

        assert commands == [["/base/python", "-m", "pip", "install", "--user", "uv"]]  # No sync follows.

    def test_locked_sync_failure_is_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failing sync stops the bootstrap with its process status."""
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: "/tools/uv")  # Select installed UV.
        monkeypatch.setattr(PipIndexProbe, "fallback_index", lambda probe: None)  # Keep the test offline.
        monkeypatch.setattr(
            bootstrap_worktree.subprocess,
            "run",
            lambda command, **options: subprocess.CompletedProcess(command, 3),  # Report a failed sync.
        )

        with pytest.raises(RuntimeError, match="locked UV sync failed with code 3"):  # Surface the process status.
            WorktreeBootstrapper(tmp_path).sync_dependencies()  # Do not report a success-shaped result.


class TestLockedSyncSources:
    """Cover source mapping without changing the caller environment."""

    def test_pip_index_maps_to_uv_and_preserves_caller_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A configured pip index remains the source for the locked sync."""
        monkeypatch.setenv("PIP_INDEX_URL", MIRROR_URL)  # Model a caller-selected mirror.
        monkeypatch.delenv("UV_INDEX_URL", raising=False)  # Start without a UV override.
        policy = WorktreeBootstrapper.InstallationPolicy("/tools/uv", {}, None, "/base/python")

        environment = WorktreeBootstrapper(Path("root"))._install_environment(policy)  # Build a child-only mapping.

        assert environment["UV_INDEX_URL"] == MIRROR_URL  # Preserve the configured package source.
        assert environment["UV_NATIVE_TLS"] == "1"  # Keep system trust for TLS inspection.
        assert environment["UV_SYSTEM_CERTS"] == "1"  # Keep system certificates available.
        assert "UV_HTTP_RETRIES" in environment and "UV_HTTP_TIMEOUT" in environment  # Bound network waits.
        assert os.environ["PIP_INDEX_URL"] == MIRROR_URL  # Keep the parent setting unchanged.
        assert "UV_INDEX_URL" not in os.environ  # Keep the mapped value in the child only.

    def test_unreachable_index_uses_the_public_source_for_both_tools(self) -> None:
        """The public fallback applies to UV and to its pip-based tool installation."""
        policy = WorktreeBootstrapper.InstallationPolicy(  # Select the fixed public fallback.
            None, {}, bootstrap_worktree.PUBLIC_INDEX_URL, "/base/python"
        )
        environment: dict[str, str] = {  # Model caller sources that all refer to the failed mirror.
            "PIP_INDEX_URL": MIRROR_URL,
            "PIP_EXTRA_INDEX_URL": MIRROR_URL,
            "UV_INDEX": MIRROR_URL,
            "UV_DEFAULT_INDEX": MIRROR_URL,
            "UV_INDEX_URL": MIRROR_URL,
            "UV_EXTRA_INDEX_URL": MIRROR_URL,
        }

        policy.apply(environment)  # Apply the source choice to one child process.

        assert environment["UV_INDEX_URL"] == bootstrap_worktree.PUBLIC_INDEX_URL  # Keep UV on the public index.
        assert environment["PIP_INDEX_URL"] == bootstrap_worktree.PUBLIC_INDEX_URL  # Use it to install UV too.
        assert "PIP_EXTRA_INDEX_URL" not in environment  # Do not retry the failed mirror.
        assert environment["PIP_CONFIG_FILE"] == bootstrap_worktree.os.devnull  # Block saved mirror settings.
        assert "UV_EXTRA_INDEX_URL" not in environment  # Do not restore the failed extra source.

    @pytest.mark.parametrize(
        ("caller", "sources", "expected"),
        [
            (
                {
                    "PIP_INDEX_URL": "https://caller.example.invalid/simple/",
                    "PIP_EXTRA_INDEX_URL": "https://caller-extra.example.invalid/simple/",
                },
                {
                    "global.index-url": "https://global.example.invalid/simple/",
                    "install.index-url": "https://install.example.invalid/simple/",
                },
                ("https://caller.example.invalid/simple/", "https://caller-extra.example.invalid/simple/"),
            ),
            (
                {"PIP_INDEX_URL": "", "PIP_EXTRA_INDEX_URL": ""},
                {
                    "global.index-url": "https://global.example.invalid/simple/",
                    "install.index-url": "https://install.example.invalid/simple/",
                    "global.extra-index-url": "https://global-extra.example.invalid/simple/",
                    "install.extra-index-url": "https://install-extra.example.invalid/simple/",
                },
                ("https://install.example.invalid/simple/", "https://install-extra.example.invalid/simple/"),
            ),
            (
                {
                    "UV_INDEX": "https://wrong.example.invalid/simple/",
                    "UV_DEFAULT_INDEX": "https://wrong.example.invalid/simple/",
                    "UV_INDEX_URL": "https://wrong.example.invalid/simple/",
                    "UV_EXTRA_INDEX_URL": "https://wrong-extra.example.invalid/simple/",
                },
                {
                    "global.index-url": "https://global.example.invalid/simple/",
                    "global.extra-index-url": "https://global-extra.example.invalid/simple/",
                },
                ("https://global.example.invalid/simple/", "https://global-extra.example.invalid/simple/"),
            ),
        ],
    )
    def test_pip_source_precedence_maps_to_uv(
        self,
        caller: dict[str, str],
        sources: dict[str, str],
        expected: tuple[str, str],
    ) -> None:
        """Caller settings override install and global config, which override nothing."""
        policy = WorktreeBootstrapper.InstallationPolicy("/tools/uv", sources, None, "/base/python")
        environment = dict(caller)  # Isolate all mappings from the caller dictionary.
        environment["UV_CONFIG_FILE"] = "caller-uv.toml"  # Model a config file that could override source choices.

        policy.apply(environment)  # Keep captured pip configuration available to UV.

        assert (environment["UV_INDEX_URL"], environment["UV_EXTRA_INDEX_URL"]) == expected  # Preserve precedence.
        assert all(  # Remove every competing alias before UV reads the environment.
            name not in environment for name in ("UV_INDEX", "UV_DEFAULT_INDEX", "UV_CONFIG_FILE")
        )
        assert environment["UV_NO_CONFIG"] == "1"  # Prevent saved UV configuration from changing the source.


class TestIndexProbe:
    """Keep the bounded mirror decision that protects bootstrap installs."""

    @pytest.mark.parametrize(
        ("report", "expected"),
        [
            ("global.index-url='https://mirror/simple/'", "https://mirror/simple/"),
            ("install.index-url='https://other/simple/'", "https://other/simple/"),
            ('global.index-url="https://quoted/simple/"', "https://quoted/simple/"),
            ("global.index-url=''", None),
            ("global.trusted-host='mirror'", None),
            ("line without a separator", None),
            ("unrelated output", None),
            ("", None),
        ],
    )
    def test_parse_index_url(self, report: str, expected: str | None) -> None:
        """The parser returns only a configured primary index."""
        assert PipIndexProbe._parse_index_url(report) == expected  # Ignore settings that are not a primary index.

    def test_an_empty_first_primary_index_wins_over_a_later_value(self) -> None:
        """A later setting does not replace an explicitly empty first primary value."""
        report = "global.index-url=''\ninstall.index-url='https://later.example.invalid/simple/'"
        sources: dict[str, str] = {}

        assert PipIndexProbe._parse_index_url(report, sources) is None  # Keep the first-value decision.
        assert sources == {  # Retain both values for UV source mapping.
            "global.index-url": "",
            "install.index-url": "https://later.example.invalid/simple/",
        }

    def test_unreachable_index_selects_the_public_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unreachable private index selects the public source for this run."""
        probe = PipIndexProbe(Path("python"))  # Do not create a real interpreter or package process.
        monkeypatch.setattr(probe, "read_index_url", lambda: MIRROR_URL)  # Supply the mirror as local test data.
        monkeypatch.setattr(probe, "reaches", lambda url: False)  # Do not open a network connection.

        assert probe.fallback_index() == bootstrap_worktree.PUBLIC_INDEX_URL  # Use only the fixed fallback.

    def test_read_index_url_captures_sources_from_one_pip_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The probe reads primary and extra sources from one bounded command."""
        calls: list[tuple[list[str], dict[str, object]]] = []  # Record the subprocess boundary.
        report = (
            "global.index-url='https://primary.example.invalid/simple/'\n"
            "global.extra-index-url='https://extra.example.invalid/simple/'\n"
        )

        def run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
            calls.append((command, options))  # Keep the arguments available for exact checks.
            return subprocess.CompletedProcess(command, 0, stdout=report)  # Avoid launching pip.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", run)  # Prevent external process execution.
        probe = PipIndexProbe(Path("/worktree/.venv/bin/python"))

        assert probe.read_index_url() == "https://primary.example.invalid/simple/"  # Keep the primary source.
        assert probe.source_settings == {  # Keep the complete source snapshot for UV.
            "global.index-url": "https://primary.example.invalid/simple/",
            "global.extra-index-url": "https://extra.example.invalid/simple/",
        }
        assert calls[0][0] == ["/worktree/.venv/bin/python", "-m", "pip", "config", "list"]  # Use worktree pip.
        assert calls[0][1]["timeout"] == 30  # Bound the configuration read.

    def test_read_index_url_keeps_setup_available_when_pip_cannot_start(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unreadable pip configuration does not prevent the package sync."""

        def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            raise OSError("pip is unavailable")  # Model a missing or unlaunchable pip command.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", fail)  # Prevent an external process.
        probe = PipIndexProbe(Path("/worktree/.venv/bin/python"))

        assert probe.read_index_url() is None  # Keep the standard package source when discovery fails.
        assert probe.source_settings == {}  # Do not keep partial settings from an earlier read.

    def test_reaches_returns_true_when_the_host_accepts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A reachable mirror stays available to the package sync."""
        calls: list[tuple[tuple[str, int], float]] = []  # Capture the host and timeout.

        def connect(address: tuple[str, int], timeout: float) -> nullcontext[None]:
            calls.append((address, timeout))  # Record the bounded connection attempt.
            return nullcontext()  # Avoid creating a network connection.

        monkeypatch.setattr(socket, "create_connection", connect)  # Replace the socket boundary.

        assert PipIndexProbe(Path("python")).reaches(MIRROR_URL) is True  # Preserve a working mirror.
        assert calls == [(("mirror.example.invalid", 443), 3.0)]  # Use HTTPS default port and short timeout.

    def test_reaches_returns_false_when_the_host_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A refused mirror selects the configured fallback."""

        def refuse(address: tuple[str, int], timeout: float) -> nullcontext[None]:
            raise OSError("connection refused")  # Model a failed network probe.

        monkeypatch.setattr(socket, "create_connection", refuse)  # Prevent a real network connection.

        assert PipIndexProbe(Path("python")).reaches(MIRROR_URL) is False  # Report the unreachable mirror.

    @pytest.mark.parametrize(
        ("url", "expected_port"),
        [("http://mirror.example.invalid/simple/", 80), ("https://mirror.example.invalid/simple/", 443)],
    )
    def test_reaches_uses_the_scheme_default_port(
        self, monkeypatch: pytest.MonkeyPatch, url: str, expected_port: int
    ) -> None:
        """A URL without a port uses its scheme default."""
        addresses: list[tuple[str, int]] = []  # Record the target without using the network.

        def refuse(address: tuple[str, int], timeout: float) -> nullcontext[None]:
            addresses.append(address)  # Check the resolved default port.
            raise OSError("connection refused")  # Keep the branch deterministic.

        monkeypatch.setattr(socket, "create_connection", refuse)  # Replace the socket boundary.
        PipIndexProbe(Path("python")).reaches(url)  # Exercise the same parser used by the bootstrap.

        assert addresses == [("mirror.example.invalid", expected_port)]  # Use the port for the URL scheme.

    def test_reaches_keeps_an_unreadable_index_without_a_probe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A URL without a host cannot justify replacing its source."""

        def fail(address: tuple[str, int], timeout: float) -> nullcontext[None]:
            raise AssertionError("The probe must not open a socket without a host.")  # Prove safe behavior.

        monkeypatch.setattr(socket, "create_connection", fail)  # Reject an unexpected network call.

        assert PipIndexProbe(Path("python")).reaches("not-a-url") is True  # Keep the configured source.

    def test_no_index_keeps_the_package_manager_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The default public index needs no network probe."""
        probe = PipIndexProbe(Path("python"))  # Avoid starting pip.
        monkeypatch.setattr(probe, "read_index_url", lambda: None)  # Model no configured index.

        def fail(url: str) -> bool:
            raise AssertionError("A missing index must not trigger a network probe.")  # Prove no probe occurs.

        monkeypatch.setattr(probe, "reaches", fail)  # Reject an unexpected connection.

        assert probe.fallback_index() is None  # Keep the package manager default.

    @pytest.mark.parametrize(
        "index_url",
        ["https://pypi.org/simple", "https://pypi.org/simple/", "https://files.pythonhosted.org/simple"],
    )
    def test_public_index_needs_no_probe(self, monkeypatch: pytest.MonkeyPatch, index_url: str) -> None:
        """The public package index needs no network probe."""
        probe = PipIndexProbe(Path("python"))  # Avoid starting pip.
        monkeypatch.setattr(probe, "read_index_url", lambda: index_url)  # Supply a known public index.

        def fail(url: str) -> bool:
            raise AssertionError("The public index must not trigger a network probe.")  # Prove no probe occurs.

        monkeypatch.setattr(probe, "reaches", fail)  # Reject an unexpected connection.

        assert probe.fallback_index() is None  # Keep the existing public source.

    def test_reachable_private_index_needs_no_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A working private index remains the source for this run."""
        probe = PipIndexProbe(Path("python"))  # Avoid starting pip.
        monkeypatch.setattr(probe, "read_index_url", lambda: MIRROR_URL)  # Supply a private index.
        monkeypatch.setattr(probe, "reaches", lambda url: True)  # Model a reachable host.

        assert probe.fallback_index() is None  # Keep the configured source.

    def test_unreachable_index_logs_the_host_and_run_scope(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The warning names the failed host and limits the change to this run."""
        probe = PipIndexProbe(Path("python"))  # Avoid starting pip.
        monkeypatch.setattr(probe, "read_index_url", lambda: MIRROR_URL)  # Supply the private index.
        monkeypatch.setattr(probe, "reaches", lambda url: False)  # Model a failed network probe.

        with caplog.at_level("WARNING", logger="bootstrap_worktree"):  # Capture the operator-facing warning.
            probe.fallback_index()  # Select the fixed public fallback.

        assert "Caution:" in caplog.text  # Use the required safety signal.
        assert "mirror.example.invalid" in caplog.text  # Identify the failed host without credentials.
        assert "for this run only" in caplog.text  # Confirm that saved configuration remains unchanged.


class TestBootstrapMain:
    """Keep the locked sync in the complete bootstrap sequence."""

    @staticmethod
    def _patch_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, events: list[object]) -> None:
        """Replace external bootstrap actions with an ordered event record."""
        monkeypatch.setattr(bootstrap_worktree.logging, "basicConfig", lambda **options: None)  # Keep logs local.
        monkeypatch.setattr(bootstrap_worktree, "REPOSITORY_ROOT", tmp_path)  # Keep file access in the test root.
        monkeypatch.setattr(
            bootstrap_worktree.StaleSourceSweeper, "sweep", lambda self: events.append("sweep")
        )  # Record the preflight step.
        monkeypatch.setattr(
            WorktreeBootstrapper, "create_environment", lambda self, recreate=False: events.append("create")
        )
        monkeypatch.setattr(
            WorktreeBootstrapper, "sync_dependencies", lambda self: events.append("sync")
        )  # Record the locked dependency step.
        monkeypatch.setattr(
            WorktreeBootstrapper, "check_environment_health", lambda self: events.append("health")
        )  # Record the health step.
        monkeypatch.setattr(
            WorktreeBootstrapper, "install_browser_driver", lambda self: events.append("browser") or True
        )  # Keep the browser step successful.
        monkeypatch.setattr(
            bootstrap_worktree, "report_result", lambda bootstrapper, browser_ready: events.append("report")
        )  # Record the final setup report.
        monkeypatch.setattr(
            bootstrap_worktree.GitHubAccountChecker,
            "configure_git_username",
            lambda self, root: events.append("configure"),
        )  # Record the local credential configuration.
        monkeypatch.setattr(
            bootstrap_worktree.GitHubAccountChecker, "warn_on_mismatch", lambda self: events.append("account")
        )  # Record the account check.

    def test_main_runs_the_locked_sync_before_browser_and_account_checks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A successful sync continues to the browser and credential steps."""
        events: list[object] = []  # Record the order without running external commands.
        self._patch_main(tmp_path, monkeypatch, events)  # Keep every external step local.

        assert bootstrap_worktree.main([]) == 0  # Return success after every required step.
        assert events == [  # Keep setup order and preserve browser and account checks.
            "sweep",
            "create",
            "sync",
            "health",
            "browser",
            "report",
            "configure",
            "account",
        ]

    def test_main_stops_after_a_failed_locked_sync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed lock sync does not report a ready worktree."""
        events: list[object] = []  # Record steps that must stop before browser setup.
        self._patch_main(tmp_path, monkeypatch, events)  # Keep every external step local.

        def fail_sync(self: WorktreeBootstrapper) -> None:
            events.append("sync")  # Record the failure point before the bootstrap reports it.
            raise RuntimeError("locked sync failed")  # Stop later readiness checks.

        monkeypatch.setattr(WorktreeBootstrapper, "sync_dependencies", fail_sync)  # Model a failed UV sync.

        assert bootstrap_worktree.main([]) == 1  # Return a failure code to the shell.
        assert events == ["sweep", "create", "sync"]  # Do not run health, browser, or account checks.
