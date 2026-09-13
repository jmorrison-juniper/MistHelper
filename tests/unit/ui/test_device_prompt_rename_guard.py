"""Guard against call sites that survived the issue #431 device-prompt rename.

Issue #431 removed ``PromptUtils.select_device`` and made
``PromptUtils.select_device_id_from_inventory`` the one device prompt. One call
site in ``src/export/site_insights/device_metric_operation.py`` kept the old
name. No unit test covered it, so menu 76 raised ``AttributeError`` until a live
``--testinteractive`` run found it.

These tests fail if the old name comes back.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ui.prompt_utils import PromptUtils

REPO_ROOT = Path(__file__).resolve().parents[3]
SCANNED_DIRS = ("src", "web_portal")
REMOVED_NAME = "select_device"
CANONICAL_NAME = "select_device_id_from_inventory"


def _python_files() -> list[Path]:
    """Return every Python file in the scanned source directories."""
    files: list[Path] = []
    for folder in SCANNED_DIRS:
        root = REPO_ROOT / folder
        if root.is_dir():
            files.extend(root.rglob("*.py"))
    return files


def _attribute_calls(tree: ast.AST) -> list[str]:
    """Return the attribute name of every call of the form ``something.name(...)``."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)
    return names


def test_canonical_prompt_exists() -> None:
    """The canonical device prompt must stay on PromptUtils."""
    assert hasattr(PromptUtils, CANONICAL_NAME), f"PromptUtils lost {CANONICAL_NAME}"


def test_removed_prompt_stays_removed() -> None:
    """Issue #431 removed the old prompt. It must not come back."""
    assert not hasattr(
        PromptUtils, REMOVED_NAME
    ), f"PromptUtils.{REMOVED_NAME} came back. Issue #431 replaced it with {CANONICAL_NAME}."


def test_no_source_file_calls_the_removed_prompt() -> None:
    """No source file may call the removed device prompt.

    A call to the removed name raises AttributeError at runtime, and only an
    interactive run reaches most of those code paths.
    """
    offenders: list[str] = []
    for path in _python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):  # Not parseable, so not a call site.
            continue
        if REMOVED_NAME in _attribute_calls(tree):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert not offenders, (
        f"These files call the removed PromptUtils.{REMOVED_NAME}: {offenders}. "
        f"Use {CANONICAL_NAME}(site_id, device_type=...) instead."
    )


@pytest.mark.parametrize(
    "module_path",
    ["src/export/site_insights/device_metric_operation.py"],
)
def test_known_regression_site_uses_canonical_prompt(module_path: str) -> None:
    """The menu 76 module must call the canonical prompt.

    This file held the missed call site, so it gets its own check.
    """
    source = (REPO_ROOT / module_path).read_text(encoding="utf-8")
    assert CANONICAL_NAME in source, f"{module_path} no longer calls {CANONICAL_NAME}"
