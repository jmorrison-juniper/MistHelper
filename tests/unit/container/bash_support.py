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

import shutil  # The probe needs the path of bash.
import subprocess  # The probe runs bash one time.
import tempfile  # The probe needs a file that it owns.
from pathlib import Path  # Every path in this module is a Path.
from typing import Final  # The constants below never change after import.

PROBE_TIMEOUT_SECONDS: Final[int] = 15  # Stop a hung shim, because a hang must not hold the suite.


class BashHarness:
    """Report the bash that the container script tests can use."""

    PATH: Final[str | None] = shutil.which("bash")  # The bash on the path, or None.

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
    def skip_reason(cls) -> str | None:
        """State why the container script tests cannot run, or None when they can.

        Returns:
            The reason for the skip, or None when this machine can run the tests.
        """
        if cls.PATH is None:
            return "bash is required to run the container scripts"  # No bash at all.
        if not cls.reads_windows_paths(cls.PATH):
            # The Windows Subsystem for Linux shim reaches this branch. It reads
            # `/mnt/c/...` and refuses `C:/...`, so it cannot open the script.
            return f"the bash at {cls.PATH} cannot open a file through a Windows path"
        return None  # This bash runs the tests.


BASH_PATH: Final[str | None] = BashHarness.PATH  # The bash that each test module runs.
BASH_SKIP_REASON: Final[str | None] = BashHarness.skip_reason()  # None when the tests can run.
