"""Run actual Bash sessions with owned paths and a synthetic application."""

from __future__ import annotations  # Keep annotations passive during collection.

import json  # Store safe launch observations without token values.
import logging  # Report owned process and filesystem actions.
import os  # Terminate only the process group created by this harness.
import re  # Inspect session identifiers and reported restart delays.
import shlex  # Quote synthetic credentials in the controlled session file.
import signal  # Compare existing INT and TERM behavior with the local base.
import subprocess  # Execute the actual session script, never SSH or production startup.
import sys  # Run the recorder with this worktree's owned interpreter.
import time  # Bound the wait for a recorder launch.
from contextlib import ExitStack
from dataclasses import dataclass  # Keep input ownership and observations explicit.
from pathlib import Path  # Confine every operational path to tmp_path.
from types import TracebackType  # Type cleanup of an owned process lifetime.
from typing import Any, BinaryIO, cast  # Type JSON records and the captured output handle.

from tests.unit.container.bash_support import BASH_PATH, BASH_SKIP_REASON  # Reuse the read-only capability result.

from .contract import ContractCopies, SourceContract  # Compare the unchanged local base without another checkout.


class RecorderApplication:
    """Supply a bounded recorder instead of the production application."""

    TOKEN = 'synthetic-3314 token "local-only"'  # Exercise quoting without using a real credential.
    SOURCE = '''"""Record only safe session observations."""
import json  # Decode only the synthetic execution plan.
import logging  # Keep file operations visible without credentials.
import os  # Inspect the controlled environment.
import sys  # Retain the exact application arguments.
import time  # Model a bounded healthy application run.
from pathlib import Path  # Keep recorder storage below tmp_path.


class SyntheticApplication:
    """Record one launch and follow the owned execution plan."""

    @staticmethod
    def run() -> None:
        logging.basicConfig(level=logging.INFO)  # Show safe operation boundaries.
        destination = Path(os.environ["MISTHELPER_RECORDER_FILE"])  # Use the explicit owned record path.
        logging.info("Read the owned launch count")  # Log before the recorder read.
        count = len(destination.read_text(encoding="utf-8").splitlines()) if destination.exists() else 0
        logging.debug("Prior launch count is %s", count)  # Report a count, never credential data.
        logging.info("Inspect the synthetic launch environment")  # Log before building safe observations.
        expected = os.environ["MISTHELPER_EXPECTED_TOKEN"]  # Compare internally without recording the value.
        aliases = ("MIST_APITOKEN", "MIST_API_TOKEN")  # Keep both existing token names covered.
        record = {"argv": sys.argv, "output_format": os.environ.get("OUTPUT_FORMAT")}  # Preserve the inherited value.
        record["token_matches"] = {name: os.environ.get(name) == expected for name in aliases}  # Store booleans only.
        record["paths"] = {name: os.environ[name] for name in ("DATABASE_PATH", "HOME", "TMPDIR")}  # Prove isolation.
        logging.debug("Prepared safe launch %s", count + 1)  # Never log the token or the environment.
        logging.info("Write the owned safe launch record")  # Log before the actual recorder write.
        with destination.open("a", encoding="utf-8") as handle:  # Store only safe observations.
            handle.write(json.dumps(record) + "\\n")  # Preserve one record for each actual launch.
        logging.debug("Wrote safe launch %s", count + 1)  # Report only the measured launch count.
        logging.info("Run the bounded synthetic application plan")  # Mark the controlled delay and exit.
        plan = json.loads(os.environ["MISTHELPER_RECORDER_PLAN"])  # Use no production application behavior.
        code, duration = plan[min(count, len(plan) - 1)]  # Repeat only the final synthetic outcome.
        time.sleep(duration)  # Model a healthy run without a resource or network call.
        logging.debug("Synthetic application exit code is %s", code)  # Preserve the requested exit outcome.
        sys.exit(code)  # Let the actual Bash loop decide whether to restart.


SyntheticApplication.run()  # Execute only this synthetic application.
'''


