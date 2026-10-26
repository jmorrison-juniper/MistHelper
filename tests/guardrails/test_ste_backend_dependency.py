"""Prove that the STE linter extra refuses the broken preshed release (issue #4468).

preshed 3.0.14 rejects hash keys at or above 2**63. spaCy then fails to load the
en_core_web_sm tokenizer with ``OverflowError``, and the STE gate stops before it
grades a file. The guard reads the ``ste-linter`` extra in ``pyproject.toml`` and
fails when the extra accepts preshed 3.0.14 or refuses the repaired 3.0.15.
"""

import logging
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

logger = logging.getLogger(__name__)  # WHY: keep the guard records on the module logger.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve paths from the test, not the working directory.
BROKEN_RELEASE = "3.0.14"  # The release that issue #4468 traced to the tokenizer overflow.
REPAIRED_RELEASE = "3.0.15"  # The upstream release that repairs keys at or above 2**63.


class SteBackendExtra:
    """Read the ste-linter extra and find the preshed requirement in it."""

    @staticmethod
    def read_requirements(path: Path) -> list[Requirement]:
        """Return the requirements of the ste-linter extra, and fail when the extra is absent."""
        logger.info("Reading the ste-linter extra from %s", path)  # Record the input before the read.
        project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})  # Raises when absent.
        entries = project.get("optional-dependencies", {}).get("ste-linter")  # The extra that installs spaCy.
        assert entries, f"{path} declares no ste-linter extra"  # An empty input must not pass.
        requirements = [Requirement(entry) for entry in entries]  # Parse each entry as PEP 508.
        logger.debug("The ste-linter extra holds %d requirements", len(requirements))  # Count the examined input.
        return requirements

    @staticmethod
    def find_preshed(requirements: list[Requirement]) -> Requirement:
        """Return the preshed requirement, and fail when the extra does not name preshed."""
        matches = [item for item in requirements if canonicalize_name(item.name) == "preshed"]  # Normalize names.
        assert matches, "The ste-linter extra does not exclude the broken preshed release"  # Fail on absence.
        return matches[0]


def test_extra_refuses_broken_preshed_release() -> None:
    """The extra refuses preshed 3.0.14 and accepts the repaired 3.0.15."""
    requirements = SteBackendExtra.read_requirements(REPOSITORY_ROOT / "pyproject.toml")  # Read the live file.
    preshed = SteBackendExtra.find_preshed(requirements)  # Locate the exclusion.
    print(f"Examined {len(requirements)} ste-linter requirements")  # Show the count that the guard checked.
    assert not preshed.specifier.contains(BROKEN_RELEASE)  # The broken release must not install.
    assert preshed.specifier.contains(REPAIRED_RELEASE)  # The repaired release must stay allowed.


def test_missing_exclusion_fails() -> None:
    """Prove the guard fails when the extra does not name preshed."""
    with pytest.raises(AssertionError, match="does not exclude"):
        SteBackendExtra.find_preshed([Requirement("spacy>=3.7.0,<4.0.0")])


def test_missing_extra_fails(tmp_path: Path) -> None:
    """Prove the guard fails when the project declares no ste-linter extra."""
    project_file = tmp_path / "pyproject.toml"  # A project file with no extras.
    project_file.write_text('[project]\nname = "sample"\n', encoding="utf-8")  # Minimal valid TOML.
    with pytest.raises(AssertionError, match="no ste-linter extra"):
        SteBackendExtra.read_requirements(project_file)
