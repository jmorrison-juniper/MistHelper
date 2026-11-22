"""Guardrail: the Spec Kit ignore file keeps the routing pointer tracked (issue #4882).

Why:
    `.specify/feature.json` is the routing pointer for the routed spec layout.
    The upstream `.specify/.gitignore` lists `feature.json` as machine-local
    state. Without a re-include rule, git ignores the pointer. The Specify CLI
    reports a missing managed file as ERROR, so the repository keeps a copy of
    that file. The copy re-includes the pointer after the upstream rule.

    These tests ask git for the answer instead of reading the file text. A rule
    that ignores the pointer fails the repository check. The fixture tests prove
    that the check reports an ignored pointer, so a passing check means something.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
POINTER = ".specify/feature.json"
IGNORE_FILE = REPOSITORY_ROOT / ".specify" / ".gitignore"

# `git check-ignore` exits 0 for an ignored path and 1 for a path that is not
# ignored. Any other exit code means that git could not evaluate the rules.
EXIT_IGNORED = 0
EXIT_NOT_IGNORED = 1


def pointer_is_ignored(repository: Path) -> bool:
    """Return whether git ignores the routing pointer in a repository.

    Why:
        The check passes `--no-index`, so git applies the rules to the pointer
        even when the pointer is tracked. Without that flag, git skips tracked
        files, and a rule that ignores the pointer would pass the check.
        Quiet mode returns 1 for a pointer that a negation rule re-includes.
        Verbose mode reports that pointer with exit code 0, so this check uses
        quiet mode.

    Args:
        repository: Root directory of a git repository.

    Returns:
        True when git ignores `.specify/feature.json`. False when it does not.

    Raises:
        RuntimeError: When git cannot evaluate the ignore rules.
    """
    completed = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", POINTER],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == EXIT_IGNORED:
        return True
    if completed.returncode == EXIT_NOT_IGNORED:
        return False
    raise RuntimeError(f"git check-ignore failed: {completed.stderr.strip()}")


def write_fixture(repository: Path, ignore_text: str) -> None:
    """Create a git repository whose `.specify/.gitignore` holds the given rules.

    Args:
        repository: Empty directory that becomes the fixture repository.
        ignore_text: Full content of the fixture `.specify/.gitignore` file.
    """
    (repository / ".specify").mkdir()
    (repository / ".specify" / ".gitignore").write_text(ignore_text, encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)


def test_ignore_file_is_present() -> None:
    """The repository keeps its customized `.specify/.gitignore` file."""
    assert IGNORE_FILE.is_file(), f"missing managed file: {IGNORE_FILE}"


def test_repository_does_not_ignore_the_pointer() -> None:
    """The repository rules leave the routing pointer tracked."""
    ignored = pointer_is_ignored(REPOSITORY_ROOT)
    assert not ignored, "git ignores .specify/feature.json"


def test_upstream_rule_alone_ignores_the_pointer(tmp_path: Path) -> None:
    """A fixture with only the upstream rule is reported as ignoring the pointer.

    Args:
        tmp_path: Empty directory that pytest provides for this test.
    """
    write_fixture(tmp_path, "feature.json\n")
    assert pointer_is_ignored(tmp_path), "the detector must see the upstream rule"


def test_reinclude_after_the_rule_keeps_the_pointer(tmp_path: Path) -> None:
    """A re-include rule placed after the upstream rule keeps the pointer.

    Args:
        tmp_path: Empty directory that pytest provides for this test.
    """
    write_fixture(tmp_path, "feature.json\n!feature.json\n")
    assert not pointer_is_ignored(tmp_path), "the re-include rule must win"


def test_reinclude_before_the_rule_does_not_keep_the_pointer(tmp_path: Path) -> None:
    """A re-include rule placed before the upstream rule loses to it.

    This edge case protects the order of the rules. A later edit that moves the
    negation above the upstream rule makes the repository check fail.

    Args:
        tmp_path: Empty directory that pytest provides for this test.
    """
    write_fixture(tmp_path, "!feature.json\nfeature.json\n")
    assert pointer_is_ignored(tmp_path), "the later upstream rule must win"
