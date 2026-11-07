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
from types import SimpleNamespace  # WHY: Replace only the bootstrap clock during duration checks.
from unittest.mock import Mock  # WHY: Record the environment builder without creating a real virtual environment.

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

    def test_locked_sync_reports_its_duration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A successful locked sync reports one measured duration."""
        clock = iter((4.0, 6.5))  # WHY: Keep elapsed time stable without patching the process clock.
        monkeypatch.setattr(
            bootstrap_worktree, "time", SimpleNamespace(monotonic=clock.__next__)
        )  # WHY: Replace only the bootstrap clock.
        monkeypatch.setattr(
            bootstrap_worktree.shutil, "which", lambda name: "/tools/uv"
        )  # WHY: Select the installed UV command.
        monkeypatch.setattr(PipIndexProbe, "fallback_index", lambda probe: None)  # WHY: Keep the sync offline.
        monkeypatch.setattr(
            bootstrap_worktree.subprocess,
            "run",
            lambda command, **options: subprocess.CompletedProcess(command, 0),
        )  # WHY: Return success without starting a process.

        with caplog.at_level("INFO", logger="bootstrap_worktree"):  # WHY: Capture the timing report.
            WorktreeBootstrapper(tmp_path).sync_dependencies()  # WHY: Exercise the locked sync.

        assert "The locked UV sync took 2.5 seconds." in caplog.text  # WHY: Verify the measured duration.

    @pytest.mark.parametrize("first_result", [0, 3])
    def test_each_sync_invocation_uses_a_fresh_source_decision(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, first_result: int
    ) -> None:
        """A later invocation does not inherit an earlier source fallback."""
        decisions = [bootstrap_worktree.PUBLIC_INDEX_URL, None]  # WHY: Model different source results per call.
        results = [first_result, 0]  # WHY: Model success or failure, then a successful fresh call.
        environments: list[dict[str, str]] = []  # WHY: Inspect each independent child environment.
        monkeypatch.delenv("UV_INDEX_URL", raising=False)  # WHY: Prevent a host value from hiding stale state.
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: "/tools/uv")  # WHY: Avoid installing UV.
        monkeypatch.setattr(
            PipIndexProbe, "fallback_index", lambda probe: decisions.pop(0)
        )  # WHY: Return one fresh source decision per invocation.

        def run(command: list[str], env: dict[str, str], **options: object) -> subprocess.CompletedProcess[str]:
            environments.append(env)  # WHY: Retain the environment passed to each sync.
            return subprocess.CompletedProcess(command, results.pop(0))  # WHY: Return the selected status.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", run)  # WHY: Avoid starting UV.
        bootstrapper = WorktreeBootstrapper(tmp_path)  # WHY: Reuse one object to expose stale state.

        if first_result:  # WHY: A failed first run must not block a later invocation.
            with pytest.raises(
                RuntimeError, match="locked UV sync failed with code 3"
            ):  # WHY: Require the first error.
                bootstrapper.sync_dependencies()  # WHY: Exercise the failed invocation.
        else:  # WHY: Also cover a successful first invocation.
            bootstrapper.sync_dependencies()  # WHY: Exercise the successful invocation.
        bootstrapper.sync_dependencies()  # WHY: Exercise a fresh second invocation.

        assert environments[0]["UV_INDEX_URL"] == bootstrap_worktree.PUBLIC_INDEX_URL  # WHY: Keep first fallback local.
        assert "UV_INDEX_URL" not in environments[1]  # WHY: Do not inherit the earlier fallback.
        assert bootstrapper.index_override is None  # WHY: Clear the prior invocation's decision.

    def test_uv_launch_failure_is_safe_and_reports_timing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A UV launch error stops once and does not expose its private detail."""
        secret = "private-launch-detail"  # WHY: Detect accidental exception-detail logging.
        clock = iter((7.0, 9.0))  # WHY: Keep the failure duration deterministic.
        commands: list[list[str]] = []  # WHY: Prove that UV receives no retry.
        monkeypatch.setattr(
            bootstrap_worktree, "time", SimpleNamespace(monotonic=clock.__next__)
        )  # WHY: Replace only the bootstrap clock.
        monkeypatch.setattr(
            bootstrap_worktree.shutil, "which", lambda name: "/tools/uv"
        )  # WHY: Select the installed UV command.
        monkeypatch.setattr(PipIndexProbe, "fallback_index", lambda probe: None)  # WHY: Keep the test offline.

        def fail(command: list[str], **options: object) -> None:
            commands.append(command)  # WHY: Count attempted launches.
            raise OSError(secret)  # WHY: Model an error that holds private detail.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", fail)  # WHY: Prevent a real process launch.

        with caplog.at_level("DEBUG", logger="bootstrap_worktree"):  # WHY: Inspect safe diagnostic output.
            with pytest.raises(
                RuntimeError, match="locked UV sync could not start \\(OSError\\)"
            ) as caught:  # WHY: Require a safe, typed failure.
                WorktreeBootstrapper(tmp_path).sync_dependencies()  # WHY: Exercise the failed UV launch.

        assert len(commands) == 1  # WHY: Do not retry an unsafe command failure.
        assert isinstance(caught.value.__cause__, OSError)  # WHY: Preserve the original failure cause.
        assert secret not in str(caught.value)  # WHY: Keep exception details private.
        assert secret not in caplog.text  # WHY: Keep logs free of exception details.
        assert "The locked UV sync took 2.0 seconds." in caplog.text  # WHY: Report duration on failure.


