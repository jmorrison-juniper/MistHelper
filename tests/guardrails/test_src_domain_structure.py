"""Guard the source domain package structure."""  # Explain the structural contract under test.

from __future__ import annotations  # Use current annotation behavior in the guard.

import re  # Find old canonical import paths in repository Python files.
import subprocess  # Read the tracked repository file set from Git.
from pathlib import Path  # Inspect the repository with platform-safe paths.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the checked-out repository from this guard file.
SOURCE_ROOT = REPOSITORY_ROOT / "src"  # Limit hierarchy checks to the product source package.
EXPECTED_DOMAINS = {"foundation", "interfaces", "mist", "operations"}  # Define the approved direct source packages.
LEGACY_PACKAGES = {  # Record every package that moved from the source root.
    "analytics",
    "api",
    "audit",
    "auth",
    "bootstrap",
    "cache",
    "capture",
    "config",
    "data",
    "dataclasses",
    "db",
    "device",
    "export",
    "firmware",
    "gateway",
    "input",
    "inventory",
    "juniper_docs",
    "maps",
    "marvis",
    "metrics_gateway",
    "mib_generator",
    "network",
    "org",
    "refactors",
    "reports",
    "security",
    "site",
    "ssh",
    "ssid_consolidation",
    "time",
    "troubleshooting",
    "ui",
    "upgrade_portal",
    "utils",
    "validation",
    "websocket",
    "websocket_streams",
}  # Make any reintroduced old canonical path fail the guard.
TEXT_SUFFIXES = {  # Name tracked text formats that can contain canonical source paths.
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mib",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}  # Cover code, configuration, scripts, and current documentation.
PERFORMANCE_CATALOGS = {  # Keep active source inventories inside the old-path guard.
    "specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv",
    "specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv",
}  # Exclude other historical artifacts without excluding these active catalogs.


def visible_children(directory: Path) -> list[Path]:
    """Return structural children and exclude package metadata."""  # Count only hierarchy items governed by the issue.
    return [
        child for child in directory.iterdir() if child.name not in {"__init__.py", "__pycache__"}
    ]  # Exclude package metadata.


def test_src_has_only_domain_packages() -> None:
    """Require the approved direct source package set."""  # Preserve the existing behavior.
    children = visible_children(SOURCE_ROOT)  # Read the measured direct source children.
    child_names = {child.name for child in children}  # Compare names without filesystem ordering.
    assert (
        child_names == EXPECTED_DOMAINS
    ), f"Checked {len(children)} src children: {sorted(child_names)}"  # Report the measured count and names.


def test_new_domain_levels_follow_five_item_rule() -> None:
    """Require each new domain level to contain five children or fewer."""  # Preserve the existing behavior.
    checked_directories = [
        SOURCE_ROOT / domain for domain in EXPECTED_DOMAINS
    ]  # Check each domain introduced by issue 3574.
    checked_directories += [
        child for domain in checked_directories for child in visible_children(domain) if child.is_dir()
    ]  # Check each new group level.
    violations = {
        str(directory.relative_to(REPOSITORY_ROOT)): len(visible_children(directory))
        for directory in checked_directories
        if len(visible_children(directory)) > 5
    }  # Collect every measured violation.
    message = (  # Build one bounded structural failure message.
        f"Checked {len(checked_directories)} new package levels. "  # Report the measured directory count.
        f"Violations: {violations}"  # Report each measured violation.
    )
    assert not violations, message  # Fail with the checked level count and each violation.


def test_tracked_text_uses_only_canonical_source_paths() -> None:
    """Reject each source path that existed before the move."""  # Preserve the existing behavior.
    separators = r"[./\\]"  # Accept import paths and both filesystem separator forms.
    legacy_pattern = re.compile(
        r"(?<!mist-ops-platform/)(?<!mist-ops-platform\\)\bsrc"
        + separators
        + r"("
        + "|".join(sorted(LEGACY_PACKAGES))
        + r")(?:"
        + separators
        + r"|\b)"
    )  # Match an old direct source child.
    result = subprocess.run(  # Read only files that the pull request can change.
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )  # Fail if Git cannot provide the required input.
    tracked_paths = [
        Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value
    ]  # Decode each tracked path.
    excluded_roots = {"changelog.d", "mist-ops-platform"}  # Exclude immutable fragments and the independent project.
    excluded_files = {
        REPOSITORY_ROOT / "compose.yml",
        REPOSITORY_ROOT / "documentation" / "security" / "codeql-verdict-register.md",
    }  # Keep protected configuration and historical alert paths outside the move scan.
    text_files = [
        REPOSITORY_ROOT / path
        for path in tracked_paths
        if path.suffix.lower() in TEXT_SUFFIXES
        and (REPOSITORY_ROOT / path).is_file()
        and not excluded_roots.intersection(path.parts)
        and REPOSITORY_ROOT / path not in excluded_files
    ]  # Scan each tracked text input.
    text_files = [
        path
        for path in text_files
        if path.name not in {"CHANGELOG.md", ".spec-context.events.jsonl"}
        and ("artifacts" not in path.parts or path.relative_to(REPOSITORY_ROOT).as_posix() in PERFORMANCE_CATALOGS)
    ]  # Exclude immutable history and generated evidence.
    violations = [
        str(path.relative_to(REPOSITORY_ROOT))
        for path in text_files
        if legacy_pattern.search(path.read_text(encoding="utf-8"))
    ]  # Collect files that still name an old path.
    assert (
        not violations
    ), f"Checked {len(text_files)} text files. Legacy source paths: {violations}"  # Preserve the existing behavior.
