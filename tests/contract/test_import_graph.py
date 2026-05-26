"""Contract tests for decomposition import boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MISTHELPER_PATH = REPO_ROOT / "MistHelper.py"
SRC_PATH = REPO_ROOT / "src"


def _collect_import_roots(py_file: Path) -> set[str]:
    """Return top-level import roots from a Python file."""
    source_text = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported_name in node.names:
                roots.add(imported_name.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_repository_paths_exist() -> None:
    """Verify expected repository roots for contract checks exist."""
    assert MISTHELPER_PATH.exists(), "Expected MistHelper.py at repository root"
    assert SRC_PATH.exists(), "Expected src/ package at repository root"


def test_no_src_module_imports_globalimportmanager_directly() -> None:
    """Guard against accidental decomposition of GlobalImportManager in this wave."""
    violating_files: list[str] = []
    for py_file in SRC_PATH.rglob("*.py"):
        source_text = py_file.read_text(encoding="utf-8")
        if "GlobalImportManager" in source_text:
            violating_files.append(str(py_file.relative_to(REPO_ROOT)))
    assert not violating_files, (
        "GlobalImportManager references are out-of-scope for wave 2; "
        f"remove from: {violating_files}"
    )


def test_extracted_modules_do_not_import_forbidden_wave2_symbols() -> None:
    """Ensure extracted wave modules avoid forbidden scope symbols for this wave."""
    forbidden_tokens = {
        "GlobalImportManager",
    }

    candidate_paths = [
        SRC_PATH / "analytics",
        SRC_PATH / "gateway",
        SRC_PATH / "capture",
        SRC_PATH / "inventory",
        SRC_PATH / "ssh",
        SRC_PATH / "websocket",
        SRC_PATH / "export",
        SRC_PATH / "site",
    ]

    forbidden_references: dict[str, list[str]] = {}
    for candidate_path in candidate_paths:
        if not candidate_path.exists():
            continue
        for py_file in candidate_path.rglob("*.py"):
            source_text = py_file.read_text(encoding="utf-8")
            matched_tokens = sorted(token for token in forbidden_tokens if token in source_text)
            if matched_tokens:
                forbidden_references[str(py_file.relative_to(REPO_ROOT))] = matched_tokens

    assert not forbidden_references, (
        "Found forbidden wave-2 scope symbols in extracted module paths: "
        f"{forbidden_references}"
    )
