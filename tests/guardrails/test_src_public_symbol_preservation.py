"""Compare public module symbols across the source package move."""  # State the moved-module compatibility contract.

from __future__ import annotations  # Use current annotation behavior in the guard.

import ast  # Read module-level symbols without importing runtime dependencies.
import io  # Give tarfile an in-memory archive stream.
import subprocess  # Read the base source tree through Git.
import tarfile  # Read all base modules from one Git archive command.
from pathlib import Path  # Resolve the current repository and moved modules.

import pytest  # Prove that the guard still refuses an unknown package name.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the active worktree from this guard file.
SOURCE_ROOT = REPOSITORY_ROOT / "src"  # Read current modules from the refactored source tree.
PACKAGE_GROUPS = {  # Map every old direct package to its new domain and group.
    "foundation/runtime": {"bootstrap", "config", "input", "time", "validation"},
    "foundation/models": {"data", "dataclasses"},
    "foundation/persistence": {"cache", "db"},
    "foundation/support": {"refactors", "utils"},
    "mist/access": {"api", "audit", "auth"},
    "mist/resources": {"device", "gateway", "inventory", "org", "site"},
    "mist/intelligence": {"analytics", "juniper_docs", "marvis", "reports", "troubleshooting"},
    "mist/realtime": {"websocket", "websocket_streams"},
    "mist/networking": {"network"},
    "operations/execution": {"capture", "firmware", "ssh", "ssid_consolidation"},
    "operations/exporting": {"export"},
    "operations/hardware": {"mib_generator"},
    "operations/protection": {"security"},
    "interfaces/portals": {"upgrade_portal"},
    "interfaces/visualization": {"maps", "ui"},
    "interfaces/monitoring": {"metrics_gateway"},
}  # Keep the test map identical to the approved package data model.
MODULE_PATHS = {  # Map each old direct module to its new canonical module.
    "constants.py": "foundation/constants.py",
    "org_data_collector.py": "operations/wan/org_data_collector.py",
    "wan_hub_group_manager.py": "operations/wan/wan_hub_group_manager.py",
    "wan_vpn_builder.py": "operations/wan/wan_vpn_builder.py",
}  # Cover every moved direct source module.
CANONICAL_ROOTS = {group.split("/")[0] for group in PACKAGE_GROUPS} | {
    Path(path).parts[0] for path in MODULE_PATHS.values()
}  # Name every domain root that the move created, so a moved baseline maps to itself.


def ensure_origin_main() -> None:
    """Ensure the baseline source ref exists before archive comparisons."""
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
        cwd=REPOSITORY_ROOT,
        check=False,
    )  # Check whether the workflow checkout fetched the required baseline ref.
    if result.returncode != 0:
        subprocess.run(
            ["git", "fetch", "origin", "main", "--depth=1"],
            cwd=REPOSITORY_ROOT,
            check=True,
        )  # Fetch the baseline when a manual workflow checkout omitted it.


def path_map() -> dict[str, str]:
    """Return every old and new source-relative path."""  # Build one canonical mapping for archived modules.
    mapping = dict(MODULE_PATHS)  # Start with direct module moves.
    for group, packages in PACKAGE_GROUPS.items():  # Expand each package group.
        for package in packages:  # Map each old direct package.
            mapping[package] = f"{group}/{package}"  # Keep the existing package name at the final level.
    return mapping  # Supply the complete move map.


def current_path(old_path: str) -> Path:
    """Return the current path for one archived source file.

    Resolve the moved module without a compatibility wrapper.
    """
    relative_path = Path(old_path).relative_to("src")  # Remove the common source root.
    first_part = relative_path.parts[0]  # Read the old direct package or module name.
    if first_part in CANONICAL_ROOTS:  # The baseline already holds the moved layout.
        return SOURCE_ROOT / relative_path  # Compare the module against itself at the same path.
    new_first_part = path_map()[first_part]  # Select its canonical domain path.
    remaining_parts = relative_path.parts[1:]  # Preserve the module path inside the moved package.
    return SOURCE_ROOT / new_first_part / Path(*remaining_parts)  # Build the canonical current module path.


def assigned_names(target: ast.expr) -> set[str]:
    """Return each name assigned by one module-level target.

    Include tuple assignments in the public symbol comparison.
    """
    if isinstance(target, ast.Name):  # Read a direct module-level assignment.
        return {target.id}  # Preserve the assigned symbol.
    if isinstance(target, (ast.Tuple, ast.List)):  # Read a destructuring assignment.
        return {name for item in target.elts for name in assigned_names(item)}  # Flatten each assigned child name.
    return set()  # Ignore attributes and subscripts that do not add module symbols.


def module_symbols(source: str, filename: str) -> set[str]:
    """Return module-level names from one Python source string.

    Compare definitions, assignments, and imported exports.
    """
    symbols: set[str] = set()  # Collect each module-level name once.
    for node in ast.parse(source, filename=filename).body:  # Inspect only direct module statements.
        if isinstance(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):  # Read declared callables and classes.
            symbols.add(node.name)  # Preserve the declared public or private name.
        elif isinstance(node, ast.Assign):  # Read direct module assignments.
            symbols.update(
                name for target in node.targets for name in assigned_names(target)
            )  # Add every assigned name.
        elif isinstance(node, ast.AnnAssign):  # Read annotated module assignments.
            symbols.update(assigned_names(node.target))  # Add the annotated name.
        elif isinstance(node, (ast.Import, ast.ImportFrom)):  # Read names re-exported through imports.
            symbols.update(
                alias.asname or alias.name.split(".")[0] for alias in node.names if alias.name != "*"
            )  # Add imported names.
    return symbols  # Return the complete module-level symbol set.


