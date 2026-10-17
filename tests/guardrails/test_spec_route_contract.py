"""Guard the fixed-width base-5 route used by the Spec Kit generator."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROUTE_SCRIPT = REPOSITORY_ROOT / ".specify/scripts/powershell/spec-route.ps1"
GENERATOR_SCRIPT = REPOSITORY_ROOT / ".specify/scripts/powershell/create-new-feature.ps1"


def snapshot_tree(root: Path) -> dict[str, bytes | str | None]:
    """Capture paths and contents so failure tests can prove preservation."""
    snapshot: dict[str, bytes | str | None] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = os.readlink(path)
        elif path.is_file():
            snapshot[relative] = path.read_bytes()
        else:
            snapshot[relative] = None
    return snapshot


def python_route(number: int, width: int = 8) -> str:
    """Return the fixed-width base-5 route for a feature number."""
    digits = ["0"] * width
    remaining = number
    for index in range(width - 1, -1, -1):
        digits[index] = str(remaining % 5)
        remaining //= 5
    if remaining:
        raise ValueError(f"Feature number {number} exceeds route width {width}.")
    return "/".join(digits)


def test_radix_route_is_stable() -> None:
    """Pin the route for the first migration and the current maximum."""
    expected = {
        800: "0/0/0/1/1/2/0/0",
        801: "0/0/0/1/1/2/0/1",
        3750: "0/0/1/1/0/0/0/0",
        3923: "0/0/1/1/1/1/4/3",
    }
    assert {number: python_route(number) for number in expected} == expected


def test_generator_calls_route_helper() -> None:
    """Require the generator to use the route helper for every new feature."""
    source = GENERATOR_SCRIPT.read_text(encoding="utf-8")
    assert "spec-route.ps1" in source
    assert "Resolve-SpecFeaturePath" in source
    assert "$featureDir = Join-Path $specsDir $branchName" not in source


def test_powershell_route_reports_environment() -> None:
    """Run PowerShell when available or report its absence explicitly."""
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.fail("Install pwsh to verify executable routing.")
    command = f". '{ROUTE_SCRIPT}'; " "$route = Get-SpecRadixSegments -Number 800; " "Write-Output ($route -join '/')"
    result = subprocess.run(
        [pwsh, "-NoProfile", "-Command", command],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "0/0/0/1/1/2/0/0"


@pytest.mark.parametrize(
    ("name", "route"),
    [
        ("19700101-000000-first", "0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0"),
        ("20261013-182828-labels", "0/0/0/1/2/1/3/2/2/1/2/3/0/3/4/1/3"),
        ("99991231-235959-last", "1/3/1/2/2/4/3/1/4/4/2/1/1/1/1/4/4"),
    ],
)
def test_timestamp_routes_use_bounded_groups(name: str, route: str, tmp_path: Path) -> None:
    """Pin independent timestamp vectors through the real PowerShell helper."""
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.fail("Install pwsh to verify timestamp routing.")
    environment = dict(os.environ, ROUTE_ROOT=str(tmp_path), RECORD_NAME=name)
    command = (
        f". '{ROUTE_SCRIPT}'; "
        "Resolve-SpecFeaturePath -SpecsDir $env:ROUTE_ROOT -BranchName $env:RECORD_NAME -Timestamp"
    )
    result = subprocess.run([pwsh, "-NoProfile", "-Command", command], env=environment, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    resolved = Path(result.stdout.strip())
    assert resolved == tmp_path / "live" / route / name
    segments = resolved.relative_to(tmp_path / "live").parts
    assert len(segments) == 18
    assert len(segments[0:17]) == 17
    assert all(segment in "01234" for segment in segments[0:17])


def test_duplicate_timestamp_names_resolve_to_the_same_record(tmp_path: Path) -> None:
    """Keep repeated timestamp identities deterministic."""
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.fail("Install pwsh to verify duplicate timestamp names.")
    environment = dict(os.environ, ROUTE_ROOT=str(tmp_path), RECORD_NAME="20261013-182828-record")
    command = (
        f". '{ROUTE_SCRIPT}'; "
        "Resolve-SpecFeaturePath -SpecsDir $env:ROUTE_ROOT -BranchName $env:RECORD_NAME -Timestamp"
    )
    resolved_paths: list[Path] = []
    for _ in range(2):
        result = subprocess.run(
            [pwsh, "-NoProfile", "-Command", command], env=environment, text=True, capture_output=True
        )
        assert result.returncode == 0, result.stderr
        resolved_paths.append(Path(result.stdout.strip()))
    assert resolved_paths[0] == resolved_paths[1]


@pytest.mark.parametrize(
    "name",
    [
        "19691231-235959-old",
        "20260230-000000-bad",
        "20261301-000000-bad",
        "20261013-240000-bad",
        "20261013-182860-bad",
        "../unsafe",
        "20261013-182828-",
    ],
)
def test_timestamp_route_rejects_invalid_names(name: str, tmp_path: Path) -> None:
    """Reject invalid labels before a destination can be created."""
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.fail("Install pwsh to verify timestamp failures.")
    environment = dict(os.environ, ROUTE_ROOT=str(tmp_path), RECORD_NAME=name)
    command = (
        f". '{ROUTE_SCRIPT}'; Resolve-SpecFeaturePath -SpecsDir $env:ROUTE_ROOT -BranchName $env:RECORD_NAME -Timestamp"
    )
    result = subprocess.run([pwsh, "-NoProfile", "-Command", command], env=environment, text=True, capture_output=True)
    assert result.returncode != 0
    assert list(tmp_path.iterdir()) == []


class SpecCommandFixture:
    """Run process commands inside an isolated repository-shaped directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.scripts = root / ".specify" / "scripts" / "powershell"
        shutil.copytree(ROUTE_SCRIPT.parent, self.scripts)
        shutil.copytree(REPOSITORY_ROOT / ".specify" / "templates", root / ".specify" / "templates")
        self.pointer = root / ".specify" / "feature.json"
        self.pointer.write_text('{"feature_directory":"specs/unchanged-owner"}\n')

    def run(self, script: str, feature: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        """Keep explicit feature selection in this child command only."""
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            pytest.fail("Install pwsh to verify feature commands.")
        environment = dict(os.environ, SPECIFY_INIT_DIR=str(self.root), SPECIFY_FEATURE_DIRECTORY=str(feature))
        return subprocess.run(
            [pwsh, "-NoProfile", "-File", str(self.scripts / script), *arguments],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
        )

    def feature(self, relative: str) -> Path:
        """Create a selected record with bounded supporting artifacts."""
        feature = self.root / relative
        (feature / "design" / "contracts").mkdir(parents=True)
        for name in ("spec.md", "plan.md", "tasks.md"):
            (feature / name).write_text("# Isolated feature\n")
        for name in ("research.md", "data-model.md", "quickstart.md"):
            (feature / "design" / name).write_text("# Isolated design\n")
        (feature / "design" / "contracts" / "paths.md").write_text("# Contract\n")
        return feature


@pytest.mark.parametrize(
    "relative",
    [
        "specs/numbered/0/0/1/1/4/0/2/3/4263-first",
        "specs/live/20261013-182828-direct",
        "specs/live/0/0/0/1/2/1/3/2/2/1/2/3/0/3/4/1/3/20261013-182828-grouped",
    ],
)
def test_selected_feature_commands_preserve_pointer(tmp_path: Path, relative: str) -> None:
    """Select actual inputs and design paths without overwriting another owner."""
    fixture = SpecCommandFixture(tmp_path)
    feature = fixture.feature(relative)
    original = fixture.pointer.read_bytes()
    for script, arguments in (
        ("check-prerequisites.ps1", ("-Json", "-RequireSpec", "-RequireTasks", "-IncludeTasks")),
        ("setup-tasks.ps1", ("-Json",)),
        ("setup-plan.ps1", ("-Json",)),
    ):
        result = fixture.run(script, feature, *arguments)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert Path(payload["FEATURE_DIR"]) == feature
        if "AVAILABLE_DOCS" in payload:
            assert Path("design/research.md") in [Path(value) for value in payload["AVAILABLE_DOCS"]]
            assert Path("design/contracts") in [Path(value) for value in payload["AVAILABLE_DOCS"]]
        assert fixture.pointer.read_bytes() == original


def test_conflicting_design_layout_fails(tmp_path: Path) -> None:
    """Reject a duplicate artifact role rather than select an arbitrary copy."""
    fixture = SpecCommandFixture(tmp_path)
    feature = fixture.feature("specs/live/20261013-182828-direct")
    (feature / "research.md").write_text("# Conflicting research\n")
    result = fixture.run("check-prerequisites.ps1", feature, "-Json", "-RequireSpec")
    assert result.returncode != 0
    assert "Ambiguous feature artifact" in result.stderr


def test_missing_selected_feature_fails(tmp_path: Path) -> None:
    """Report an absent selected record instead of selecting the saved owner."""
    fixture = SpecCommandFixture(tmp_path)
    result = fixture.run("check-prerequisites.ps1", tmp_path / "specs" / "missing", "-Json", "-RequireSpec")
    assert result.returncode != 0
    assert "Feature directory not found" in result.stderr


@pytest.mark.parametrize("case", ["outside", "nested", "symlink"])
def test_unsafe_feature_selection_fails(tmp_path: Path, case: str) -> None:
    """Reject escaping and nested selections before command execution."""
    fixture = SpecCommandFixture(tmp_path)
    parent = fixture.feature("specs/live/20261013-182828-parent")
    selected = tmp_path / "outside"
    if case == "nested":
        selected = fixture.feature(str(parent.relative_to(tmp_path) / "design" / "child"))
    if case == "symlink":
        selected = tmp_path / "specs" / "linked"
        selected.symlink_to(parent, target_is_directory=True)
    before = snapshot_tree(tmp_path)
    result = fixture.run("check-prerequisites.ps1", selected, "-Json", "-RequireSpec")
    assert result.returncode != 0
    assert "Examined" in result.stderr
    assert snapshot_tree(tmp_path) == before


def test_explicit_selection_disambiguates_duplicate_feature_names(tmp_path: Path) -> None:
    """Select the requested route when separate records share a basename."""
    fixture = SpecCommandFixture(tmp_path)
    identity = "20261013-182828-shared"
    fixture.feature(f"specs/live/{identity}")
    selected = fixture.feature(f"specs/live/{'/'.join(['0'] * 17)}/{identity}")
    original = fixture.pointer.read_bytes()

    result = fixture.run("check-prerequisites.ps1", selected, "-Json", "-RequireSpec")

    assert result.returncode == 0, result.stderr
    assert Path(json.loads(result.stdout)["FEATURE_DIR"]) == selected
    assert fixture.pointer.read_bytes() == original


def test_full_managed_root_rejects_allocation_without_writes(tmp_path: Path) -> None:
    """Check the live root before creating any timestamp route segment."""
    fixture = SpecCommandFixture(tmp_path)
    live = tmp_path / "specs" / "live"
    for number in range(5):
        fixture.feature(f"specs/live/20261013-18282{number}-owner")
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    result = fixture.run(
        "create-new-feature.ps1",
        live,
        "-Json",
        "-Timestamp",
        "-ShortName",
        "new-record",
        "Test bounded allocation",
    )
    assert result.returncode != 0
    assert "five children" in result.stderr
    assert sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*")) == before


def test_full_numeric_group_rejects_allocation_without_partial_paths(tmp_path: Path) -> None:
    """Stop allocation before adding any route segment to a full group."""
    fixture = SpecCommandFixture(tmp_path)
    blocked_parent = tmp_path / "specs" / "numbered" / "0"
    blocked_parent.mkdir(parents=True)
    for number in range(5):
        (blocked_parent / f"occupied-{number}").mkdir()
    before = snapshot_tree(tmp_path)

    result = fixture.run(
        "create-new-feature.ps1",
        tmp_path / "specs",
        "-Json",
        "-Number",
        "4263",
        "-ShortName",
        "capacity",
        "Test bounded allocation",
    )

    assert result.returncode != 0
    assert "five children" in result.stderr
    assert str(blocked_parent) in result.stderr
    assert "Examined" in result.stderr
    assert snapshot_tree(tmp_path) == before


def test_occupied_destination_preserves_existing_records(tmp_path: Path) -> None:
    """Keep source and destination files unchanged when allocation finds a collision."""
    fixture = SpecCommandFixture(tmp_path)
    fixture.feature("specs/live/20261013-182828-source")
    fixture.feature("specs/numbered/0/0/1/1/4/0/2/3/4263-capacity")
    before = snapshot_tree(tmp_path)

    result = fixture.run(
        "create-new-feature.ps1",
        tmp_path / "specs",
        "-Json",
        "-Number",
        "4263",
        "-ShortName",
        "capacity",
        "Test occupied destination",
    )

    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert snapshot_tree(tmp_path) == before


def test_non_file_source_blocks_prerequisites_without_mutation(tmp_path: Path) -> None:
    """Reject a source specification that cannot be read as a file."""
    fixture = SpecCommandFixture(tmp_path)
    feature = fixture.feature("specs/live/20261013-182828-unreadable")
    (feature / "spec.md").unlink()
    (feature / "spec.md").mkdir()
    original = fixture.pointer.read_bytes()
    before = snapshot_tree(tmp_path)

    result = fixture.run("check-prerequisites.ps1", feature, "-Json", "-RequireSpec")

    assert result.returncode != 0
    assert snapshot_tree(tmp_path) == before
    assert fixture.pointer.read_bytes() == original


@pytest.mark.skipif(
    os.name == "nt" or os.geteuid() == 0, reason="Directory permission checks need a non-root POSIX user."
)
def test_unreadable_source_blocks_prerequisites_without_mutation(tmp_path: Path) -> None:
    """Reject a source directory that denies feature-file access."""
    fixture = SpecCommandFixture(tmp_path)
    feature = fixture.feature("specs/live/20261013-182828-private")
    original_mode = feature.stat().st_mode & 0o777
    original_pointer = fixture.pointer.read_bytes()
    before = snapshot_tree(tmp_path)
    feature.chmod(0)
    try:
        result = fixture.run("check-prerequisites.ps1", feature, "-Json", "-RequireSpec")
    finally:
        feature.chmod(original_mode)

    assert result.returncode != 0
    assert snapshot_tree(tmp_path) == before
    assert fixture.pointer.read_bytes() == original_pointer


def test_generator_creates_grouped_record(tmp_path: Path) -> None:
    """Exercise allocation through its public command in an isolated worktree."""
    fixture = SpecCommandFixture(tmp_path)
    result = fixture.run(
        "create-new-feature.ps1",
        tmp_path / "specs" / "selected",
        "-Json",
        "-Timestamp",
        "-ShortName",
        "new-record",
        "Test bounded allocation",
    )
    assert result.returncode == 0, result.stderr
    spec = Path(json.loads(result.stdout)["SPEC_FILE"])
    relative = spec.relative_to(tmp_path / "specs" / "live")
    assert len(relative.parts) == 19
    assert set(relative.parts[:17]) <= set("01234")
    assert spec.is_file()
    assert spec.read_text(encoding="utf-8").startswith("# Feature Specification:")


def test_explicit_persistence_remains_available(tmp_path: Path) -> None:
    """Preserve intentional selector writes while read-only commands opt out."""
    fixture = SpecCommandFixture(tmp_path)
    feature = fixture.feature("specs/live/20261013-182828-direct")
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.fail("Install pwsh to verify explicit persistence.")
    environment = dict(os.environ, SPECIFY_INIT_DIR=str(tmp_path), SPECIFY_FEATURE_DIRECTORY=str(feature))
    command = f". '{fixture.scripts / 'common.ps1'}'; Get-FeaturePathsEnv | ConvertTo-Json -Compress"
    result = subprocess.run([pwsh, "-NoProfile", "-Command", command], env=environment, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    saved = json.loads(fixture.pointer.read_text(encoding="utf-8"))["feature_directory"]
    assert Path(saved) == feature.relative_to(tmp_path)


@pytest.mark.parametrize("number", [0, 800, 4263, 390624])
def test_numeric_feature_route_remains_stable(number: int, tmp_path: Path) -> None:
    """Pin the actual numeric resolver, not only the digit helper."""
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.fail("Install pwsh to verify numeric feature routing.")
    name = f"{number}-numeric"
    environment = dict(os.environ, ROUTE_ROOT=str(tmp_path), RECORD_NAME=name, FEATURE_NUMBER=str(number))
    command = (
        f". '{ROUTE_SCRIPT}'; "
        "Resolve-SpecFeaturePath -SpecsDir $env:ROUTE_ROOT -BranchName $env:RECORD_NAME -Number $env:FEATURE_NUMBER"
    )
    result = subprocess.run([pwsh, "-NoProfile", "-Command", command], env=environment, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    resolved = Path(result.stdout.strip())
    assert resolved == tmp_path / "numbered" / python_route(number) / name
    segments = resolved.relative_to(tmp_path / "numbered").parts
    assert len(segments) == 9
    assert all(digit in "01234" for digit in segments[0:8])


@pytest.mark.parametrize(
    ("script", "missing", "arguments"),
    [
        ("setup-plan.ps1", "plan.md", ("-Json",)),
        ("setup-tasks.ps1", "tasks.md", ("-Json",)),
        (
            "create-new-feature.ps1",
            "spec.md",
            ("-Json", "-Number", "4263", "-ShortName", "capacity", "-AllowExistingBranch", "Test bounded artifacts"),
        ),
    ],
)
def test_full_artifact_root_rejects_generation(
    tmp_path: Path, script: str, missing: str, arguments: tuple[str, ...]
) -> None:
    """Reject a sixth artifact before creating output or changing selection."""
    fixture = SpecCommandFixture(tmp_path)
    feature = fixture.feature("specs/numbered/0/0/1/1/4/0/2/3/4263-capacity")
    (feature / missing).unlink()
    for name in ("analysis.md", "ownership.md"):
        (feature / name).write_text("# Existing artifact\n")
    original = fixture.pointer.read_bytes()
    before = snapshot_tree(tmp_path)
    result = fixture.run(script, feature, *arguments)
    assert result.returncode != 0
    assert "five children" in result.stderr
    assert snapshot_tree(tmp_path) == before
    assert fixture.pointer.read_bytes() == original


def test_independent_worktrees_preserve_selection(tmp_path: Path) -> None:
    """Keep generated context and selected artifacts inside each worktree."""
    for owner in ("first", "second"):
        fixture = SpecCommandFixture(tmp_path / owner)
        feature = fixture.feature("specs/live/20261013-182828-shared")
        original = fixture.pointer.read_bytes()
        result = fixture.run("update-agent-context.ps1", feature, "-AgentType", "copilot")
        assert result.returncode == 0, result.stderr
        assert (fixture.root / ".specify" / "memory" / "agent-context.md").is_file()
        assert fixture.pointer.read_bytes() == original
        assert not (fixture.root / "AGENTS.md").exists()
        assert not (fixture.root / "CLAUDE.md").exists()
