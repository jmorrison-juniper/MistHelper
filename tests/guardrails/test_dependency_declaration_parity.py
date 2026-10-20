"""Prove that pyproject.toml declares every package of the requirements files (issue #3400).

``pyproject.toml`` is the canonical dependency declaration. Before the lock file
exists, each package in ``requirements.txt`` and ``requirements-dev.txt`` must
appear in the ``dependencies`` list or in the ``dev`` extra, with a floor that is
not lower and with an upper bound that is not looser. The guard prints the count
of packages that it examined and fails when an input is unreadable or empty.
"""

import logging
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import Specifier
from packaging.utils import canonicalize_name
from packaging.version import Version

logger = logging.getLogger(__name__)  # WHY: keep the guard records on the module logger.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve paths from the test, not the working directory.
REQUIREMENT_FILES = ("requirements.txt", "requirements-dev.txt")  # The two files that the later slices will generate.


class DeclarationParity:
    """Compare the requirement files with the pyproject declaration."""

    @staticmethod
    def read_requirements(path: Path) -> list[Requirement]:
        """Parse one requirements file, and fail when it is absent or empty."""
        lines = [line.split(" #")[0].strip() for line in path.read_text(encoding="utf-8").splitlines()]  # Drop comments
        found = [Requirement(line) for line in lines if line and not line.startswith("#")]  # Keep requirements
        if not found:  # An empty parse means the guard read nothing.
            raise AssertionError(f"No requirement found in {path}")
        return found

    @staticmethod
    def read_declared(pyproject: Path) -> dict[str, list[Requirement]]:
        """Return the declared requirements for each canonical package name."""
        project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]  # A missing table raises KeyError.
        texts = list(project["dependencies"]) + list(project["optional-dependencies"]["dev"])  # Runtime and dev.
        declared: dict[str, list[Requirement]] = {}
        for text in texts:  # Group by canonical name so extras and case do not hide a match.
            requirement = Requirement(text)
            declared.setdefault(canonicalize_name(requirement.name), []).append(requirement)
        return declared

    @staticmethod
    def floor(requirement: Requirement) -> Version | None:
        """Return the lowest version that the requirement allows, or None."""
        for clause in requirement.specifier:  # An exact pin and a lower bound both set the floor.
            if clause.operator in (">=", "=="):
                return Version(clause.version)
        return None

    @staticmethod
    def ceiling(requirement: Requirement) -> Specifier | None:
        """Return the upper bound clause of the requirement, or None."""
        for clause in requirement.specifier:  # Only a strict upper bound or an exact pin limits the top.
            if clause.operator in ("<", "=="):
                return clause
        return None

    @classmethod
    def defect(cls, wanted: Requirement, declared: list[Requirement]) -> str | None:
        """Return the reason that no declaration covers the wanted requirement."""
        if wanted.url is not None:  # A direct reference must match exactly.
            same = [item for item in declared if item.url == wanted.url]
            return None if same else f"{wanted.name}: no declaration with url {wanted.url}"
        if not declared:  # No declaration at all is the most common drift.
            return f"{wanted.name}: not declared in pyproject.toml"
        reasons = [cls.compare(wanted, item) for item in declared]  # One covering declaration is enough.
        return None if None in reasons else f"{wanted.name}: {'; '.join(r for r in reasons if r)}"

    @classmethod
    def compare(cls, wanted: Requirement, item: Requirement) -> str | None:
        """Return why one declaration is looser than the wanted requirement, or None."""
        wanted_floor, item_floor = cls.floor(wanted), cls.floor(item)
        if wanted_floor and (item_floor is None or item_floor < wanted_floor):  # The floor must not drop.
            return f"floor {item_floor} is below {wanted_floor}"
        wanted_ceiling, item_ceiling = cls.ceiling(wanted), cls.ceiling(item)
        if wanted_ceiling and (item_ceiling is None or Version(item_ceiling.version) > Version(wanted_ceiling.version)):
            return f"upper bound {item_ceiling} is looser than {wanted_ceiling}"  # The top must not rise.
        if str(wanted.marker or "") != str(item.marker or ""):  # The platform marker must survive.
            return f"marker {item.marker} differs from {wanted.marker}"
        return None

    @classmethod
    def audit(cls, root: Path) -> tuple[int, list[str]]:
        """Return the count of examined requirements and each defect."""
        declared = cls.read_declared(root / "pyproject.toml")
        examined, defects = 0, []
        for name in REQUIREMENT_FILES:  # Check each file against the one declaration.
            for wanted in cls.read_requirements(root / name):
                examined += 1
                reason = cls.defect(wanted, declared.get(canonicalize_name(wanted.name), []))
                if reason:
                    defects.append(f"{name}: {reason}")
        return examined, defects


def test_pyproject_declares_each_requirement() -> None:
    """Fail when a requirement has no declaration, or only a looser one."""
    examined, defects = DeclarationParity.audit(REPOSITORY_ROOT)
    logger.info("Dependency parity examined %d requirements with %d defects", examined, len(defects))
    print(f"dependency parity: examined {examined} requirements, {len(defects)} defects")
    assert examined >= 50, f"Examined only {examined} requirements"
    assert defects == [], "\n".join(defects)


@pytest.mark.parametrize(
    ("wanted", "declared", "expected"),
    [
        ("requests>=2.34.2,<3", ["requests>=2.28.0,<3"], "floor 2.28.0 is below 2.34.2"),
        ("requests>=2.34.2,<3", ["requests>=2.34.2,<4"], "looser"),
        ("requests>=2.34.2,<3", [], "not declared"),
        ("waitress>=3.0.2 ; sys_platform == 'win32'", ["waitress>=3.0.2"], "marker"),
        ("black==26.10.1", ["black==26.10.1"], None),
        ("black==26.10.1", ["black==26.10.0"], "floor 26.10.0 is below 26.10.1"),
        ("pdfplumber>=0.11.10", ["pdfplumber>=0.11.10,<1"], None),
    ],
)
def test_comparison_detects_a_looser_declaration(wanted: str, declared: list[str], expected: str | None) -> None:
    """Prove that the comparison can fail for each kind of drift."""
    reason = DeclarationParity.defect(Requirement(wanted), [Requirement(item) for item in declared])
    if expected is None:
        assert reason is None
    else:
        assert reason is not None and expected in reason


def test_audit_fails_on_an_empty_requirements_file(tmp_path: Path) -> None:
    """Fail closed when a requirements file holds no requirement."""
    (tmp_path / "requirements.txt").write_text("# only a comment\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="No requirement found"):
        DeclarationParity.read_requirements(tmp_path / "requirements.txt")


def test_audit_reports_a_missing_package(tmp_path: Path) -> None:
    """Prove that a package with no declaration is a defect."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["requests>=2"]\n[project.optional-dependencies]\ndev = []\n',
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("requests>=2\nflask>=3\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("black==1.0\n", encoding="utf-8")
    examined, defects = DeclarationParity.audit(tmp_path)
    assert examined == 3
    assert len(defects) == 2