@dataclass
class SessionSandbox:
    """Own every path and environment value supplied to a real session."""

    root: Path  # Confine app, environment, logs, home, temp, markers, and database paths.
    environment: dict[str, str]  # Supply an allowlist rather than copying ambient credentials.
    CONTROLS = {  # Keep default test retries short without modifying the script.
        "MISTHELPER_MAX_START_ATTEMPTS": "3",
        "MISTHELPER_MIN_HEALTHY_SECONDS": "30",
        "MISTHELPER_RESTART_DELAY_SECONDS": "0",
        "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "0",
    }

    @classmethod
    def create(cls, root: Path, plan: tuple[tuple[int, float], ...] = ((0, 0.0),)) -> SessionSandbox:
        """Prepare a synthetic recorder and a controlled database-path override."""
        for directory in ("app/data", "sessions", "home", "tmp"):  # Create only this test's operational directories.
            logging.info("Create owned session directory %s", root / directory)  # Log before filesystem writes.
            (root / directory).mkdir(parents=True, exist_ok=True)  # No default container path may receive a write.
            logging.debug("Owned session directory exists at %s", root / directory)  # Report the completed write.
        logging.info("Write the owned synthetic application")  # Mark the recorder application write.
        (root / "app" / "MistHelper.py").write_text(RecorderApplication.SOURCE, encoding="utf-8", newline="\n")
        logging.debug("Wrote %s synthetic application characters", len(RecorderApplication.SOURCE))  # Report only size.
        logging.info("Write the controlled session environment")  # Mark the safe database-path override.
        database = shlex.quote(str(root / "app" / "data" / "mist_data.db"))  # Quote only an owned path.
        (root / "session.env").write_text("DATABASE_PATH=" + database + "\n", encoding="utf-8", newline="\n")
        logging.debug("Controlled session environment is below %s", root)  # Do not report credential values.
        environment = cls.clean_environment(root)  # Exclude BASH_ENV and every ambient token.
        environment["MISTHELPER_RECORDER_PLAN"] = json.dumps(plan)  # Keep the execution plan case-local.
        return cls(root, environment)  # Retain this one test's operational ownership.

    @classmethod
    def clean_environment(cls, root: Path) -> dict[str, str]:
        """Build the complete clean environment from owned paths and synthetic values."""
        logging.info("Build the allowlisted synthetic session environment")  # Mark the environment transformation.
        environment = {  # Every operational path is explicit and below this test root.
            "PATH": os.defpath,
            "HOME": str(root / "home"),  # Use only the system shell tools and owned home.
            "TMPDIR": str(root / "tmp"),
            "LANG": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",  # Keep recorder imports local.
            "MISTHELPER_APP_DIR": str(root / "app"),  # Replace only the application executed by the real script.
            "MISTHELPER_SESSION_DIR": str(root / "sessions"),  # Keep markers and PID files owned.
            "MISTHELPER_SESSION_ENV_FILE": str(root / "session.env"),  # Never read a production environment file.
            "MISTHELPER_LOG_FILE": str(root / "app" / "data" / "ssh.log"),  # Own the session log.
            "MISTHELPER_RUNTIME_LOG_FILE": str(root / "app" / "data" / "script.log"),  # Own the runtime log path.
            "MISTHELPER_PYTHON": sys.executable,  # Use the already restored worktree interpreter.
            "MISTHELPER_RECORDER_FILE": str(root / "app" / "data" / "launches.jsonl"),  # Own safe records.
            "MISTHELPER_EXPECTED_TOKEN": RecorderApplication.TOKEN,  # Compare tokens internally, never print them.
            "MIST_APITOKEN": RecorderApplication.TOKEN,  # Open the credential gate with a synthetic value.
            "MISTHELPER_STANDALONE": "true",  # Keep any optional remote write decision inactive.
            "SSH_CONNECTION": "192.0.2.10 55001 198.51.100.20 22",  # Use reserved documentation addresses.
        }
        environment.update(cls.CONTROLS)  # Bound retry tests without changing production defaults.
        logging.debug("Allowlisted session environment has %s names", len(environment))  # Never log environment values.
        return environment  # Pass no ambient credentials, BASH_ENV, or cloud settings.

    def credential(self, alias: str | None, source: str) -> None:
        """Transfer one synthetic alias from the environment or controlled file."""
        logging.info("Prepare synthetic credential source %s", source)  # Name the source without a value.
        for name in ("MIST_APITOKEN", "MIST_API_TOKEN"):  # Keep each transfer case independent.
            self.environment.pop(name, None)  # Remove only the harness's synthetic aliases.
        path = self.root / "session.env"  # Keep the database override in the controlled file.
        text = "DATABASE_PATH=" + shlex.quote(str(self.root / "app" / "data" / "mist_data.db")) + "\n"
        if alias is not None and source == "file":  # Model entrypoint transfer without invoking the writer.
            text += alias + "=" + shlex.quote(RecorderApplication.TOKEN) + "\n"  # Preserve spaces and a quotation mark.
        elif alias is not None:  # Model an already supplied synthetic session environment.
            self.environment[alias] = RecorderApplication.TOKEN  # Never copy a host credential.
        path.write_text(text, encoding="utf-8", newline="\n")  # Keep every session-file write under tmp_path.
        logging.debug(
            "Synthetic credential configured=%s from %s", alias is not None, source
        )  # Do not expose its value.

    def markers(self) -> tuple[Path, Path]:
        """Pre-create the session marker and existing PID file without owning another process."""
        logging.info("Prepare the owned session marker and existing PID file")  # Mark the fixture filesystem operation.
        identifier = re.sub(r"[ :.]", "_", self.environment["SSH_CONNECTION"])  # Match the existing normalization.
        directory = Path(self.environment["MISTHELPER_SESSION_DIR"])  # Allow two sessions to share an owned directory.
        directory.mkdir(parents=True, exist_ok=True)  # Never create a production session directory.
        marker, pid_file = directory / ("session_" + identifier), directory / ("pid_" + identifier)  # Keep exact names.
        marker.write_text("owned marker\n", encoding="utf-8")  # Let the actual cleanup remove only its own marker.
        pid_file.write_text(
            "existing PID sentinel\n", encoding="utf-8"
        )  # Never terminate a process named by this file.
        logging.debug("Prepared marker %s and PID file %s", marker, pid_file)  # Report safe owned paths.
        return marker, pid_file  # Tests check the original PID-file treatment.


