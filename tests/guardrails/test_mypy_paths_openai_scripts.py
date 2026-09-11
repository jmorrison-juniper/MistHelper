"""Guardrail for the two openai-importing script packages in the mypy gate.

Issue #1948 recorded that a major dependency bump could merge with no gate
above the code it changes. The two packages that import the openai SDK are
``mist_ideas_analyzer_pkg`` and ``mist_ideas_distiller_v2_pkg``. They sit in
``scripts/``, which the mypy config excludes, so the CI gate must name their
``__init__.py`` files explicitly in ``MYPY_PATHS``.

These tests hold that requirement in place. A change that drops either path
from ``MYPY_PATHS`` fails a test, and the packages then return to ungated
status.
"""

from pathlib import Path

import yaml

# The workflow sits three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Name the workflow once, because both tests below read the same file.
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Name the two packages once, because both tests below inspect the same pair.
OPENAI_SCRIPT_PACKAGES = [
    "scripts/mist_ideas_analyzer_pkg/__init__.py",
    "scripts/mist_ideas_distiller_v2_pkg/__init__.py",
]


def _mypy_paths() -> str:
    """Read the MYPY_PATHS value from the quality gate workflow."""
    # Read with an explicit encoding, because the Windows default differs.
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    # Parse with the safe loader, because the file is untrusted configuration.
    parsed = yaml.safe_load(text)

    # The env block must exist, because the mypy job reads MYPY_PATHS from it.
    assert isinstance(parsed, dict), f"The workflow must be a mapping: {CI_WORKFLOW}"

    # Return the value as a string, because the tests below inspect its parts.
    return str(parsed["env"]["MYPY_PATHS"])


def test_mypy_paths_include_both_openai_script_packages() -> None:
    """The gate must name both script packages, so a bump cannot merge ungated."""
    # Read the gate scope, because the checks below inspect each required path.
    mypy_paths = _mypy_paths()

    # A missing path returns the package to ungated status, so reject that case.
    for package_path in OPENAI_SCRIPT_PACKAGES:
        assert package_path in mypy_paths, (
            f"MYPY_PATHS must include {package_path}. "
            "Without it, a dependency bump merges with no gate above the code."
        )


def test_mypy_paths_keep_the_original_scope() -> None:
    """The original scope must stay, so the new paths do not replace it."""
    # Read the gate scope, because the checks below inspect the original parts.
    mypy_paths = _mypy_paths()

    # A dropped original path loses existing coverage, so reject that case.
    for original_path in ["src/", "MistHelper.py", "wsgi.py"]:
        assert original_path in mypy_paths, (
            f"MYPY_PATHS must keep {original_path}. " "Dropping it loses the coverage that #888 added."
        )
