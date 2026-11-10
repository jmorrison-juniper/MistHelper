"""Prove that the locked exports match direct declarations in pyproject.toml (issue #3400).

The export files include transitive packages. Their ``via misthelper`` comments
identify direct project packages. The guard checks those pins against the
canonical declarations and fails when an input is unreadable or empty.
"""

import logging
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet  # WHY: validate package bounds and Python support ranges.
from packaging.utils import canonicalize_name
from packaging.version import Version

logger = logging.getLogger(__name__)  # WHY: keep the guard records on the module logger.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve paths from the test, not the working directory.
REQUIREMENT_FILES = ("requirements.txt", "requirements-dev.txt")  # The two files that the later slices will generate.


class DeclarationParity:
    """Compare direct locked exports with the pyproject declaration."""

    @classmethod
    def read_requirements(cls, path: Path) -> list[Requirement]:
        """Parse direct project requirements from one generated export."""
        logger.info("Reading generated dependency export %s", path.name)  # Trace the file before reading.
        try:
            lines = path.read_text(encoding="utf-8").splitlines()  # Read the export and split its package blocks.
        except (OSError, UnicodeError) as error:
            logger.error("Could not read dependency export %s: %s", path.name, error)  # Preserve the read failure.
            raise
        found: list[Requirement] = []  # Keep only packages that the project declares directly.
        current: str | None = None  # Track the package line for its following UV annotations.
        annotations: list[str] = []  # Store comments that identify the source of the current package.
        for line in lines:
            if line and not line[0].isspace() and not line.startswith("#"):
                if current is not None and cls.is_direct(annotations):
                    found.append(Requirement(current))  # Keep a direct project requirement.
                current = line.split(" #")[0].strip()  # Remove any inline annotation from the requirement.
                annotations = []  # Start a new annotation block for the next package.
            elif current is not None:
                annotations.append(line)  # Keep the source comments for the current package.
        if current is not None and cls.is_direct(annotations):
            found.append(Requirement(current))  # Keep the final direct package in the file.
        logger.debug("Read %s direct requirements from %s", len(found), path.name)  # Report the measured count.
        if not found:  # An empty parse means the guard read nothing.
            raise AssertionError(f"No direct requirement found in {path}")
        return found

    @staticmethod
    def is_direct(annotations: list[str]) -> bool:
        """Return whether UV identifies the root project as a package source."""
        sources = {annotation.replace("#", "").strip() for annotation in annotations}  # Normalize UV comment text.
        return "misthelper" in sources or "via misthelper" in sources  # Match direct package annotations.

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
        exact_pins = [clause for clause in wanted.specifier if clause.operator == "=="]  # Find exact locked pins.
        if len(exact_pins) == 1 and "*" not in exact_pins[0].version:
            pinned_version = Version(exact_pins[0].version)  # Check the locked version against the declaration.
            if not item.specifier.contains(pinned_version, prereleases=True):
                return f"version {pinned_version} is outside {item.specifier}"
            if str(wanted.marker or "") != str(item.marker or ""):
                return f"marker {item.marker} differs from {wanted.marker}"
            return None
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
    "project_file",  # WHY: select each project metadata file for the same floor check.
    [
        REPOSITORY_ROOT / "pyproject.toml",  # WHY: validate the root project minimum.
        REPOSITORY_ROOT / "mist-ops-platform" / "pyproject.toml",  # WHY: validate the platform project minimum.
    ],
    ids=("misthelper", "mist-ops-platform"),  # WHY: identify the project in test output.
)
def test_projects_reject_python_314_and_accept_python_315(project_file: Path) -> None:
    """Fail when either project accepts Python 3.14 or rejects Python 3.15."""
    logger.info("Reading Python support from %s", project_file.relative_to(REPOSITORY_ROOT))  # Identify the metadata.
    metadata = tomllib.loads(project_file.read_text(encoding="utf-8"))  # Parse the declared project metadata.
    supported = SpecifierSet(metadata["project"]["requires-python"])  # Evaluate the supported runtime range.
    logger.debug("Project %s supports Python %s", project_file.name, supported)  # Report the tested support range.
    assert (  # WHY: enforce the new minimum and target runtime.
        Version("3.14") not in supported  # WHY: reject the previous minimum.
        and Version("3.15") in supported  # WHY: accept the requested minimum.
    )


@pytest.mark.parametrize(
    ("wanted", "declared", "expected"),
    [
        ("requests>=2.34.2,<3", ["requests>=2.28.0,<3"], "floor 2.28.0 is below 2.34.2"),
        ("requests>=2.34.2,<3", ["requests>=2.34.2,<4"], "looser"),
        ("requests>=2.34.2,<3", [], "not declared"),
        ("waitress>=3.0.2 ; sys_platform == 'win32'", ["waitress>=3.0.2"], "marker"),
        ("black==26.10.1", ["black==26.10.1"], None),
        ("black==26.10.1", ["black==26.10.0"], "version 26.10.1 is outside ==26.10.0"),
        ("requests==2.34.2", ["requests>=2.34.2,<3"], None),
        ("requests==3.0.0", ["requests>=2.34.2,<3"], "version 3.0.0 is outside <3,>=2.34.2"),
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
    with pytest.raises(AssertionError, match="No direct requirement found"):
        DeclarationParity.read_requirements(tmp_path / "requirements.txt")


def test_audit_reports_a_missing_package(tmp_path: Path) -> None:
    """Prove that a package with no declaration is a defect."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["requests>=2"]\n[project.optional-dependencies]\ndev = []\n',
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text(
        "requests==2.0\n    # via misthelper\nurllib3==2.8\n    # via requests\nflask==3.0\n    # via misthelper\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements-dev.txt").write_text("black==1.0\n    # via misthelper\n", encoding="utf-8")
    examined, defects = DeclarationParity.audit(tmp_path)
    assert examined == 3
    assert len(defects) == 2