class TestLockedSyncSources:
    """Cover source mapping without changing the caller environment."""

    def test_pip_index_maps_to_uv_and_preserves_caller_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A configured pip index remains the source for the locked sync."""
        monkeypatch.setenv("PIP_INDEX_URL", MIRROR_URL)  # Model a caller-selected mirror.
        monkeypatch.delenv("UV_INDEX_URL", raising=False)  # Start without a UV override.
        policy = WorktreeBootstrapper.InstallationPolicy("/tools/uv", {}, None, "/base/python")

        environment = WorktreeBootstrapper(Path("root"))._install_environment(policy)  # Build a child-only mapping.

        assert environment["UV_INDEX_URL"] == MIRROR_URL  # Preserve the configured package source.
        assert environment["UV_LINK_MODE"] == "copy"  # Avoid hard links across the worktree and cache.
        assert environment["UV_NATIVE_TLS"] == "1"  # Keep system trust for TLS inspection.
        assert environment["UV_SYSTEM_CERTS"] == "1"  # Keep system certificates available.
        assert environment["UV_HTTP_RETRIES"] == "1"  # Match the bounded retry contract.
        assert environment["UV_HTTP_TIMEOUT"] == "15"  # Match the bounded socket timeout.
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

    def test_fallback_keeps_the_caller_environment_and_private_settings_unchanged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed mirror changes only one child environment and hides its credentials."""
        secret_url = "https://user:private-index-password@mirror.example.invalid/simple/"  # WHY: Detect leaks.
        child_environments: list[dict[str, str]] = []  # WHY: Inspect child-only changes.
        pip_config = tmp_path / "pip.conf"  # WHY: Keep saved configuration inside the test root.
        uv_config = tmp_path / "uv.toml"  # WHY: Keep saved configuration inside the test root.
        pip_config.write_text("index-url = private\n", encoding="utf-8")  # WHY: Model existing pip configuration.
        uv_config.write_text("index-url = private\n", encoding="utf-8")  # WHY: Model existing UV configuration.
        monkeypatch.setenv("PIP_INDEX_URL", secret_url)  # WHY: Model caller primary-source settings.
        monkeypatch.setenv("PIP_EXTRA_INDEX_URL", secret_url)  # WHY: Model caller extra-source settings.
        monkeypatch.setenv("PIP_CONFIG_FILE", str(pip_config))  # WHY: Model saved pip configuration.
        monkeypatch.setenv("UV_INDEX_URL", secret_url)  # WHY: Model a competing caller UV source.
        monkeypatch.setenv("UV_CONFIG_FILE", str(uv_config))  # WHY: Model saved UV configuration.
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: "/tools/uv")  # WHY: Avoid installing UV.

        def read_index(probe: PipIndexProbe) -> str:
            probe.source_settings["global.index-url"] = secret_url  # WHY: Snapshot the configured primary.
            probe.source_settings["global.extra-index-url"] = secret_url  # WHY: Snapshot the configured extra.
            return secret_url  # WHY: Model the selected private index.

        def fail_connection(probe: PipIndexProbe, url: str) -> bool:
            return False  # WHY: Select the public fallback without a network request.

        def run(command: list[str], env: dict[str, str], **options: object) -> subprocess.CompletedProcess[str]:
            child_environments.append(dict(env))  # WHY: Retain an isolated copy for the assertions.
            return subprocess.CompletedProcess(command, 0)  # WHY: Complete the locked sync successfully.

        monkeypatch.setattr(PipIndexProbe, "read_index_url", read_index)  # WHY: Avoid launching pip for discovery.
        monkeypatch.setattr(PipIndexProbe, "reaches", fail_connection)  # WHY: Avoid opening a network connection.
        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", run)  # WHY: Avoid launching UV.

        with caplog.at_level("WARNING", logger="bootstrap_worktree"):  # WHY: Inspect the operator warning.
            WorktreeBootstrapper(tmp_path).sync_dependencies()  # WHY: Exercise the complete fallback path.

        assert len(child_environments) == 1  # WHY: Run one locked sync.
        assert child_environments[0]["UV_INDEX_URL"] == bootstrap_worktree.PUBLIC_INDEX_URL  # WHY: Use safe source.
        assert child_environments[0]["PIP_INDEX_URL"] == bootstrap_worktree.PUBLIC_INDEX_URL  # WHY: Align pip source.
        assert child_environments[0]["PIP_CONFIG_FILE"] == bootstrap_worktree.os.devnull  # WHY: Ignore saved pip.
        assert "PIP_EXTRA_INDEX_URL" not in child_environments[0]  # WHY: Drop the failed extra source.
        assert os.environ["PIP_INDEX_URL"] == secret_url  # WHY: Preserve the caller primary source.
        assert os.environ["PIP_EXTRA_INDEX_URL"] == secret_url  # WHY: Preserve the caller extra source.
        assert os.environ["PIP_CONFIG_FILE"] == str(pip_config)  # WHY: Preserve saved pip configuration.
        assert os.environ["UV_INDEX_URL"] == secret_url  # WHY: Preserve the caller UV source.
        assert os.environ["UV_CONFIG_FILE"] == str(uv_config)  # WHY: Preserve saved UV configuration.
        assert pip_config.read_text(encoding="utf-8") == "index-url = private\n"  # WHY: Do not rewrite pip config.
        assert uv_config.read_text(encoding="utf-8") == "index-url = private\n"  # WHY: Do not rewrite UV config.
        assert "private-index-password" not in caplog.text  # WHY: Redact source credentials.

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
            (
                {},
                {"install.extra-index-url": "https://extra-only.example.invalid/simple/"},
                (None, "https://extra-only.example.invalid/simple/"),
            ),
        ],
    )
    def test_pip_source_precedence_maps_to_uv(
        self,
        caller: dict[str, str],
        sources: dict[str, str],
        expected: tuple[str | None, str | None],
    ) -> None:
        """Caller settings override install and global config, which override nothing."""
        policy = WorktreeBootstrapper.InstallationPolicy("/tools/uv", sources, None, "/base/python")
        environment = dict(caller)  # Isolate all mappings from the caller dictionary.
        environment["UV_CONFIG_FILE"] = "caller-uv.toml"  # Model a config file that could override source choices.

        policy.apply(environment)  # Keep captured pip configuration available to UV.

        assert (
            environment.get("UV_INDEX_URL"),
            environment.get("UV_EXTRA_INDEX_URL"),
        ) == expected  # Preserve precedence.
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

    def test_configuration_snapshot_keeps_whitespace_and_all_source_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One configuration report preserves install priority and both source classes."""
        report = (
            " global.index-url = 'https://global.example.invalid/simple/' \n"  # WHY: Include leading spaces.
            " install.index-url = 'https://install.example.invalid/simple/' \n"  # WHY: Include higher-priority source.
            " global.extra-index-url = 'https://global-extra.example.invalid/simple/' \n"  # WHY: Keep global extra.
            " install.extra-index-url = 'https://install-extra.example.invalid/simple/' \n"  # WHY: Keep install extra.
        )
        monkeypatch.setattr(
            bootstrap_worktree.subprocess,
            "run",
            lambda command, **options: subprocess.CompletedProcess(command, 0, stdout=report),
        )  # WHY: Return a captured configuration report without running pip.
        probe = PipIndexProbe(Path("/worktree/.venv/bin/python"))  # WHY: Avoid a real interpreter.

        assert probe.read_index_url() == "https://global.example.invalid/simple/"  # WHY: Preserve first report value.
        assert probe.source_settings == {  # WHY: Retain every source for later precedence decisions.
            "global.index-url": "https://global.example.invalid/simple/",
            "install.index-url": "https://install.example.invalid/simple/",
            "global.extra-index-url": "https://global-extra.example.invalid/simple/",
            "install.extra-index-url": "https://install-extra.example.invalid/simple/",
        }

    def test_sync_reads_and_probes_once_without_logging_index_credentials(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The complete sync makes one source read and one bounded probe."""
        secret_url = "https://user:probe-password@mirror.example.invalid/simple/"  # WHY: Detect credential leaks.
        report = f"global.index-url='{secret_url}'"  # WHY: Model pip's private configuration output.
        commands: list[list[str]] = []  # WHY: Count the source read and locked sync.
        probes: list[tuple[tuple[str, int], float]] = []  # WHY: Count bounded network probes.
        for name in (
            "PIP_INDEX_URL",
            "PIP_EXTRA_INDEX_URL",
            "UV_INDEX",
            "UV_DEFAULT_INDEX",
            "UV_INDEX_URL",
            "UV_EXTRA_INDEX_URL",
        ):
            monkeypatch.delenv(name, raising=False)  # WHY: Remove host-specific source settings.
        monkeypatch.setattr(bootstrap_worktree.shutil, "which", lambda name: "/tools/uv")  # WHY: Select installed UV.

        def run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
            commands.append(command)  # WHY: Count each subprocess invocation.
            output = report if command[-4:] == ["-m", "pip", "config", "list"] else ""  # WHY: Answer the source read.
            return subprocess.CompletedProcess(command, 0, stdout=output)  # WHY: Complete both commands successfully.

        def refuse(address: tuple[str, int], timeout: float) -> nullcontext[None]:
            probes.append((address, timeout))  # WHY: Record the bounded connection attempt.
            raise OSError("connection refused")  # WHY: Select the public fallback deterministically.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", run)  # WHY: Avoid starting external processes.
        monkeypatch.setattr(socket, "create_connection", refuse)  # WHY: Avoid network access.

        with caplog.at_level("DEBUG", logger="bootstrap_worktree"):  # WHY: Inspect probe logs.
            WorktreeBootstrapper(tmp_path).sync_dependencies()  # WHY: Exercise the integrated source decision.

        assert len(commands) == 2  # WHY: Read configuration once, then run one locked sync.
        assert sum(command[-4:] == ["-m", "pip", "config", "list"] for command in commands) == 1  # WHY: One read.
        assert sum("sync" in command for command in commands) == 1  # WHY: One package operation.
        assert probes == [(("mirror.example.invalid", 443), 3.0)]  # WHY: Make one bounded probe.
        assert "probe-password" not in caplog.text  # WHY: Hide URL credentials.

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


