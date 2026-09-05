"""Tests for the restart loop in the SSH session script.

The script ``container/scripts/misthelper-session.sh`` starts MistHelper for
each SSH session. The script restarts MistHelper when a run fails. A permanent
fault, such as a missing dependency, makes every run fail. An unbounded loop
then burns container CPU and fills the log file. See issue #1911.

Each test runs the real script with a stub in place of MistHelper. Each test
uses a hard timeout, so a lost limit fails the test instead of a hang. The
script writes to a file and not to a pipe, because a killed shell leaves a
sleep child that holds a pipe open.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from tests.unit.container.bash_support import BASH_PATH, BASH_SKIP_REASON

# Find the repository root, because pytest moves the working directory.
REPO_ROOT = Path(__file__).resolve().parents[3]
# Point at the script under test.
SESSION_SCRIPT = REPO_ROOT / "container" / "scripts" / "misthelper-session.sh"
# Stop a runaway loop, because a lost limit must fail the test and not hang it.
HARNESS_TIMEOUT_SECONDS = 60

# Skip the module when no bash can open the script. A bash that refuses a
# Windows path reaches this guard too, because the presence of bash proves
# nothing on Windows. Read tests/unit/container/bash_support.py for the reason.
pytestmark = pytest.mark.skipif(BASH_SKIP_REASON is not None, reason=BASH_SKIP_REASON or "")

# The token that every loop test carries. Issue #2181 makes the script refuse a
# session with no token, so a loop test must supply one. No test reaches the
# Mist cloud, so the value only has to be present.
STAND_IN_TOKEN = "stand-in-token-for-the-session-tests"

# Fail at once with a fixed code, because a startup defect fails at once.
ALWAYS_FAILS_STUB = "#!/bin/bash\nexit 3\n"
# Exit with success, because menu option 0 ends a session.
CLEAN_EXIT_STUB = "#!/bin/bash\nexit 0\n"
# Fail twice after a long run, then exit clean. A long run is a real session,
# so the script must clear the crash count after each long run.
LONG_RUN_THEN_CLEAN_STUB = """#!/bin/bash
COUNT_FILE="./data/run_count"
COUNT=0
if [[ -f "$COUNT_FILE" ]]; then
    COUNT=$(cat "$COUNT_FILE")
fi
COUNT=$(( COUNT + 1 ))
echo "$COUNT" > "$COUNT_FILE"
if [[ $COUNT -ge 3 ]]; then
    exit 0
