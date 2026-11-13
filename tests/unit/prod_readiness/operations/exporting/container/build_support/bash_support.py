"""Find a bash that reads the paths the container script tests pass to it.

Why:
    `shutil.which("bash")` finds a bash on Windows, because the System32
    directory holds a shim for the Windows Subsystem for Linux. That shim reads
    a Linux path such as `/mnt/c/Users/...`. It refuses a Windows path such as
    `C:/Users/...`, and it answers with the status 127.

    The container tests pass a Windows path, because Python built that path.
    A guard that reads only the presence of bash therefore starts the tests on
    Windows, and every one of them fails on a path that bash cannot open. The
    repository names Windows 11 as the standard local environment, so that
    guard reports 21 faults that no engineer can act on.

    This module probes the capability instead of the presence. The probe runs
    one time for each session, because Python caches an imported module.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import os  # The probe reads the Git install folders from the environment.
import shutil  # The probe needs the path of bash.
import subprocess  # The probe runs bash one time.
import tempfile  # The probe needs a file that it owns.
from pathlib import Path  # Every path in this module is a Path.
from typing import Final  # The constants below never change after import.

PROBE_TIMEOUT_SECONDS: Final[int] = 15  # Stop a hung shim, because a hang must not hold the suite.


def windows_system_variables() -> dict[str, str]:
    """Return the Windows folder variables that a child process needs.

    Why:
        Winsock cannot load in a child whose environment lacks SYSTEMROOT, and
        the child then fails with WinError 10106. This function copies only the
        two folder names, so no token or other ambient value enters a test child.

    Returns:
        SYSTEMROOT and SYSTEMDRIVE on Windows, or an empty mapping on POSIX.
    """
    if os.name != "nt":  # POSIX children need no Windows folder variables.
        return {}  # Keep the child environment unchanged on Linux and macOS.
    names = ("SYSTEMROOT", "SYSTEMDRIVE")  # The folder names that Winsock and the loader read.
    return {name: os.environ[name] for name in names if name in os.environ}  # Copy only the names that exist.


class BashHarness:
    """Report the bash that the container script tests can use."""

    @staticmethod
    def candidates() -> tuple[str, ...]:
        """List the bash programs to probe, in the order that this machine should try them.

        Returns:
            The bash paths to probe. A listed path can be absent on this machine.
        """
        found: list[str] = []  # Keep the order, because the first capable bash wins.
        on_path = shutil.which("bash")  # The bash on PATH, which is the WSL shim on Windows.
        if on_path is not None:  # A Linux or macOS bash is normally the right answer.
            found.append(on_path)  # Try the PATH entry before the install folders.
        git = shutil.which("git")  # Git for Windows keeps its bash in a folder beside git.
        if git is not None:  # The install root of git holds bin\bash.exe.
            found.append(str(Path(git).parents[1] / "bin" / "bash.exe"))  # Move from cmd or bin to the root.
        program_files = os.environ.get("ProgramFiles")  # The default Git for Windows install root.
        if program_files:  # Only Windows defines this variable.
            found.append(str(Path(program_files) / "Git" / "bin" / "bash.exe"))  # The standard install path.
        return tuple(dict.fromkeys(found))  # Drop duplicates and keep the first occurrence of each path.

    @staticmethod
    def reads_windows_paths(bash: str) -> bool:
        """Answer whether this bash opens a file through a Windows path.

        Args:
            bash: The path of the bash program to probe.

        Returns:
            True when bash opens the probe file, and False in every other case.
        """
        with tempfile.TemporaryDirectory() as folder:  # Own the directory, so no test file leaks.
            probe = Path(folder) / "probe.sh"  # Name the file that bash must open.
            probe.write_text("exit 0\n", encoding="utf-8")  # Write a script that always passes.
            try:
                # `bash -n` parses the file and runs no command in it. A shim that
                # cannot open the path answers 127 and never reaches the parse.
                result = subprocess.run(
                    [bash, "-n", probe.as_posix()],
                    capture_output=True,
                    text=True,
                    timeout=PROBE_TIMEOUT_SECONDS,
                    check=False,  # Keep the status, because the status is the answer.
                )
            except (OSError, subprocess.SubprocessError):
                return False  # A bash that cannot start cannot run the tests.
            return result.returncode == 0  # A zero status proves that bash opened the file.

    @classmethod
    def select(cls) -> str | None:
        """Return the first candidate that opens a Windows path, or None when none does.

        Returns:
            The path of the bash that runs the tests, or None when no candidate can.
        """
        for candidate in cls.candidates():  # Probe in order, so the PATH entry is tried first.
            if not Path(candidate).is_file():  # A missing program cannot run, so skip it.
                continue  # Move to the next candidate.
            if cls.reads_windows_paths(candidate):  # The probe proves the capability, not the presence.
                return candidate  # This bash opens the paths that Python builds.
        return None  # No candidate can run the container script tests.

    @classmethod
    def skip_reason(cls, selected: str | None) -> str | None:
        """State why the container script tests cannot run, or None when they can.

        Args:
            selected: The bash that `select` returned, or None when no candidate can open a Windows path.

        Returns:
            The reason for the skip, or None when this machine can run the tests.
        """
        if selected is not None:  # A probed bash runs the tests.
            return None  # The tests can run on this machine.
        if not any(Path(candidate).is_file() for candidate in cls.candidates()):  # Any bash program at all?
            return "bash is required to run the container scripts"  # Name the missing program.
        return (  # A bash exists, but none of them reads the Windows paths.
            "no bash on this machine can open a file through a Windows path; "
            "install Git for Windows or run the tests on Linux"  # Name the fix for the operator.
        )


SELECTED_BASH: Final[str | None] = BashHarness.select()  # Probe once for each session.
BASH_PATH: Final[str | None] = SELECTED_BASH  # The bash that each test module runs.
BASH_SKIP_REASON: Final[str | None] = BashHarness.skip_reason(SELECTED_BASH)  # None when the tests can run.
