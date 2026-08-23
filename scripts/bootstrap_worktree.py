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
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess  # nosec B404 - the script starts pip with a fixed argument list.
import sys
import venv
from pathlib import Path

LOGGER = logging.getLogger("bootstrap_worktree")

# The requirement files that the script installs, in this order. The script
# skips a file that the worktree does not hold.
REQUIREMENT_FILES: tuple[str, ...] = ("requirements.txt", "requirements-dev.txt")


class WorktreeBootstrapper:
    """Create one virtual environment and install the project dependencies."""

    def __init__(self, root: Path, venv_name: str = ".venv") -> None:
        """Store the worktree root and the name of the environment directory."""
        self.root = root  # Keep the worktree root, because every path starts here.
        self.venv_dir = root / venv_name  # Build the environment path with pathlib, so both platforms work.

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
        for name in REQUIREMENT_FILES:  # Install the files in the declared order.
            path = self.root / name  # Build the file path under the worktree root.
            if not path.is_file():  # A worktree without the file needs no action.
                LOGGER.info("Skipping %s, because the worktree does not hold this file", name)
                continue  # Move to the next file in the list.
            self._install_file(path)  # Install the packages that this file declares.
            installed.append(name)  # Add the file to the report list.
        return installed  # Give the caller the list of the installed files.

    def _install_file(self, path: Path) -> None:
        """Install one requirement file with pip."""
        command = [str(self.interpreter), "-m", "pip", "install", "-r", str(path)]  # Use the new interpreter.
        LOGGER.info("Installing the packages from %s", path.name)
        result = subprocess.run(command, check=False)  # nosec B603 - the argument list holds no shell input.
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