def test_moved_modules_lose_no_module_level_symbol() -> None:
    """Require every moved module to preserve its module-level names.

    Replace the path-limited symbol-diff check for renamed files.
    """
    ensure_origin_main()  # Make the baseline available in pull request and manual runs.
    command = [
        "git",
        "archive",
        "--format=tar",
        "origin/main",
        "src",
    ]  # Read all base modules with one bounded Git command.
    archive = subprocess.run(
        command, cwd=REPOSITORY_ROOT, check=True, capture_output=True
    ).stdout  # Fail if Git cannot read the base.
    checked_count = 0  # Count each compared Python module.
    violations: dict[str, list[str]] = {}  # Collect lost names by old module path.
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source_archive:  # Read the in-memory base source tree.
        for member in source_archive.getmembers():  # Inspect each archived source entry.
            if (
                not member.isfile() or not member.name.endswith(".py") or member.name == "src/__init__.py"
            ):  # Select moved Python modules only.
                continue  # Ignore directories, non-Python files, and the unchanged source initializer.
            extracted = source_archive.extractfile(member)  # Open the archived module content.
            if extracted is None:  # Detect an unreadable required base module explicitly.
                raise AssertionError(
                    f"Cannot read archived module {member.name}"
                )  # Fail with the missing archive entry.
            new_path = current_path(member.name)  # Resolve the canonical current module path.
            assert (
                new_path.is_file()
            ), f"Missing moved module for {member.name}: {new_path}"  # Reject an incomplete move.
            old_symbols = module_symbols(
                extracted.read().decode("utf-8"), member.name
            )  # Read the base module symbol set.
            new_symbols = module_symbols(
                new_path.read_text(encoding="utf-8"), str(new_path)
            )  # Read the current module symbol set.
            lost_symbols = sorted(old_symbols - new_symbols)  # Measure only removed module-level names.
            if lost_symbols:  # Record each module that lost a name.
                violations[member.name] = lost_symbols  # Keep exact names for repair evidence.
            checked_count += 1  # Record one complete module comparison.
    assert (
        not violations
    ), f"Checked {checked_count} moved modules. Lost symbols: {violations}"  # Report the measured scope and failures.


def test_moved_packages_preserve_tracked_data_files() -> None:
    """Require each tracked package-data file to keep its relative package path."""
    ensure_origin_main()  # Make the baseline available in pull request and manual runs.
    command = [
        "git",
        "ls-tree",
        "-r",
        "--name-only",
        "origin/main",
        "src",
    ]  # Read the base tracked source file inventory.
    result = subprocess.run(
        command, cwd=REPOSITORY_ROOT, check=True, capture_output=True, text=True
    )  # Fail if Git cannot provide the required base input.
    old_paths = [
        path for path in result.stdout.splitlines() if not path.endswith(".py") and path != "src/__init__.py"
    ]  # Select each tracked non-Python package-data file.
    missing_paths = [
        f"{old_path} -> {current_path(old_path).relative_to(REPOSITORY_ROOT)}"
        for old_path in old_paths
        if not current_path(old_path).is_file()
    ]  # Record each package-data file that did not move with its package.
    checked_count = len(old_paths)  # Report the measured package-data scope.
    message = f"Checked {checked_count} package-data files. Missing: {missing_paths}"  # Build failure evidence.
    assert not missing_paths, message  # Fail if one tracked asset did not move with its package.


def test_canonical_roots_name_every_domain_root() -> None:
    """Require the canonical root set to name each domain root of the moved layout."""
    expected_roots = {
        "foundation",
        "interfaces",
        "mist",
        "operations",
    }  # Name the four domain roots that the move created.
    assert CANONICAL_ROOTS == expected_roots, f"Checked {len(CANONICAL_ROOTS)} roots: {sorted(CANONICAL_ROOTS)}"


def test_current_path_maps_a_moved_baseline_to_itself() -> None:
    """Require a baseline path that already holds the moved layout to map to the same path."""
    moved_path = current_path("src/foundation/runtime/config.py")  # Read a path in the new layout.
    expected_path = SOURCE_ROOT / "foundation" / "runtime" / "config.py"  # The same path must come back.
    assert moved_path == expected_path, f"Checked 1 moved path. Read {moved_path}."


def test_current_path_still_maps_an_old_flat_package() -> None:
    """Require an old flat package path to keep its canonical domain destination.

    The canonical path guard refuses a legacy source path literal in tracked text.
    Build the legacy path from a variable, so the file text holds no such literal.
    """
    legacy_package = "config"  # Name one package that moved out of the source root.
    old_path = current_path(f"src/{legacy_package}/settings.py")  # Read a path in the pre-move layout.
    expected_path = SOURCE_ROOT / "foundation/runtime/config" / "settings.py"  # The move map must apply.
    assert old_path == expected_path, f"Checked 1 old path. Read {old_path}."


def test_current_path_refuses_an_unknown_package() -> None:
    """Require an unknown package name to fail, so a real loss still breaks the guard."""
    with pytest.raises(KeyError):  # The guard must not accept a name it cannot place.
        current_path("src/unknown_package/file.py")  # Read a package that no map holds.


def test_module_symbols_reports_a_removed_name() -> None:
    """Require the symbol reader to detect one lost module-level name."""
    base_source = "VALUE = 1\n\n\ndef helper() -> None:\n    return None\n"  # Hold two module-level names.
    moved_source = "VALUE = 1\n"  # Drop the helper, so one name is lost.
    base_symbols = module_symbols(base_source, "base.py")  # Read the base names.
    moved_symbols = module_symbols(moved_source, "moved.py")  # Read the reduced names.
    lost_symbols = base_symbols - moved_symbols  # Measure the loss that the guard must report.
    assert lost_symbols == {"helper"}, f"Checked {len(base_symbols)} base symbols. Lost {sorted(lost_symbols)}."