@dataclass(frozen=True)
class SessionObservation:
    """Retain safe results from the actual session and recorder."""

    returncode: int  # Preserve the real script outcome, including signals.
    output: str  # Keep exact launch, cleanup, and restart messages.
    records: tuple[dict[str, Any], ...]  # Retain arguments, format, booleans, and owned paths only.
    logs: tuple[str, ...]  # Inspect every owned log for disclosure.

    @classmethod
    def read(cls, sandbox: SessionSandbox, returncode: int) -> SessionObservation:
        """Read only outputs below the owned sandbox."""
        logging.info("Read owned session evidence below %s", sandbox.root)  # Mark the actual evidence reads.
        output = (sandbox.root / "app" / "data" / "stdout.log").read_text(encoding="utf-8")  # Retain captured output.
        destination = Path(sandbox.environment["MISTHELPER_RECORDER_FILE"])  # Use the explicitly owned record path.
        records = (
            tuple(json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines())
            if destination.exists()
            else ()
        )
        logs = tuple(
            path.read_text(encoding="utf-8") for path in sandbox.root.rglob("*.log")
        )  # Inspect every owned log.
        logging.debug(
            "Read %s launch records and %s logs", len(records), len(logs)
        )  # Report counts, never credentials.
        return cls(returncode, output, cast(tuple[dict[str, Any], ...], records), logs)  # Keep the actual results.

    @property
    def delays(self) -> list[int]:
        """Read the restart delays reported by the unchanged loop."""
        logging.info("Inspect reported session restart delays")  # Mark the output transformation.
        delays = [
            int(value) for value in re.findall(r"Next start in (\d+) seconds", self.output)
        ]  # Read actual reports.
        logging.debug("Read %s restart delays", len(delays))  # Retain the measured delay count.
        return delays  # Do not reproduce the production backoff calculation.

    def require_no_disclosure(self) -> None:
        """Require all captured output, owned logs, and records to exclude token values."""
        assert RecorderApplication.TOKEN not in self.output  # The terminal must not disclose a credential.
        assert all(RecorderApplication.TOKEN not in text for text in self.logs)  # Every owned log must stay safe.
        assert RecorderApplication.TOKEN not in json.dumps(self.records)  # Records must contain booleans, not tokens.


