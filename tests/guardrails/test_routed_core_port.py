"""Guardrail: the routed core keeps its routing rules through the Spec Kit 1.4.3 port (issue #4873).

Why:
    A later sync from upstream Spec Kit can drop a routing rule without any test
    failing. These tests read the PowerShell sources and fail when a rule that the
    routed layout needs is no longer present. They check each rule by name, so an
    unrelated refactor does not break them.
"""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY_ROOT / ".specify" / "scripts" / "powershell"
COMMON = SCRIPTS / "common.ps1"
CREATE_NEW_FEATURE = SCRIPTS / "create-new-feature.ps1"


def read_script(path: Path) -> str:
    """Return a PowerShell script with LF line endings.

    Why:
        Windows checkouts store `.ps1` files with CRLF line endings, so a
        multi-line search needs the same line endings on every platform.

    Args:
        path: Script to read.

    Returns:
        The script text with CRLF replaced by LF.
    """
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_numbering_scans_the_routed_tree() -> None:
    """The numbering scan descends into the routed folders."""
    text = read_script(CREATE_NEW_FEATURE)
    assert "Get-ChildItem -LiteralPath $SpecsDir -Directory -Recurse" in text, (
        "create-new-feature.ps1 must scan specs/ recursively, or routed records get the wrong number"
    )


def test_feature_selection_keeps_the_routing_assertion() -> None:
    """The routing assertion runs before the feature directory is used."""
    text = read_script(COMMON)
    assert "Assert-SpecFeatureSelection -RepoRoot $repoRoot -FeatureDir $featureDir" in text, (
        "common.ps1 must reject features outside specs/ and features nested in other features"
    )


def test_design_artifacts_resolve_through_the_routed_helper() -> None:
    """The design artifacts use the helper that rejects conflicting ownership."""
    text = read_script(COMMON)
    assert "Get-SpecDesignArtifact -FeatureDir $featureDir -Name 'research.md'" in text, (
        "common.ps1 must select design artifacts through Get-SpecDesignArtifact"
    )


def test_no_persist_switch_guards_the_pointer_write() -> None:
    """The environment switch and the parameter both block the pointer write."""
    text = read_script(COMMON)
    assert "$env:SPECIFY_FEATURE_NO_PERSIST" in text, (
        "common.ps1 must honor SPECIFY_FEATURE_NO_PERSIST, so orchestrators can block pointer writes"
    )
    assert "if ($env:SPECIFY_FEATURE_DIRECTORY -and -not $noPersist) {" in text, (
        "the pointer write must check $noPersist, or read-only commands change .specify/feature.json"
    )


def test_template_resolution_keeps_its_repository_order() -> None:
    """The 1.4.3 priority and composition engine stays out until its own issue decides it."""
    text = read_script(COMMON)
    assert "Get-SortedExtensionIds" not in text, (
        "the 1.4.3 template engine was adopted; the routed template order needs its own decision"
    )
