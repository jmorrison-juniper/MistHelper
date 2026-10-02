"""Prove the actual session behavior with synthetic values and owned paths."""

from __future__ import annotations  # Keep test annotations import-safe.

import logging  # Report temporary mutations and measured outcomes.
import signal  # Compare the script's existing signal behavior.
import subprocess  # Prove owned cleanup after a bounded wait fails.
from pathlib import Path  # Keep every test write under tmp_path.
from types import SimpleNamespace  # Isolate the harness deadline clock without changing process waits.
from unittest.mock import Mock, patch  # Inject only harness decisions and refuse Git history reads.

import pytest  # Keep every required session case bounded and unskipped.

from . import session as session_module  # Exercise explicit missing-capability branches.
from .session import BashSession, OwnedProcess, SessionSandbox  # Execute actual Bash.


@pytest.mark.timeout(30)
class TestBashSyntax:
    """Require real Bash parsing and explicit capability refusal."""

    @pytest.mark.parametrize("invalid", [False, True])
    def test_script_syntax(self, tmp_path: Path, invalid: bool) -> None:
        """Parse the actual source and reject a malformed owned copy."""
        sandbox = SessionSandbox.create(tmp_path)
        path = BashSession.SCRIPT
        if invalid:
            path = tmp_path / "invalid-session.sh"
            logging.info("Write the owned malformed Bash copy %s", path)
            path.write_bytes(BashSession.SCRIPT.read_bytes() + b"\nif then\n")
            logging.debug("Malformed Bash copy is ready at %s", path)
        result = BashSession.syntax(path, sandbox)
        assert result.returncode == (2 if invalid else 0), result.stderr
        assert not Path(sandbox.environment["MISTHELPER_RECORDER_FILE"]).exists()
        if invalid:
            assert str(path) in result.stderr
            assert "syntax error" in result.stderr

    @pytest.mark.parametrize("failure", [OSError("synthetic spawn refusal"), ValueError("synthetic spawn refusal")])
    def test_failed_spawn_closes_capture(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: Exception
    ) -> None:
        """A failed process launch must close its output handle."""
        sandbox = SessionSandbox.create(tmp_path)
        owned = OwnedProcess(sandbox, BashSession.SCRIPT)
        monkeypatch.setattr(session_module.subprocess, "Popen", Mock(side_effect=failure))
        with pytest.raises(type(failure), match="synthetic spawn refusal"):
            owned.__enter__()
        assert owned.handle.closed is True
        assert owned.process is None
        assert not Path(sandbox.environment["MISTHELPER_RECORDER_FILE"]).exists()

    @pytest.mark.parametrize("reason", ["synthetic unavailable", None])
    def test_missing_capability_fails_explicitly(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reason: str | None
    ) -> None:
        """A missing executable or path capability must block rather than pass a skip."""
        sandbox = SessionSandbox.create(tmp_path)  # Keep refusal paths owned even when no process starts.
        owned = OwnedProcess(sandbox, BashSession.SCRIPT)  # No child or output handle exists yet.
        monkeypatch.setattr(session_module, "BASH_SKIP_REASON", reason)  # Exercise the capability refusal directly.
        monkeypatch.setattr(session_module, "BASH_PATH", None)  # Never execute a substitute or unavailable shell.
        with pytest.raises(RuntimeError, match="required Bash capability unavailable"):  # Preserve a real refusal.
            owned.__enter__()  # Required proof must refuse before a log or child exists.
        owned.__exit__(None, None, None)  # Unstarted cleanup must leave every unrelated process alone.
        assert owned.process is None and owned.handle is None  # No resource may leak after the refusal.

    def test_owned_cleanup_after_timeout(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed 30-second wait must release only its owned process group."""
        sandbox = SessionSandbox.create(tmp_path, ((0, 2.0),))  # Keep the actual child alive for the refusal decision.
        with OwnedProcess(sandbox, BashSession.SCRIPT) as owned:  # Own the exact group before injecting a wait failure.
            assert isinstance(owned.process, subprocess.Popen)
            assert owned.process.pid > 0
            with monkeypatch.context() as patcher:  # Restore the real wait before the context performs cleanup.
                patcher.setattr(owned.process, "wait", Mock(side_effect=subprocess.TimeoutExpired("owned session", 30)))
                with pytest.raises(subprocess.TimeoutExpired) as failure:  # Keep the 30-second refusal explicit.
                    owned.wait()  # Inject a harness wait failure, not a production script change.
                assert failure.value.timeout == 30  # The harness timeout must stay at the required value.
        assert owned.process.returncode == -signal.SIGKILL
        assert owned.handle.closed is True

    @pytest.mark.parametrize("mode", ["missing-token", "launch-timeout"])
    def test_signal_without_launch_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
        """A missing recorder must refuse a signal instead of passing an unmeasured case."""
        sandbox = SessionSandbox.create(tmp_path)  # Keep the refusal session fully owned.
        if mode == "missing-token":  # The real credential gate ends the session before a launch.
            sandbox.credential(None, "environment")  # Clear only synthetic credentials.
            expected: type[BaseException] = RuntimeError  # Retain the actual missing-launch refusal.
        else:  # A running child without a recorder must reach the 30-second deadline decision.
            application = tmp_path / "app" / "MistHelper.py"  # Replace only this owned synthetic child.
            logging.info("Write the owned delayed recorder")  # Mark the temporary negative fixture write.
            application.write_text(
                "import time  # Stay local.\ntime.sleep(2)  # Test the recorder deadline.\n", encoding="utf-8"
            )
            logging.debug("Owned delayed recorder is ready")  # Report no token or environment values.
            clock = SimpleNamespace(
                monotonic=Mock(side_effect=[0.0, 31.0]), sleep=Mock()
            )  # Cross only the harness deadline.
            monkeypatch.setattr(session_module, "time", clock)  # Keep actual subprocess waits unchanged.
            expected = subprocess.TimeoutExpired  # A missing recorder must retain the exact timeout refusal.
        with pytest.raises(expected) as failure:  # Do not claim an application received a signal.
            BashSession.run(sandbox, interruption=signal.SIGTERM)  # Signal synchronization must fail closed.
        if mode == "launch-timeout":  # The injected decision still uses the configured 30-second timeout.
            assert failure.value.timeout == 30  # Never weaken the bound to make this case pass.


@pytest.mark.timeout(30)
class TestSessionInheritance:
    """Require the unchanged application arguments and inherited format behavior."""

    @pytest.mark.parametrize("environment", [None, "csv", "sqlite", "polyglot", "synthetic-unsupported"])
    def test_live_preserves_inherited_format(self, tmp_path: Path, environment: str | None) -> None:
        """The original export is red for every case except inherited SQLite."""
        sandbox = SessionSandbox.create(tmp_path)  # Run only the synthetic recorder.
        if environment is not None:  # The clean fixture supplies no OUTPUT_FORMAT by default.
            sandbox.environment["OUTPUT_FORMAT"] = environment  # Supply exactly one inherited non-secret value.
        observation = BashSession.run(sandbox)  # Execute the actual live session script.
        assert observation.returncode == 0  # A clean recorder exit must close the session.
        assert len(observation.records) == 1  # No restart may follow a clean exit.
        assert observation.output.count("[SESSION] Starting MistHelper...") == 1  # Count actual launches too.
        record = observation.records[0]  # Inspect the one real recorder launch.
        assert record["argv"] == ["MistHelper.py"]  # No output flag or new application argument may appear.
        assert record["output_format"] == environment  # Preserve unset and all inherited values.
        assert record["paths"] == {  # Keep application-visible operational paths under tmp_path.
            "DATABASE_PATH": str(tmp_path / "app" / "data" / "mist_data.db"),
            "HOME": str(tmp_path / "home"),
            "TMPDIR": str(tmp_path / "tmp"),
        }
        assert "BASH_ENV" not in sandbox.environment  # Never load an ambient shell startup script.


@pytest.mark.timeout(30)
class TestSessionCredentials:
    """Keep both token aliases, both transfer sources, and early refusal."""

    @pytest.mark.parametrize("alias", ["MIST_APITOKEN", "MIST_API_TOKEN"])
    @pytest.mark.parametrize("source", ["environment", "file"])
    def test_alias_transfer(self, tmp_path: Path, alias: str, source: str) -> None:
        """Both aliases must survive transfer without disclosure."""
        sandbox = SessionSandbox.create(tmp_path)  # Use no entrypoint, SSH daemon, or real credential.
        sandbox.credential(alias, source)  # Supply one synthetic alias through the selected source.
        observation = BashSession.run(sandbox)  # Exercise the existing file reader and credential gate.
        assert observation.returncode == 0  # The synthetic token must open the existing gate.
        assert len(observation.records) == 1  # The clean application must launch exactly once.
        assert observation.records[0]["argv"] == ["MistHelper.py"]  # Credential transfer must not alter invocation.
        assert observation.records[0]["token_matches"] == {  # Compare internally without logging the value.
            "MIST_APITOKEN": alias == "MIST_APITOKEN",
            "MIST_API_TOKEN": alias == "MIST_API_TOKEN",
        }
        observation.require_no_disclosure()  # Include captured output, every owned log, and safe records.

    def test_missing_token_refuses_before_launch(self, tmp_path: Path) -> None:
        """A permanent missing credential must return 1 with zero launches."""
        sandbox = SessionSandbox.create(tmp_path)  # The recorder would otherwise exit successfully.
        sandbox.credential(None, "environment")  # Clear both synthetic token names.
        marker, pid_file = sandbox.markers()  # Preserve cleanup and the existing PID-file treatment on refusal.
        observation = BashSession.run(sandbox)  # Run the actual pre-loop credential gate.
        assert observation.returncode == 1  # Keep the original exact refusal code.
        assert observation.records == ()  # No application launch may occur.
        assert "[SESSION] Starting MistHelper..." not in observation.output  # Refuse before the loop.
        assert "holds no Mist API token" in observation.output  # Name the actual cause once.
        assert not marker.exists()  # Refusal must retain existing marker cleanup.
        assert pid_file.read_text(encoding="utf-8") == "existing PID sentinel\n"  # Never remove or kill this sentinel.


@pytest.mark.timeout(30)
class TestSessionIsolation:
    """Compare actual normal and signal cleanup with the immutable original."""

    @pytest.mark.parametrize("interruption", [None, signal.SIGINT, signal.SIGTERM])
    def test_signal_and_normal_cleanup(self, tmp_path: Path, interruption: signal.Signals | None) -> None:
        """Keep original return codes and cleanup without inventing signal codes."""
        outcomes: list[tuple[int, int]] = []  # Compare actual baseline and live outcomes.
        for version in ("base", "live"):  # Use separate owned paths for each actual execution.
            sandbox = SessionSandbox.create(tmp_path / version, ((0, 0.4),))  # Leave time for a controlled signal.
            marker, pid_file = sandbox.markers()  # Pre-create only owned test files.
            other = marker.parent / "session_unrelated"  # Prove cleanup does not delete a different marker.
            logging.info("Write the unrelated owned marker %s", other)  # Mark the isolation fixture write.
            other.write_text("other session\n", encoding="utf-8")  # Keep this marker outside the active session name.
            logging.debug("Unrelated owned marker exists at %s", other)  # Report no sensitive content.
            with patch("subprocess.run", side_effect=AssertionError("session replay must not require Git history")):
                script = BashSession.baseline(sandbox) if version == "base" else BashSession.SCRIPT
            observation = BashSession.run(sandbox, script, interruption)  # Let the existing traps choose the status.
            outcomes.append((observation.returncode, len(observation.records)))  # Retain actual exit and launch counts.
            assert observation.records[0]["argv"] == ["MistHelper.py"]  # Keep the exact original invocation.
            assert not marker.exists()  # The actual trap must remove its own marker.
            assert other.read_text(encoding="utf-8") == "other session\n"  # No other marker may disappear.
            assert pid_file.read_text(encoding="utf-8") == "existing PID sentinel\n"  # Keep the existing PID file.
            assert "Cleaning up session" in "\n".join(observation.logs)  # Prove actual trap execution.
        print(f"signal={interruption} base={outcomes[0]} live={outcomes[1]}")  # Retain exact measured codes.
        assert outcomes[0] == outcomes[1]  # Removing a setting must not change normal or signal outcomes.
        assert outcomes[0][1] == 1  # Every compared case must launch the actual recorder.

    def test_two_session_identifiers_remain_isolated(self, tmp_path: Path) -> None:
        """Two synthetic connections share a marker directory without deleting each other's files."""
        first = SessionSandbox.create(tmp_path / "first")  # Own the first application's paths.
        second = SessionSandbox.create(tmp_path / "second")  # Own the second application's paths.
        shared = tmp_path / "shared-sessions"  # Use one owned directory to expose cross-session deletion.
        first.environment["MISTHELPER_SESSION_DIR"] = str(shared)  # Keep both marker sets in the same directory.
        second.environment["MISTHELPER_SESSION_DIR"] = str(shared)  # Keep the second session in the same namespace.
        second.environment["SSH_CONNECTION"] = "2001:db8::10 55002 2001:db8::20 22"  # Include colon normalization.
        first_marker, first_pid = first.markers()  # Pre-create the first session's marker.
        second_marker, second_pid = second.markers()  # Pre-create the second session's marker.
        assert first_marker != second_marker  # The two connections must retain distinct normalized identifiers.
        assert first_marker.name == "session_192_0_2_10_55001_198_51_100_20_22"  # Preserve IPv4 normalization.
        assert second_marker.name == "session_2001_db8__10_55002_2001_db8__20_22"  # Preserve IPv6 normalization.
        first_result = BashSession.run(first)  # Execute the first actual session.
        assert first_result.returncode == 0 and len(first_result.records) == 1  # A clean session closes once.
        assert not first_marker.exists() and second_marker.exists()  # Remove only the first marker.
        second_result = BashSession.run(second)  # Execute the second actual session.
        assert second_result.returncode == 0 and len(second_result.records) == 1  # Preserve its independent clean exit.
        assert not second_marker.exists()  # Remove the second marker only after its session ends.
        assert (
            first_pid.read_text(encoding="utf-8") == second_pid.read_text(encoding="utf-8") == "existing PID sentinel\n"
        )


@pytest.mark.timeout(30)
class TestSessionRestarts:
    """Keep measured retry limits, delays, caps, healthy reset, and defaults."""

    @pytest.mark.parametrize(
        ("plan", "controls", "expected"),
        [
            (
                ((3, 0.0),),
                {"MISTHELPER_MAX_START_ATTEMPTS": "3"},
                (1, 3, [0, 0]),  # Permanent failures must stop at the exact attempt limit.
            ),
            (
                ((3, 0.0),),
                {
                    "MISTHELPER_MAX_START_ATTEMPTS": "4",
                    "MISTHELPER_RESTART_DELAY_SECONDS": "1",
                    "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "2",
                },
                (1, 4, [1, 2, 2]),  # Actual reported delays must double and stop at the cap.
            ),
            (
                ((3, 0.0), (3, 0.0), (3, 3.0), (3, 0.0), (0, 0.0)),
                {
                    "MISTHELPER_MAX_START_ATTEMPTS": "3",
                    "MISTHELPER_MIN_HEALTHY_SECONDS": "2",
                    "MISTHELPER_RESTART_DELAY_SECONDS": "1",
                    "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "2",
                },
                (0, 5, [1, 2, 1, 2]),  # A healthy run resets both the count and the delay.
            ),
        ],
    )
    def test_actual_restart_controls_match_base(
        self,
        tmp_path: Path,
        plan: tuple[tuple[int, float], ...],
        controls: dict[str, str],
        expected: tuple[int, int, list[int]],
    ) -> None:
        """Compare each exact result with actual Bash execution of the local base."""
        outcomes: list[tuple[int, int, list[int]]] = []  # Keep actual baseline and live measurements.
        for version in ("base", "live"):  # Keep each application's records and logs separate.
            sandbox = SessionSandbox.create(tmp_path / version, plan)  # Follow only the bounded synthetic plan.
            logging.info("Set the owned restart-control case")  # Mark the environment transformation.
            sandbox.environment.update(controls)  # Use only overrides already exposed by the script.
            logging.debug("Applied %s existing restart controls", len(controls))  # Never change a production default.
            script = BashSession.baseline(sandbox) if version == "base" else BashSession.SCRIPT  # Use actual sources.
            observation = BashSession.run(sandbox, script)  # Execute the real loop, not a duplicate calculation.
            result = (observation.returncode, len(observation.records), observation.delays)  # Read measured outcomes.
            outcomes.append(result)  # Keep both measurements for the evidence record.
            assert result == expected, observation.output  # Require exact counts, return code, and reported delays.
            assert observation.output.count("[SESSION] Starting MistHelper...") == expected[1]  # Count actual launches.
            assert all(record["argv"] == ["MistHelper.py"] for record in observation.records)  # Preserve invocation.
        print(f"restart base={outcomes[0]} live={outcomes[1]}")  # Retain exact baseline comparisons.
        assert outcomes[0] == outcomes[1]  # Keep every restart-control outcome unchanged.

    def test_original_restart_defaults_remain(self) -> None:
        """Keep five attempts, 30 healthy seconds, two initial seconds, and the 60-second cap."""
        defaults = {  # Read the real declarations rather than override the default behavior.
            "MAX_START_ATTEMPTS": ("MISTHELPER_MAX_START_ATTEMPTS", "5"),
            "MIN_HEALTHY_SECONDS": ("MISTHELPER_MIN_HEALTHY_SECONDS", "30"),
            "RESTART_DELAY_SECONDS": ("MISTHELPER_RESTART_DELAY_SECONDS", "2"),
            "MAX_RESTART_DELAY_SECONDS": ("MISTHELPER_MAX_RESTART_DELAY_SECONDS", "60"),
        }
        logging.info("Read the actual restart-default declarations")  # Mark the source read before the check.
        text = BashSession.SCRIPT.read_text(encoding="utf-8")  # Do not run the slow default failure sequence.
        logging.debug("Read %s actual session characters", len(text))  # Report source size, not credentials.
        for name, (environment, value) in defaults.items():  # Verify all four defaults.
            assert f'{name}="${{{environment}:-{value}}}"' in text  # Preserve every exact original default.
