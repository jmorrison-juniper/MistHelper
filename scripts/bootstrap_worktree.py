#!/usr/bin/env python3
"""Create the virtual environment that a new MistHelper worktree needs.

The command `git worktree add` copies the tracked files only. The directory
`.venv` is not tracked, so a new worktree holds no virtual environment. Without
that environment, pytest runs against the global interpreter, and every test
module fails to import. The reader then sees a source defect that does not
exist. Run this script one time in each new worktree. See issue #1866.

Usage:
    python scripts/bootstrap_worktree.py
    python scripts/bootstrap_worktree.py --recreate

The script works on Windows and on Linux. The script prints the path of the
interpreter that it created.

The script also protects the install against an unreachable pip index. It reads
the configured index one time, probes the host for 3 seconds, and falls back to
the public index for that run only. It never writes your pip configuration. See
issue #2000.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import socket
import subprocess  # nosec B404 - the script starts pip with a fixed argument list.
import sys
import time
import venv
from pathlib import Path
from urllib.parse import urlparse

LOGGER = logging.getLogger("bootstrap_worktree")

# The requirement files that the script installs, in this order. The script
# skips a file that the worktree does not hold.
REQUIREMENT_FILES: tuple[str, ...] = ("requirements.txt", "requirements-dev.txt")

# The public index that the script uses when the configured index does not
# answer. See issue #2000.
PUBLIC_INDEX_URL = "https://pypi.org/simple"

# The seconds that the script waits for the configured index to accept one TCP
# connection. A short wait keeps the probe cheap.
PROBE_TIMEOUT_SECONDS = 3.0

# The retry count and the socket timeout that the script gives to pip. pip
# retries 5 times with a 15 second timeout for each package by default, which
# costs about 75 seconds for each package against a dead index.
PIP_RETRIES = "1"
PIP_TIMEOUT = "15"

# The default port of each scheme that a pip index can use.
SCHEME_PORTS: dict[str, int] = {"http": 80, "https": 443}


class PipIndexProbe:
    """Report whether the configured pip index accepts a connection."""

    def __init__(self, interpreter: Path) -> None:
        """Store the interpreter that owns the pip configuration to read."""
        self.interpreter = interpreter  # Read the configuration of the new environment, not of the global one.

    def read_index_url(self) -> str | None:
        """Return the configured global index URL, or None when none is set."""
        command = [str(self.interpreter), "-m", "pip", "config", "list"]  # Ask pip for its effective settings.
        LOGGER.debug("Reading the pip configuration with %s", " ".join(command))
        try:  # A missing pip or a broken configuration must not stop the bootstrap.
            result = subprocess.run(  # nosec B603 - the argument list holds no shell input.
                command, check=False, capture_output=True, text=True, timeout=30
            )
        except (OSError, subprocess.SubprocessError) as error:  # Treat any failure as "no index configured".
            LOGGER.debug("The pip configuration read failed: %s", error)
            return None  # Report no index, because the caller then keeps the pip default.
        return self._parse_index_url(result.stdout)  # Pull the index line out of the report.

    @staticmethod
    def _parse_index_url(output: str) -> str | None:
        """Return the value of the global.index-url line of a pip config report."""
        for line in output.splitlines():  # The report holds one setting for each line.
            key, separator, value = line.partition("=")  # Split the setting name from its value.
            if not separator:  # A line without a separator carries no setting.
                continue  # Move to the next line of the report.
            if key.strip() not in ("global.index-url", "install.index-url"):  # Read the index setting only.
                continue  # Move to the next line of the report.
            return value.strip().strip("'\"") or None  # Remove the quotes that pip prints around the value.
        return None  # Report no index, because the report named none.

    def reaches(self, index_url: str) -> bool:
        """Open one short TCP connection to the index host and report the result."""
        parsed = urlparse(index_url)  # Split the URL, because the probe needs the host and the port.
        host = parsed.hostname  # Read the host without the credentials and without the port.
        if not host:  # A URL without a host cannot be probed.
            LOGGER.debug("The index URL %s carries no host", index_url)
            return True  # Report success, because the script must not override a value it cannot read.
        port = parsed.port or SCHEME_PORTS.get(parsed.scheme, 443)  # Use the explicit port, or the scheme default.
        LOGGER.debug("Probing the index host %s on port %d", host, port)
        try:  # A dead host raises here after the short timeout, not after 75 seconds.
            with socket.create_connection((host, port), timeout=PROBE_TIMEOUT_SECONDS):
                return True  # The host accepted the connection, so pip can reach it.
        except OSError as error:  # A refused, a filtered, or an unknown host lands here.
            LOGGER.debug("The index host %s did not answer: %s", host, error)
            return False  # Report the failure, so the caller can choose the public index.

    def fallback_index(self) -> str | None:
        """Return the public index when the configured index does not answer."""
        index_url = self.read_index_url()  # Read the index that pip would use for this run.
        if not index_url:  # No configured index means the pip default, which is the public index.
            LOGGER.debug("pip names no global index, so the script keeps the pip default")
            return None  # Report no override, because the default already points at the public index.
        if urlparse(index_url).hostname in ("pypi.org", "files.pythonhosted.org"):  # The public index needs no probe.
            LOGGER.debug("The configured index is already the public index")
            return None  # Report no override, because the configured index is the public one.
        if self.reaches(index_url):  # A reachable mirror stays in use, because it is faster than the public index.
            LOGGER.info("The configured pip index answered: %s", index_url)
            return None  # Report no override, because the mirror works.
        host = urlparse(index_url).hostname or index_url  # Name the host in the message that the user reads.
        LOGGER.warning(  # State the signal word and the consequence, as the writing guide requires.
            "Caution: the configured pip index host %s did not answer in %.0f seconds. "
            "The script uses %s for this run only. Your pip configuration is not changed.",
            host,
            PROBE_TIMEOUT_SECONDS,
            PUBLIC_INDEX_URL,
        )
        return PUBLIC_INDEX_URL  # Give the caller the index to use for this run.


class WorktreeBootstrapper:
    """Create one virtual environment and install the project dependencies."""

    def __init__(self, root: Path, venv_name: str = ".venv") -> None:
        """Store the worktree root and the name of the environment directory."""
        self.root = root  # Keep the worktree root, because every path starts here.
        self.venv_dir = root / venv_name  # Build the environment path with pathlib, so both platforms work.
        self.index_override: str | None = None  # Hold the index that this run uses when the configured one fails.

    @property
    def interpreter(self) -> Path:
        """Return the interpreter path of the environment for this platform."""
        if sys.platform == "win32":  # Windows puts the interpreter in the Scripts directory.
            return self.venv_dir / "Scripts" / "python.exe"  # Return the Windows interpreter path.
        return self.venv_dir / "bin" / "python"  # Return the Linux interpreter path.

    def create_environment(self, recreate: bool = False) -> None:
        """Create the virtual environment. If recreate is true, delete it first."""
        if recreate and self.venv_dir.exists():  # A recreate request must start from an empty directory.
            LOGGER.info("Deleting the existing environment at %s", self.venv_dir)
            shutil.rmtree(self.venv_dir)  # Remove the old environment, so the new one holds no stale package.
            LOGGER.debug("Deleted the existing environment")
        if self.interpreter.exists():  # An existing interpreter shows that the environment is ready.
            LOGGER.info("The environment exists at %s", self.venv_dir)
            return  # Keep the existing environment, because a second creation adds no value.
        LOGGER.info("Creating the virtual environment at %s", self.venv_dir)
        venv.EnvBuilder(with_pip=True, upgrade_deps=False).create(self.venv_dir)  # Build the environment with pip.
        LOGGER.debug("Created the virtual environment")

    def install_requirements(self) -> list[str]:
        """Install each requirement file that the worktree holds."""
        installed: list[str] = []  # Record each file that the script installed, so the caller can report it.
        self.index_override = PipIndexProbe(self.interpreter).fallback_index()  # Probe one time, not for each file.
        started = time.monotonic()  # Start the clock, so a slow install is visible rather than silent.
        for name in REQUIREMENT_FILES:  # Install the files in the declared order.
            path = self.root / name  # Build the file path under the worktree root.
            if not path.is_file():  # A worktree without the file needs no action.
                LOGGER.info("Skipping %s, because the worktree does not hold this file", name)
                continue  # Move to the next file in the list.
            self._install_file(path)  # Install the packages that this file declares.
            installed.append(name)  # Add the file to the report list.
        LOGGER.info("The install took %.1f seconds.", time.monotonic() - started)  # Report the total wall time.
        return installed  # Give the caller the list of the installed files.

    def _install_environment(self) -> dict[str, str]:
        """Build the environment that the pip subprocess reads."""
        environment = dict(os.environ)  # Copy the caller environment, because pip needs the rest of it.
        environment["PIP_RETRIES"] = PIP_RETRIES  # Cut the retry count, so a dead index costs seconds, not minutes.
        environment["PIP_TIMEOUT"] = PIP_TIMEOUT  # Bound the socket wait of each attempt.
        if self.index_override:  # An override applies only when the probe found the configured index unreachable.
            environment["PIP_INDEX_URL"] = self.index_override  # Point this run at the public index.
            environment.pop("PIP_EXTRA_INDEX_URL", None)  # Drop the extra index, because the override replaces it.
        LOGGER.debug("The pip subprocess uses index override %s", self.index_override or "none")
        return environment  # Give the caller the environment for the subprocess alone.

    def _install_file(self, path: Path) -> None:
        """Install one requirement file with pip."""
        command = [str(self.interpreter), "-m", "pip", "install", "-r", str(path)]  # Use the new interpreter.
        LOGGER.info("Installing the packages from %s", path.name)
        started = time.monotonic()  # Time this file, so the report names the slow one.
        result = subprocess.run(  # nosec B603 - the argument list holds no shell input.
            command, check=False, env=self._install_environment()
        )
        LOGGER.info("The install of %s took %.1f seconds.", path.name, time.monotonic() - started)
        LOGGER.debug("The install of %s returned code %d", path.name, result.returncode)
        if result.returncode != 0:  # A failed install leaves an incomplete environment.
            raise RuntimeError(f"The install of {path.name} failed with code {result.returncode}.")


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser of the script."""
    parser = argparse.ArgumentParser(description="Prepare the virtual environment of a MistHelper worktree.")
    parser.add_argument(  # Give the user one option to rebuild a damaged environment.
        "--recreate",
        action="store_true",
        help="Delete the existing .venv directory before the script creates a new one.",
    )
    return parser  # Give the caller the ready parser.