class OwnedProcess:
    """Own one isolated process group and release it on every exit path."""

    def __init__(self, sandbox: SessionSandbox, script: Path) -> None:
        """Store process ownership before opening an output file or starting Bash."""
        self.sandbox = sandbox  # Retain the clean environment and owned paths.
        self.script = script  # Execute the actual script or its immutable base copy.
        self.process: subprocess.Popen[bytes] | None = None  # No process exists before context entry.
        self.handle: BinaryIO | None = None  # No log handle exists before context entry.

    def __enter__(self) -> OwnedProcess:
        """Start actual Bash with no ambient credentials or startup file."""
        executable = BashSession.capability()
        logging.info("Start an owned Bash session for %s", self.script)
        output = self.sandbox.root / "app" / "data" / "stdout.log"
        with ExitStack() as cleanup:
            self.handle = cleanup.enter_context(output.open("wb"))
            self.process = subprocess.Popen(
                [executable, str(self.script)],
                cwd=self.sandbox.environment["MISTHELPER_APP_DIR"],
                env=self.sandbox.environment,
                stdin=subprocess.DEVNULL,
                stdout=self.handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            cleanup.pop_all()  # Transfer handle cleanup only after the process starts.
        logging.debug("Started owned Bash PID %s", self.process.pid)
        return self

    def interrupt(self, interruption: signal.Signals) -> None:
        """Send a signal only after this recorder proves an application launch."""
        assert self.process is not None  # Signals must never target an absent or unrelated process.
        destination = Path(self.sandbox.environment["MISTHELPER_RECORDER_FILE"])  # Wait only for this owned recorder.
        deadline = time.monotonic() + BashSession.TIMEOUT  # Bound launch synchronization at 30 seconds.
        logging.info("Wait for the owned recorder before signal %s", interruption.name)  # Mark the synchronization.
        while not destination.exists() or destination.stat().st_size == 0:  # A completed record proves the launch.
            if self.process.poll() is not None:  # A missing-token exit must not become a signal to another process.
                raise RuntimeError(
                    "owned session ended before the recorder launched"
                )  # Retain the missing-launch cause.
            if time.monotonic() >= deadline:  # A missing recorder must fail instead of silently skipping signals.
                raise subprocess.TimeoutExpired("owned recorder launch", BashSession.TIMEOUT)  # Preserve the timeout.
            time.sleep(0.01)  # Avoid a busy loop while the owned application starts.
        self.process.send_signal(interruption)  # Target only the PID that this context created.
        logging.debug("Sent %s to owned PID %s", interruption.name, self.process.pid)  # Report no token or environment.

    def wait(self) -> int:
        """Wait at most 30 seconds for the owned session outcome."""
        assert self.process is not None  # A wait cannot establish ownership for an unrelated PID.
        logging.info("Wait for owned Bash PID %s", self.process.pid)  # Mark the bounded process wait.
        returncode = self.process.wait(timeout=BashSession.TIMEOUT)  # Preserve the actual script exit code.
        logging.debug("Owned Bash PID %s returned %s", self.process.pid, returncode)  # Retain the baseline outcome.
        return returncode  # Let tests compare baseline and repaired behavior.

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop only this context's unfinished descendants and close its log."""
        if self.process is not None and self.process.poll() is None:  # A timeout must not leave this child running.
            logging.info("Stop unfinished owned process group %s", self.process.pid)  # Mark exact owned cleanup.
            os.killpg(self.process.pid, signal.SIGKILL)  # The new session contains only this harness's descendants.
            self.process.wait(timeout=BashSession.TIMEOUT)  # Reap the exact owned child.
            logging.debug("Stopped owned process group %s", self.process.pid)  # Report the completed cleanup.
        if self.handle is not None:  # Context setup may fail before an output handle opens.
            self.handle.close()  # Release the owned output file on success and failure.


class BashSession:
    """Run actual syntax and behavior checks through the existing Bash capability."""

    TIMEOUT = 30  # Match every new session subprocess and pytest timeout.
    SCRIPT = SourceContract.REPOSITORY / SourceContract.PATHS[0]  # Use the actual repository session script.

    @staticmethod
    def capability() -> str:
        """Fail explicitly when the existing Bash capability is unavailable."""
        if BASH_SKIP_REASON is not None or BASH_PATH is None:  # Presence alone does not prove path compatibility.
            raise RuntimeError("required Bash capability unavailable: " + str(BASH_SKIP_REASON))  # Never pass a skip.
        return BASH_PATH  # Reuse the existing read-only capability result.

    @classmethod
    def syntax(cls, path: Path, sandbox: SessionSandbox) -> subprocess.CompletedProcess[str]:
        """Parse the actual script or an owned invalid copy without execution."""
        logging.info("Parse Bash source %s", path)  # Mark actual Bash parsing before the subprocess.
        result = subprocess.run(  # Keep actual parser diagnostics and status.
            [cls.capability(), "-n", str(path)],  # Run no command inside the script.
            env=sandbox.environment,
            cwd=sandbox.root,  # Exclude BASH_ENV and ambient credentials.
            capture_output=True,
            text=True,
            timeout=cls.TIMEOUT,
            check=False,  # Preserve intentional syntax failures.
        )
        logging.debug("Bash parsing returned %s for %s", result.returncode, path)  # Report the exact source path.
        return result  # A malformed input must remain a nonzero result.

    @classmethod
    def baseline(cls, sandbox: SessionSandbox) -> Path:
        """Write immutable original script bytes below this test's own root."""
        logging.info("Read the measured original session source")
        current = cls.SCRIPT.read_bytes().decode("utf-8")
        original = ContractCopies.original(0, current).encode("utf-8")
        logging.debug("Verified %s original session bytes", len(original))
        path = sandbox.root / "original-session.sh"  # Keep immutable copies outside the checkout.
        logging.info("Write owned original session copy %s", path)  # Mark the controlled baseline write.
        path.write_bytes(original)
        logging.debug("Wrote %s original bytes to %s", len(original), path)
        return path  # Compare actual Bash execution against this source.

    @classmethod
    def run(
        cls, sandbox: SessionSandbox, script: Path | None = None, interruption: signal.Signals | None = None
    ) -> SessionObservation:
        """Execute one bounded session and retain its safe observations."""
        with OwnedProcess(sandbox, cls.SCRIPT if script is None else script) as owned:  # Own every descendant.
            if interruption is not None:  # Compare only requested signal scenarios.
                owned.interrupt(interruption)  # Signal the exact owned session after a recorder launch.
            returncode = owned.wait()  # Keep the real session's return code.
        observation = SessionObservation.read(sandbox, returncode)  # Read outputs only after closing the writer.
        observation.require_no_disclosure()  # Never report a session with a leaked token as passing.
        return observation  # Preserve the actual arguments, counts, delays, and outcome.
