"""Guard the portal access log fields (issue #3217) and the launch quoting (issue #4157)."""

import os  # Read the search path, so the stub runs before the real tools.
import re  # Find the assignment and the launch lines in start.sh.
import shlex  # Quote the test folder, so the shell reads one path.
import shutil  # Check whether bash exists on the test host.
import subprocess  # Run each launch line in bash.
import sys  # Detect Windows, where the POSIX launch line cannot run.
from pathlib import Path  # Build paths from this test file.

import pytest  # Mark the bash tests with a skip condition.

START_SCRIPT = Path(__file__).resolve().parents[3] / "container" / "scripts" / "start.sh"
ACCESS_LOG_FORMAT = (
    'ACCESS_LOG_FORMAT=\'%(h)s %(l)s %(u)s %(t)s "%(r)s" '
    "status=%(s)s bytes=%(b)s response_time_us=%(D)s "
    "refusal_code=%({X-MistHelper-Refusal-Code}o)s'"
)


def test_start_script_defines_safe_access_fields() -> None:
    """The fixed Gunicorn format names timing and refusal fields."""
    source = START_SCRIPT.read_text(encoding="utf-8")
    assert ACCESS_LOG_FORMAT in source
    assert source.count("--access-logformat '$ACCESS_LOG_FORMAT'") == 2  # Both launch lines keep the single quotes.


FORMAT_VALUE = ACCESS_LOG_FORMAT.split("=", 1)[1][1:-1]  # The format text without its single quotes.
ASSIGNMENT_LINE = re.compile(r"^ACCESS_LOG_FORMAT=.*$", re.MULTILINE)  # The assignment with its trailing comment.
LAUNCH_LINE = re.compile(  # Each su launch line, with its gunicorn command in group one.
    r'^su misthelper -c "(cd /app && gunicorn (?:wsgi|wsgi_capture):app .*?)" &$',
    re.MULTILINE | re.DOTALL,
)
REQUIRES_POSIX_BASH = pytest.mark.skipif(  # Skip on Windows, where bash can be WSL and cannot read the test paths.
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="the launch line needs a POSIX bash",
)
GUNICORN_STUB = '#!/bin/sh\nprintf "%s\\0" "$@" > "$ARGV_FILE"\n'  # Record each argument, separated by NUL.
SU_STUB = 'su() { shift 2; sh -c "$@"; }'  # Run the -c string in a child shell and pass extra words, as su does.


@REQUIRES_POSIX_BASH
@pytest.mark.parametrize("entrypoint", ["wsgi:app", "wsgi_capture:app"])
def test_gunicorn_receives_the_access_log_format_as_one_argument(tmp_path: Path, entrypoint: str) -> None:
    """Run each launch line in bash and check the argument that Gunicorn receives."""
    source = START_SCRIPT.read_text(encoding="utf-8")  # Read the launch script as text.
    launch = next(  # Pick this portal's launch line from the two in start.sh.
        match for match in LAUNCH_LINE.findall(source) if f"gunicorn {entrypoint} " in match
    )
    stub_dir = tmp_path / "bin"  # Hold the gunicorn stub on the search path.
    stub_dir.mkdir()  # Create the folder before the stub is written.
    gunicorn_stub = stub_dir / "gunicorn"  # The stub replaces the real Gunicorn.
    gunicorn_stub.write_text(GUNICORN_STUB, encoding="utf-8")  # Write the argument recorder.
    gunicorn_stub.chmod(0o755)  # Make the stub executable for the shell.
    argv_file = tmp_path / "argv.bin"  # The stub writes the received arguments here.
    # Run in the test folder, because this test host has no /app.
    launch_in_folder = launch.replace("cd /app", f"cd {shlex.quote(str(tmp_path))}", 1)
    script = tmp_path / "launch.sh"  # The bash script that runs the launch line.
    script_lines = [
        "WEB_PORT=8055",  # Give the port variables the values that compose sets.
        "CAPTURE_PORT=8056",
        "PORTAL_THREADS=24",
        "SHUTDOWN_GRACE_SECONDS=30",
        ASSIGNMENT_LINE.search(source).group(0),  # Use the real assignment from start.sh.
        SU_STUB,  # Stand in for su, so the test runs without root.
        f'su misthelper -c "{launch_in_folder}"',  # Run the real launch line.
    ]
    script.write_text("\n".join(script_lines) + "\n", encoding="utf-8")  # Write the script for bash.
    environment = {  # Put the stub first on PATH and pass the output path.
        **os.environ,
        "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
        "ARGV_FILE": str(argv_file),
    }
    result = subprocess.run(  # Run the launch script once, with a deadline.
        ["bash", str(script)],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr  # A shell error in the launch line fails here.
    assert argv_file.exists(), "gunicorn did not start"  # No record means the stub never ran.
    arguments = argv_file.read_bytes().split(b"\0")[:-1]  # Split the NUL-separated arguments.
    position = arguments.index(b"--access-logformat")  # Find the format option.
    assert arguments[position + 1] == FORMAT_VALUE.encode()  # The whole format arrives as one argument.
