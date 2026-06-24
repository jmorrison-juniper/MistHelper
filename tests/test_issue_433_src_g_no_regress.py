"""Regression test for issue #433 Phase A: prevent G-rule reintroduction in src/.

After issue #429 cleaned MistHelper.py and #433 Phase A cleaned src/, tools/,
web_portal/, starlink_dashboard.py, and wsgi.py, the project's pyproject.toml
``[tool.ruff.lint] select`` enforces the ``G`` rule family with no per-file
ignores apart from the codemod synthetic-input fixture.

This test pins that contract: ``ruff check --select G003,G004,G201 .``
MUST exit 0 (when scoped to non-fixture paths). Any new PR that reintroduces
an eager-formatted logging call anywhere in src/, tools/, web_portal/, or
the top-level scripts will fail this test and the CI ruff gate.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/433
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

import subprocess  # Drives ruff via its CLI so we exercise the documented public interface.
import sys  # Provides the active Python interpreter path for the subprocess call.
from pathlib import Path  # Portable filesystem handling for the repo-root anchor.

REPO_ROOT = Path(__file__).resolve().parent.parent  # tests/ -> repo root anchor.
TARGET_PATHS = (  # Paths whose G-rule cleanup is locked in by issue #433 Phase A.
    "src",  # The main src/ tree (789 sites converted).
    "tools",  # Already clean before issue #433; verified by Phase A pre-sweep.
    "web_portal",  # 3 sites converted during Phase A.
    "starlink_dashboard.py",  # 12 sites converted during Phase A.
    "wsgi.py",  # Already clean before issue #433; verified by Phase A pre-sweep.
)


def test_g_rules_stay_clean_in_all_swept_paths() -> None:
    """Every path swept by issue #433 Phase A must report 0 G-rule violations."""
    cmd = [  # Construct the ruff CLI invocation with --isolated so per-file-ignores cannot mask a regression.
        sys.executable,  # Use the active interpreter to match the project's pinned Python.
        "-m",
        "ruff",
        "check",
        "--isolated",  # Ignore pyproject config; the test pins the raw rule outcome.
        "--select",
        "G003,G004,G201",  # The three G-rules issue #433 Phase A drove to zero.
        *TARGET_PATHS,  # Restrict the scan to the paths Phase A actually swept.
    ]
    result = subprocess.run(  # nosec B603 -- trusted args from this test module only.
        cmd,
        cwd=REPO_ROOT,  # Anchor the cwd so relative TARGET_PATHS resolve correctly.
        capture_output=True,  # Capture stderr/stdout so failure messages are visible.
        text=True,  # Decode bytes -> str for assertion-message readability.
        check=False,  # We assert below so failure context is included in the message.
    )
    assert result.returncode == 0, (  # exit 0 == no violations; non-zero means regression.
        f"ruff found G-rule violations after issue #433 Phase A locked them out.\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