class TestEnvironmentOptions:
    """Keep environment paths and creation modes correct across platforms."""

    @pytest.mark.parametrize(
        ("platform", "path_parts"),
        [("win32", ("Scripts", "python.exe")), ("linux", ("bin", "python")), ("darwin", ("bin", "python"))],
    )
    def test_interpreter_path_is_platform_specific(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        platform: str,
        path_parts: tuple[str, str],
    ) -> None:
        """Return the Windows path or the POSIX path for the selected platform."""
        monkeypatch.setattr(bootstrap_worktree.sys, "platform", platform)  # WHY: Exercise each platform branch.
        bootstrapper = WorktreeBootstrapper(tmp_path)  # WHY: Build paths from an isolated root.

        assert bootstrapper.interpreter == tmp_path / ".venv" / Path(*path_parts)  # WHY: Keep both path forms.

    @pytest.mark.parametrize("platform, symlinks", [("win32", False), ("linux", True), ("darwin", True)])
    def test_environment_builder_uses_platform_symlink_policy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str, symlinks: bool
    ) -> None:
        """Select symlinks only on POSIX platforms."""
        monkeypatch.setattr(bootstrap_worktree.sys, "platform", platform)  # WHY: Exercise each platform branch.
        builder = Mock()  # WHY: Prevent creation of a real environment.
        options_seen: list[dict[str, object]] = []  # WHY: Inspect the builder policy.

        def build(**options: object) -> Mock:
            options_seen.append(options)  # WHY: Retain the constructor settings.
            return builder  # WHY: Keep the environment creation local.

        monkeypatch.setattr(bootstrap_worktree.venv, "EnvBuilder", build)  # WHY: Replace the environment builder.
        WorktreeBootstrapper(tmp_path).create_environment()  # WHY: Exercise environment creation.

        assert options_seen == [{"with_pip": True, "upgrade_deps": False, "symlinks": symlinks}]  # WHY: Check options.
        assert builder.create.call_args.args == (tmp_path / ".venv",)  # WHY: Use the configured environment path.

    def test_environment_creation_reuses_and_recreates_the_interpreter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Reuse an existing interpreter unless recreation is explicit."""
        builder = Mock()  # WHY: Prevent creation of a real environment.
        calls: list[dict[str, object]] = []  # WHY: Count environment-builder construction.

        def build(**options: object) -> Mock:
            calls.append(options)  # WHY: Record each environment creation.
            return builder  # WHY: Keep the environment creation local.

        monkeypatch.setattr(bootstrap_worktree.venv, "EnvBuilder", build)  # WHY: Replace the environment builder.
        bootstrapper = WorktreeBootstrapper(tmp_path)  # WHY: Own the temporary environment.
        bootstrapper.create_environment()  # WHY: Create the initial environment.
        bootstrapper.interpreter.parent.mkdir(parents=True)  # WHY: Model the created interpreter path.
        bootstrapper.interpreter.touch()  # WHY: Mark the environment as ready.
        bootstrapper.create_environment()  # WHY: Check the reuse path.
        assert len(calls) == 1  # WHY: Reuse must not create another environment.
        bootstrapper.create_environment(recreate=True)  # WHY: Explicitly rebuild the environment.

        assert len(calls) == 2  # WHY: Recreate must construct a new environment.
        assert builder.create.call_count == 2  # WHY: Verify the initial and recreated builds.


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

    def test_health_failure_is_nonblocking_and_redacts_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A health command failure warns without exposing its private detail."""
        secret = "private-health-detail"  # WHY: Detect accidental exception-detail logging.

        def fail(*args: object, **options: object) -> subprocess.CompletedProcess[str]:
            raise OSError(secret)  # WHY: Model an error that holds private detail.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", fail)  # WHY: Prevent a health subprocess.

        with caplog.at_level("WARNING", logger="bootstrap_worktree"):  # WHY: Capture the warning.
            WorktreeBootstrapper(tmp_path).check_environment_health()  # WHY: Exercise the nonblocking health check.

        assert "failed (OSError)" in caplog.text  # WHY: Report only the error type.
        assert secret not in caplog.text  # WHY: Keep private error details out of logs.

    def test_account_failure_is_nonblocking_and_redacts_error(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unknown active account does not block setup or expose private detail."""
        secret = "private-account-detail"  # WHY: Detect accidental exception-detail logging.
        monkeypatch.setattr(
            bootstrap_worktree.shutil, "which", lambda name: "/tools/gh"
        )  # WHY: Select the account command.

        def fail(*args: object, **options: object) -> subprocess.CompletedProcess[str]:
            raise OSError(secret)  # WHY: Model an error that holds private detail.

        monkeypatch.setattr(bootstrap_worktree.subprocess, "run", fail)  # WHY: Prevent an account subprocess.

        with caplog.at_level("DEBUG", logger="bootstrap_worktree"):  # WHY: Capture the account diagnostic.
            result = bootstrap_worktree.GitHubAccountChecker().warn_on_mismatch()  # WHY: Check unknown-account safety.

        assert result is True  # WHY: An unknown account must not block setup.
        assert "The account read failed (OSError)." in caplog.text  # WHY: Report only the error type.
        assert secret not in caplog.text  # WHY: Keep private error details out of logs.

    def test_main_continues_after_browser_health_and_account_warnings(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nonblocking readiness warnings do not change the successful exit code."""
        events: list[object] = []  # WHY: Record setup order without external actions.
        self._patch_main(tmp_path, monkeypatch, events)  # WHY: Keep setup operations local.
        monkeypatch.setattr(
            WorktreeBootstrapper, "install_browser_driver", lambda self: events.append("browser-warning") or False
        )  # WHY: Model a nonblocking browser warning.
        monkeypatch.setattr(
            WorktreeBootstrapper, "check_environment_health", lambda self: events.append("health-warning")
        )  # WHY: Model a nonblocking health warning.
        monkeypatch.setattr(
            bootstrap_worktree.GitHubAccountChecker,
            "configure_git_username",
            lambda self, root: events.append("configure-warning") or False,
        )  # WHY: Model a nonblocking credential warning.
        monkeypatch.setattr(
            bootstrap_worktree.GitHubAccountChecker,
            "warn_on_mismatch",
            lambda self: events.append("account-warning") or False,
        )  # WHY: Model a nonblocking account warning.

        assert bootstrap_worktree.main([]) == 0  # WHY: Preserve successful readiness despite warnings.
        assert events[-5:] == [  # WHY: Run every later readiness step.
            "health-warning",
            "browser-warning",
            "report",
            "configure-warning",
            "account-warning",
        ]
