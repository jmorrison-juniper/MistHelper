"""Unit tests for the writer of the session configuration file, issue #2181.

Why:
    `compose.yml` supplies the credentials through `env_file`, which fills the
    environment of the container process and writes no file. The SSH daemon
    starts each session with a fresh environment, so no credential reached an
    SSH session. MistHelper then refused five times in a row, and the operator
    read a login loop.

    `container/scripts/write-session-env.sh` closes that gap. The entrypoint
    runs it as root at container start, and the session script reads the file
    that it writes.

    The file holds the Mist API token, so these tests also guard the mode and
    the allowlist. A wider mode would expose the token to every account of the
    container, and a blind copy of the environment would write the SSH password
    to disk.

Scope:
    The writer script only. No test starts a container, and no test reaches the
    Mist cloud.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import os  # The writer reads its values from the environment.
import shutil  # The test needs the path of bash.
import stat  # One test reads the permission bits of the finished file.
import subprocess  # The test runs a shell script.
from pathlib import Path  # Every path in this module is a Path.

import pytest  # The test framework of the project.

# Find the repository root, because pytest moves the working directory.
REPO_ROOT = Path(__file__).resolve().parents[3]
# Point at the script under test.
WRITER_SCRIPT = REPO_ROOT / "container" / "scripts" / "write-session-env.sh"
# Locate bash, because the writer is a bash script.
BASH_PATH = shutil.which("bash")
# Stop a runaway script, because a hang must fail the test and not the suite.
HARNESS_TIMEOUT_SECONDS = 30

# Skip the module when bash is absent, because the script needs bash.
pytestmark = pytest.mark.skipif(BASH_PATH is None, reason="bash is required to run the writer script")

# The account that owns the finished file inside the container. A test runs as
# one account, so the writer treats a failed change of owner as harmless.
OWNER_NAME = "misthelper"


def _run_writer(target: Path, values: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the writer with a fixed environment and return the finished process.

    Args:
        target: The path of the file that the writer builds.
        values: The variables that the writer may read.

    Returns:
        The finished process, which carries the status and the output.
    """
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}  # Start clean, so no real token reaches the file.
    env.update(values)  # Apply the values that this test states.
    return subprocess.run(
        [str(BASH_PATH), WRITER_SCRIPT.as_posix(), OWNER_NAME, target.as_posix()],
        capture_output=True,  # Keep the report line for the assertions.
        text=True,  # Decode the output for the message.
        timeout=HARNESS_TIMEOUT_SECONDS,  # Apply the hard timeout, because a hang must not stop the suite.
        env=env,  # Pass the fixed environment.
        check=False,  # Keep the status, because one test proves a clean status.
    )


