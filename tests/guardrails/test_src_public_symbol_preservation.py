"""Compare public module symbols across the source package move."""  # State the moved-module compatibility contract.

from __future__ import annotations  # Use current annotation behavior in the guard.

import ast  # Read module-level symbols without importing runtime dependencies.
import io  # Give tarfile an in-memory archive stream.
import subprocess  # Read the base source tree through Git.
import tarfile  # Read all base modules from one Git archive command.
from pathlib import Path  # Resolve the current repository and moved modules.

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
            assert (
                extracted is not None
            ), f"Cannot read archived module {member.name}"  # Fail if the required base input is unreadable.
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
