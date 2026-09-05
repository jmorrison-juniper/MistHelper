"""Guard the commit citations of the upgrade capture portal documents.

Why:
    Issue #1997 records the fault. Two documents of this feature cite commits of
    the branch `feat/1823-upgrade-capture-portal` as evidence. A squash merge
    replaced that branch, and the branch is deleted, so no cited hash resolves in
    a fresh clone. A reader who runs `git show <hash>` gets a fatal error and no
    evidence.

    `specs/1823-upgrade-capture-portal/commit-citations.md` records the subject of
    every one of those hashes. This test keeps that record complete. A new
    citation must either resolve in the repository or carry an entry in the
    record.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404  # WHY: this test asks git whether one object exists.
from pathlib import Path

import pytest

SPEC_FOLDER = Path(__file__).resolve().parents[3] / "specs" / "1823-upgrade-capture-portal"
CITATION_RECORD = SPEC_FOLDER / "commit-citations.md"
CITING_DOCUMENTS = ("audit-2026-08-20.md", "HANDOFF.md")

# A hash inside backticks. The pattern demands one letter, because a plain run of
# digits is a timestamp or a count and never a commit.
HASH_PATTERN = re.compile(r"`([0-9a-f]{7,40})`")
LETTER_PATTERN = re.compile(r"[a-f]")

# The floor of the record. The squash merge of pull request #1825 voided 19
# citations. A record that drops below this count lost an entry.
RECORDED_CITATION_FLOOR = 19


def cited_hashes(text: str) -> set[str]:
    """Return every commit hash that one document cites.

    Args:
        text: The whole document.

    Returns:
        The hashes, with every run of digits dropped.
    """
    found = HASH_PATTERN.findall(text)  # Every backtick value that looks like a hash.
    return {value for value in found if LETTER_PATTERN.search(value)}  # Drop a timestamp and a count.


def resolves_in_this_repository(commit: str) -> bool:
    """Report whether git can read one object by hash.

    Args:
        commit: The hash to read.

    Returns:
        True when git answers an object type.
    """
    answer = subprocess.run(  # nosec B603 B607  # WHY: a fixed command with one hash from a document.
        ["git", "cat-file", "-t", commit],
        cwd=SPEC_FOLDER,
        capture_output=True,
        check=False,
        text=True,
    )
    return answer.returncode == 0  # A missing object answers a non-zero code.


class TestEveryCitationStaysReadable:
    """A reader must reach the meaning of every cited hash."""

    def test_the_record_exists_and_holds_its_entries(self) -> None:
        """The citation record must list every voided hash."""
        assert CITATION_RECORD.is_file(), "The citation record is missing."
        entries = cited_hashes(CITATION_RECORD.read_text(encoding="utf-8"))
        assert len(entries) >= RECORDED_CITATION_FLOOR, "The citation record lost an entry."

    @pytest.mark.parametrize("name", CITING_DOCUMENTS)
    def test_every_cited_hash_resolves_or_carries_a_record(self, name: str) -> None:
        """A citation must name a readable object or an entry in the record."""
        document = SPEC_FOLDER / name
        assert document.is_file(), f"The document {name} is missing."
        recorded = cited_hashes(CITATION_RECORD.read_text(encoding="utf-8"))  # The voided hashes.
        unexplained = [
            commit
            for commit in sorted(cited_hashes(document.read_text(encoding="utf-8")))  # Every citation.
            if commit not in recorded and not resolves_in_this_repository(commit)  # Neither route works.
        ]
        assert not unexplained, (
            f"The document {name} cites {unexplained}. Each one names no readable object and holds no "
            f"entry in commit-citations.md. Cite a pull request number or an issue number instead."
        )

    @pytest.mark.parametrize("name", CITING_DOCUMENTS)
    def test_each_document_points_at_the_record(self, name: str) -> None:
        """A reader who opens the document must learn where the meaning lives."""
        text = (SPEC_FOLDER / name).read_text(encoding="utf-8")
        assert "commit-citations.md" in text, f"The document {name} names no citation record."
