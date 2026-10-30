"""Assert the owner-only protection of a file on POSIX and on Windows.

Why:
    POSIX stores an owner-only mode such as 0o400. NTFS stores one read-only
    attribute, and Python reports a read-only file on Windows with the mode
    0o444. A test that compares the mode with 0o400 on Windows fails for a
    reason that no script controls. This helper asserts the strongest
    protection that each platform stores.
"""

from __future__ import annotations  # Keep annotations lazy for the test runner.

import os  # The platform name chooses the assertion.
import stat  # The permission bits decode the POSIX mode.
from pathlib import Path  # The helper receives the finished file.


def assert_owner_only(path: Path) -> None:
    """Prove that the account cannot change the finished file.

    Args:
        path: The finished file that the writer created.
    """
    if os.name == "nt":  # NTFS has one read-only attribute, not owner-only permission bits.
        assert not os.access(path, os.W_OK), "The Windows file is writable."  # The read-only attribute must hold.
        return  # The POSIX mode check does not apply on Windows.
    mode = stat.S_IMODE(path.stat().st_mode)  # Read the POSIX permission bits alone.
    assert mode == 0o400, oct(mode)  # A wider mode would expose the token to other accounts.