def test_the_script_parses_under_bash() -> None:
    """A syntax fault would stop every container start."""
    result = subprocess.run(
        [str(BASH_PATH), "-n", WRITER_SCRIPT.as_posix()],  # Ask bash to parse the script without a run.
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr  # A non-zero status names the line of the fault.


def test_the_writer_carries_the_token_and_the_host(tmp_path: Path) -> None:
    """The preflight reads both names, so both must reach the session."""
    target = tmp_path / "session.env"
    _run_writer(target, {"MIST_APITOKEN": "a-token", "MIST_HOST": "api.mist.com"})

    written = target.read_text(encoding="utf-8")
    assert "MIST_APITOKEN=a-token" in written  # The token reaches the file.
    assert "MIST_HOST=api.mist.com" in written  # The host reaches the file.


def test_the_finished_file_is_readable_by_its_owner_alone(tmp_path: Path) -> None:
    """The file holds the API token, so no other account of the container reads it."""
    target = tmp_path / "session.env"
    _run_writer(target, {"MIST_APITOKEN": "a-token"})

    mode = stat.S_IMODE(target.stat().st_mode)  # Read the permission bits alone.
    assert mode == 0o400, oct(mode)  # A wider mode would expose the token.


def test_a_variable_outside_the_allowlist_never_reaches_the_file(tmp_path: Path) -> None:
    """A blind copy of the environment would write the SSH password to disk."""
    target = tmp_path / "session.env"
    _run_writer(
        target,
        {
            "MIST_APITOKEN": "a-token",
            "MISTHELPER_SSH_PASSWORD": "the-ssh-password",  # A real secret of the container.
            "AWS_SECRET_ACCESS_KEY": "an-unrelated-secret",  # A secret of another system.
        },
    )

    written = target.read_text(encoding="utf-8")
    assert "the-ssh-password" not in written  # The SSH password stays out of the file.
    assert "an-unrelated-secret" not in written  # Every unrelated secret stays out as well.


def test_an_empty_variable_never_reaches_the_file(tmp_path: Path) -> None:
    """An empty value would override a default that MistHelper would otherwise use."""
    target = tmp_path / "session.env"
    _run_writer(target, {"MIST_APITOKEN": "a-token", "MIST_ORG_ID": ""})

    assert "MIST_ORG_ID" not in target.read_text(encoding="utf-8")  # The empty name stays out.


def test_the_report_names_the_variables_and_prints_no_value(tmp_path: Path) -> None:
    """The report reaches the log file, which every reader of the data volume opens."""
    target = tmp_path / "session.env"
    result = _run_writer(target, {"MIST_APITOKEN": "a-secret-token", "MIST_HOST": "api.mist.com"})

    assert "MIST_APITOKEN" in result.stdout  # The report names the variable.
    assert "a-secret-token" not in result.stdout  # The report holds no token value.
    assert "a-secret-token" not in result.stderr  # No error path leaks the value either.


def test_a_value_with_a_space_and_a_quotation_mark_reads_back_whole(tmp_path: Path) -> None:
    """A lost character would send a broken token to the Mist cloud."""
    target = tmp_path / "session.env"
    awkward = 'tok en"with$specials'  # A space, a quotation mark, and a dollar sign together.
    _run_writer(target, {"MIST_APITOKEN": awkward})

    # Read the value back the way the session script does, which is a source
    # under `set -a`. A test that read the raw line would prove nothing about
    # the shell that consumes it.
    read_back = subprocess.run(
        [str(BASH_PATH), "-c", f'set -a; source "{target.as_posix()}"; printf "%s" "$MIST_APITOKEN"'],
        capture_output=True,
        text=True,
        timeout=HARNESS_TIMEOUT_SECONDS,
        check=False,
    )
    assert read_back.stdout == awkward, read_back.stdout  # The value survives the round trip.


def test_a_second_run_replaces_every_earlier_value(tmp_path: Path) -> None:
    """A stale token from an earlier container start must never survive a restart."""
    target = tmp_path / "session.env"
    _run_writer(target, {"MIST_APITOKEN": "the-first-token"})
    _run_writer(target, {"MIST_APITOKEN": "the-second-token"})

    written = target.read_text(encoding="utf-8")
    assert "the-first-token" not in written  # The earlier value is gone.
    assert "the-second-token" in written  # The current value stands alone.


def test_the_writer_builds_a_missing_directory(tmp_path: Path) -> None:
    """The container holds no /etc/misthelper directory before the first start."""
    target = tmp_path / "absent" / "misthelper" / "session.env"
    result = _run_writer(target, {"MIST_APITOKEN": "a-token"})

    assert result.returncode == 0, result.stderr  # The writer reports success.
    assert target.exists()  # The file reached the new directory.


def test_a_run_with_no_named_variable_writes_an_empty_file(tmp_path: Path) -> None:
    """A container with no configuration must still leave a readable file."""
    target = tmp_path / "session.env"
    result = _run_writer(target, {})

    assert result.returncode == 0, result.stderr  # The writer never fails on an empty environment.
    assert target.read_text(encoding="utf-8") == ""  # The file holds nothing, so the session refuses later.
    assert "Carried 0 configuration name(s)" in result.stdout  # The report names the count, so the operator sees it.