fi
sleep 2
exit 1
"""


def _build_fake_app(tmp_path: Path, stub_body: str) -> Path:
    """Build a directory that takes the place of /app inside the container.

    The session script runs the command ``$MISTHELPER_PYTHON MistHelper.py``.
    A test sets ``MISTHELPER_PYTHON`` to ``bash``, so the stub is a shell
    script that carries the name of the Python entry point.
    """
    app_dir = tmp_path / "app"  # Keep the fake application outside the repository.
    (app_dir / "data").mkdir(parents=True)  # Create the data directory, because the script appends to data/ssh.log.
    stub_path = app_dir / "MistHelper.py"  # Use the name that the session script starts.
    stub_path.write_text(stub_body, encoding="ascii", newline="\n")  # Write LF endings, because bash rejects a CR.
    stub_path.chmod(0o755)  # Grant the execute bit, because a POSIX runner needs it.
    return app_dir  # Give the path back for the assertions.


def _run_session_script(app_dir: Path, overrides: dict[str, str]) -> tuple[int, str]:
    """Run the session script and return the exit status and the output."""
    env = os.environ.copy()  # Start from the real environment, because bash needs PATH.
    env["MISTHELPER_APP_DIR"] = app_dir.as_posix()  # Point the script at the fake application directory.
    env["MISTHELPER_SESSION_DIR"] = (app_dir / "sessions").as_posix()  # Keep the session marker in the temporary tree.
    env["MISTHELPER_PYTHON"] = "bash"  # Run the stub with bash, because the stub is a shell script.
    # Issue #2181. The script refuses a session that holds no API token, so a
    # loop test needs one. The value is a stand-in, because no test reaches the
    # Mist cloud. The name of the real token never enters this environment.
    env["MIST_APITOKEN"] = STAND_IN_TOKEN
    env.pop("MIST_API_TOKEN", None)  # Keep one token name in play, so each test states its own condition.
    # Point at a path inside the temporary tree, so no test reads the real
    # configuration file of a container that runs on the same machine.
    env["MISTHELPER_SESSION_ENV_FILE"] = (app_dir / "session.env").as_posix()
    env.update(overrides)  # Apply the restart controls for this test.
    output_path = app_dir / "session_output.txt"  # Collect the output in a file, because a pipe blocks after a kill.
    with output_path.open("w", encoding="utf-8") as handle:
        status = subprocess.run(
            [str(BASH_PATH), SESSION_SCRIPT.as_posix()],  # Run the real script, because the test proves its behavior.
            stdout=handle,  # Send the screen output to the file.
            stderr=subprocess.STDOUT,  # Keep the error output with the screen output, because a fault prints there.
            timeout=HARNESS_TIMEOUT_SECONDS,  # Apply the hard timeout, because a lost limit must not hang the suite.
            env=env,  # Pass the overrides that select the test values.
            cwd=str(app_dir),  # Start in the fake application directory, because the stub reads a file there.
            check=False,  # Keep the failure status, because a give-up returns a non-zero status.
        ).returncode
    return status, output_path.read_text(encoding="utf-8", errors="replace")  # Read the output for the assertions.


def _run_or_fail(app_dir: Path, overrides: dict[str, str]) -> tuple[int, str]:
    """Run the script and turn a timeout into a clear test failure."""
    try:
        return _run_session_script(app_dir, overrides)  # Run the script under the hard timeout.
    except subprocess.TimeoutExpired:  # A timeout shows that the loop never stopped.
        pytest.fail(
            f"The session script did not stop within {HARNESS_TIMEOUT_SECONDS} seconds. "
            "The restart loop has no attempt limit."
        )


def _count_starts(output: str) -> int:
    """Count the start messages, because each message marks one attempt."""
    return output.count("[SESSION] Starting MistHelper...")  # Match the fixed message from the script.


class TestSessionRestartLoop:
    """Prove that the restart loop is bounded, patient, and clear."""

    def test_script_syntax_is_valid(self) -> None:
        """The script must parse, because a syntax error closes every session."""
        result = subprocess.run(
            [str(BASH_PATH), "-n", SESSION_SCRIPT.as_posix()],  # Ask bash to parse the script without a run.
            capture_output=True,  # Keep the output, because a failure names the line.
            text=True,  # Decode the output for the message.
            timeout=30,  # Bound the parse, because a hung parse hides a defect.
            check=False,  # Read the status in the assertion instead.
        )
        assert result.returncode == 0, result.stderr  # A non-zero status means a syntax error.

    def test_repeated_crash_stops_after_the_attempt_limit(self, tmp_path: Path) -> None:
        """A permanent fault must stop the loop and close the session."""
        app_dir = _build_fake_app(tmp_path, ALWAYS_FAILS_STUB)  # Build an application that always fails.
        status, output = _run_or_fail(
            app_dir,
            {
                "MISTHELPER_MAX_START_ATTEMPTS": "3",  # Use a small limit, because the test must stay fast.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",  # Use a short delay for the same reason.
                "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "1",  # Hold the delay flat, because this test reads the count.
                "MISTHELPER_MIN_HEALTHY_SECONDS": "30",  # Keep the normal threshold, because every run is short.
            },
        )

        assert _count_starts(output) == 3, output  # The script must try exactly three times.
        assert status != 0, output  # The session must report a failure to the SSH client.
        assert "failed 3 times in a row" in output, output  # The message must name the attempt count.
        assert "The last exit code was 3." in output, output  # The message must name the exit code.
        assert "script.log" in output, output  # The message must point at the runtime log.
        assert "ssh.log" in output, output  # The message must point at the session log.

    def test_give_up_message_reaches_the_session_log(self, tmp_path: Path) -> None:
        """The cause must stay in the log, because the screen goes away."""
        app_dir = _build_fake_app(tmp_path, ALWAYS_FAILS_STUB)  # Build an application that always fails.
        _run_or_fail(
            app_dir,
            {
                "MISTHELPER_MAX_START_ATTEMPTS": "2",  # Use the smallest useful limit for speed.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",  # Keep the single delay short.
                "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "1",  # Hold the delay flat.
                "MISTHELPER_MIN_HEALTHY_SECONDS": "30",  # Keep the normal threshold.
            },
        )

        log_text = (app_dir / "data" / "ssh.log").read_text(encoding="utf-8")  # Read the log that the operator keeps.
        assert "failed 2 times in a row" in log_text, log_text  # The log must hold the attempt count.
        assert "The last exit code was 3." in log_text, log_text  # The log must hold the exit code.

    def test_restart_delay_grows_and_stops_at_the_cap(self, tmp_path: Path) -> None:
        """The delay must double, and the cap must hold it."""
        app_dir = _build_fake_app(tmp_path, ALWAYS_FAILS_STUB)  # Build an application that always fails.
        _status, output = _run_or_fail(
            app_dir,
            {
                "MISTHELPER_MAX_START_ATTEMPTS": "4",  # Allow three delays before the give-up.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",  # Start the sequence at one second.
                "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "2",  # Cap the sequence at two seconds.
                "MISTHELPER_MIN_HEALTHY_SECONDS": "30",  # Keep the normal threshold.
            },
        )

        delays = [int(value) for value in re.findall(r"Next start in (\d+) seconds", output)]  # Read each delay.
        assert delays == [1, 2, 2], output  # The delay must double one time and then hold at the cap.

    def test_a_healthy_run_clears_the_crash_count(self, tmp_path: Path) -> None:
        """A long session must not spend the crash budget."""
        app_dir = _build_fake_app(tmp_path, LONG_RUN_THEN_CLEAN_STUB)  # Build an application with two long failures.
        status, output = _run_or_fail(
            app_dir,
            {
                "MISTHELPER_MAX_START_ATTEMPTS": "2",  # Give up on the second failure in a row.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",  # Keep each delay short.
                "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "1",  # Hold the delay flat.
                "MISTHELPER_MIN_HEALTHY_SECONDS": "1",  # Treat a run of one second or more as a real session.
            },
        )

        assert _count_starts(output) == 3, output  # Two long failures must not stop the third start.
        assert "User selected exit. Closing session." in output, output  # The third run ends the session.
        assert status == 0, output  # A clean exit must report success.
        assert "times in a row" not in output, output  # The script must not report a give-up.

    def test_clean_exit_closes_the_session_without_a_restart(self, tmp_path: Path) -> None:
        """Menu option 0 must keep its behavior, because operators rely on it."""
        app_dir = _build_fake_app(tmp_path, CLEAN_EXIT_STUB)  # Build an application that exits with success.
        status, output = _run_or_fail(
            app_dir,
            {
                "MISTHELPER_MAX_START_ATTEMPTS": "3",  # Use a small limit, because no restart is expected.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",  # Keep the value small for speed.
                "MISTHELPER_MAX_RESTART_DELAY_SECONDS": "1",  # Keep the value small for speed.
                "MISTHELPER_MIN_HEALTHY_SECONDS": "30",  # Keep the normal threshold.
            },
        )

        assert _count_starts(output) == 1, output  # A clean exit must start MistHelper one time.
        assert "User selected exit. Closing session." in output, output  # The clean message must stay.
        assert status == 0, output  # A clean exit must report success.


class TestSessionCredentials:
    """Prove that the session receives the token and refuses fast without one.

    Why:
        `compose.yml` supplies the credentials through `env_file`, which fills
        the environment of the container process and writes no file. The SSH
        daemon starts every session with a fresh environment, so no credential
        reached the session on its own. MistHelper then refused five times in a
        row, and the operator read a login loop. Issue #2181 holds that report.
    """

    def test_a_session_with_no_token_refuses_before_the_first_start(self, tmp_path: Path) -> None:
        """A missing token is permanent, so no start attempt may happen at all."""
        app_dir = _build_fake_app(tmp_path, CLEAN_EXIT_STUB)  # The stub would succeed, so only the gate can stop it.
        status, output = _run_or_fail(
            app_dir,
            {
                "MIST_APITOKEN": "",  # Clear the stand-in token of the harness.
                "MIST_API_TOKEN": "",  # Clear the second accepted name as well.
                "MISTHELPER_MAX_START_ATTEMPTS": "5",  # Keep the normal limit, so a loop would show.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",  # Keep the value small for speed.
            },
        )

        assert _count_starts(output) == 0, output  # The gate sits before the loop, so nothing starts.
        assert status == 1, output  # The session closes with a failure status.

    def test_the_refusal_names_the_cause_and_holds_no_token(self, tmp_path: Path) -> None:
        """The operator needs the cause, and the terminal keeps whatever it prints."""
        app_dir = _build_fake_app(tmp_path, CLEAN_EXIT_STUB)
        _, output = _run_or_fail(
            app_dir,
            {"MIST_APITOKEN": "", "MIST_API_TOKEN": "", "MISTHELPER_RESTART_DELAY_SECONDS": "1"},
        )

        assert "holds no Mist API token" in output, output  # The message names the missing item.
        assert "MIST_APITOKEN" in output, output  # The message names the variable that fixes it.
        assert "failed 5 times" not in output, output  # No retry loop repeats a permanent fault.

    def test_the_session_reads_the_token_from_the_configuration_file(self, tmp_path: Path) -> None:
        """The entrypoint writes that file, because the daemon passes no environment."""
        app_dir = _build_fake_app(tmp_path, CLEAN_EXIT_STUB)
        env_file = app_dir / "session.env"
        env_file.write_text("MIST_APITOKEN=from-the-file\n", encoding="ascii", newline="\n")

        status, output = _run_or_fail(
            app_dir,
            {
                "MIST_APITOKEN": "",  # The environment carries nothing, as in a real session.
                "MIST_API_TOKEN": "",
                "MISTHELPER_SESSION_ENV_FILE": env_file.as_posix(),
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",
            },
        )

        assert _count_starts(output) == 1, output  # The file satisfied the gate, so the session started.
        assert status == 0, output  # The stub exits clean, so the session ends clean.

    def test_a_token_with_a_space_and_a_quotation_mark_survives_the_file(self, tmp_path: Path) -> None:
        """`start.sh` quotes each value, so an unusual token must read back whole."""
        app_dir = _build_fake_app(
            tmp_path,
            '#!/bin/bash\necho "SEEN=[$MIST_APITOKEN]"\nexit 0\n',  # Print the value that reached the session.
        )
        env_file = app_dir / "session.env"
        # This is the exact form that `printf '%s=%q\\n'` writes for a value that
        # holds a space and a quotation mark.
        env_file.write_text('MIST_APITOKEN=tok\\ en\\"x\n', encoding="ascii", newline="\n")

        _, output = _run_or_fail(
            app_dir,
            {
                "MIST_APITOKEN": "",
                "MIST_API_TOKEN": "",
                "MISTHELPER_SESSION_ENV_FILE": env_file.as_posix(),
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",
            },
        )

        assert 'SEEN=[tok en"x]' in output, output  # A lost character would send a broken token to the cloud.

    def test_the_second_token_name_also_satisfies_the_gate(self, tmp_path: Path) -> None:
        """The preflight accepts either name, so the gate must accept both."""
        app_dir = _build_fake_app(tmp_path, CLEAN_EXIT_STUB)
        status, output = _run_or_fail(
            app_dir,
            {
                "MIST_APITOKEN": "",  # Leave the first name empty.
                "MIST_API_TOKEN": "the-second-name",  # Supply the second name alone.
                "MISTHELPER_RESTART_DELAY_SECONDS": "1",
            },
        )

        assert _count_starts(output) == 1, output  # The second name must open the gate.
        assert status == 0, output  # The session then runs as usual.
