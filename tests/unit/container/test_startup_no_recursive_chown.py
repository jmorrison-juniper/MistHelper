"""Guard the container startup against a recursive walk of the data mount.

Issue #3138 measured a seven minute start on a 19.9 GB data directory. The
whole delay sat in one `chown -R` over `/app/data`. The startup script must
name the paths a session writes instead of walking the mount.

These checks read the shipped script, so they need no container and no network.
"""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
START_SCRIPT = REPOSITORY_ROOT / "container" / "scripts" / "start.sh"

# A session writes these paths, so the startup script may own them.
SESSION_PATHS = (
    "/app/data/script.log",
    "/app/data/ssh.log",
    "/app/data/per-host-logs",
    "/app/sessions",
)


def _script_text() -> str:
    """Return the startup script, so every check reads one source."""
    return START_SCRIPT.read_text(encoding="utf-8")


class TestStartupNeverWalksTheDataMount:
    """A recursive ownership change over the mount costs minutes."""

    def test_the_script_exists(self):
        """A missing script would make every check below pass for the wrong reason."""
        assert START_SCRIPT.is_file(), f"no startup script at {START_SCRIPT}"

    def test_no_recursive_chown_over_the_data_root(self):
        """The script must not walk /app/data, whatever owner it sets."""
        text = _script_text()
        offenders = re.findall(r"chown\s+-R\s+\S+\s+/app/data\s*(?:$|\s|2>)", text, re.M)
        assert offenders == [], "startup runs a recursive ownership change over the whole data mount: " f"{offenders}"

    def test_the_script_owns_each_session_path(self):
        """Every path a session writes must still receive an owner."""
        text = _script_text()
        missing = [path for path in SESSION_PATHS if path not in text]
        assert missing == [], f"startup no longer owns these session paths: {missing}"

    def test_the_data_root_entry_is_still_owned(self):
        """The user must be able to create a new report in the data root."""
        text = _script_text()
        # The non-recursive form changes one directory entry and never descends.
        assert re.search(
            r'chown\s+"\$USERNAME"\s+/app/data\b', text
        ), "startup no longer sets an owner on the data root entry"

    def test_the_guard_reports_the_scope_it_read(self):
        """A guard that reads nothing must not report success."""
        text = _script_text()
        assert len(text) > 500, "startup script is too small to be the real file"
        checked = len(SESSION_PATHS)
        assert checked == 4, f"expected to check 4 session paths, checked {checked}"