def report_result(bootstrapper: WorktreeBootstrapper, installed: list[str]) -> None:
    """Print the interpreter path and the activation command for this platform."""
    activate = ".venv\\Scripts\\Activate.ps1" if sys.platform == "win32" else "source .venv/bin/activate"
    LOGGER.info("The environment is ready.")
    LOGGER.info("Installed requirement files: %s", ", ".join(installed) or "none")
    LOGGER.info("Interpreter: %s", bootstrapper.interpreter)
    LOGGER.info("To activate the environment, run: %s", activate)
    LOGGER.info("To run the tests, run: python -m pytest -q")


def main(argv: list[str] | None = None) -> int:
    """Run the bootstrap and return the exit code of the script."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")  # Show one plain line for each step.
    args = build_parser().parse_args(argv)  # Read the command line of the caller.
    root = Path(__file__).resolve().parents[1]  # The worktree root holds the scripts directory.
    LOGGER.info("Preparing the worktree at %s", root)
    bootstrapper = WorktreeBootstrapper(root)  # Build the object that owns every step.
    try:  # Report a failed step as one clear message, because the user reads the console.
        bootstrapper.create_environment(recreate=args.recreate)  # Create the environment first.
        installed = bootstrapper.install_requirements()  # Install the declared dependencies.
    except (OSError, RuntimeError) as error:  # A file error or a failed install stops the script.
        LOGGER.error("The bootstrap failed: %s", error)
        return 1  # Report the failure to the shell.
    report_result(bootstrapper, installed)  # Tell the user which interpreter to activate.
    LOGGER.debug("The bootstrap completed for %s", root)
    return 0  # Report the success to the shell.


if __name__ == "__main__":  # Run the script only as a program, never as an import.
    sys.exit(main())  # Give the exit code of the bootstrap to the shell.
