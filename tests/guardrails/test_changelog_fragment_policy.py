"""Guardrail: each change owns one release-note fragment (issue #2541).

Why:
    `CHANGELOG.md` holds more than 5,000 lines. Every change added its entry at
    the top of the same `## [Unreleased]` section, so each open pull request
    touched the same lines and every rebase reported a conflict. Pull request
    #2501 moved the release note into one fragment for each change under
    `changelog.d/`.

    That rule lives in five instruction files, and no gate reads one of them. An
    agent can edit `CHANGELOG.md` again, or invent a shared fragment name such
    as `unreleased.md`, and the conflict returns in silence. `.gitattributes`
    marks `CHANGELOG.md` with `merge=union`. A union merge hides a collision
    instead of reporting it, so that rule cannot replace a gate.

    These tests read the directory and the instruction files. They fail when a
    later change reintroduces a shared record.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT_DIR = REPOSITORY_ROOT / "changelog.d"

POLICY_FILE = "README.md"  # The one file here that states the rule instead of a change.

# The three name forms the policy allows. Each one carries a value that no other
# change can choose: the pull request number, the issue number, or the date.
SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"  # Lowercase words joined by a hyphen.
PULL_REQUEST_NAME = re.compile(rf"^pr-\d+(?:-{SLUG})?\.md$")
ISSUE_NAME = re.compile(rf"^issue-\d+-{SLUG}\.md$")
DATE_NAME = re.compile(rf"^(\d{{4}}-\d{{2}}-\d{{2}})-{SLUG}\.md$")
ALLOWED_NAMES = (PULL_REQUEST_NAME, ISSUE_NAME, DATE_NAME)

# A fragment states one of these five words, so the release coordinator groups
# the merged entries without reading the whole change.
CHANGE_TYPES = ("Added", "Changed", "Fixed", "Removed", "Security")

# A generic name defeats the policy, because two changes then pick one file.
SHARED_STEMS = frozenset({"index", "summary", "unreleased", "changelog", "notes", "all", "release"})

# Each file that must keep sending an author to the directory. A rewrite that
# drops the directory name returns this repository to one shared record.
# `changelog.d/README.md` is absent here, because that file describes the
# directory it sits in and writes "this directory" instead of the path.
GUIDANCE_FILES = (
    Path(".github/copilot-instructions.md"),
    Path(".specify/memory/constitution.md"),
    Path("agents.md"),
    Path(".github/PULL_REQUEST_TEMPLATE.md"),
)

# The rule file states all three name forms, so an author can pick one without
# opening another document.
NAME_FORMS = ("pr-<number>", "issue-<number>", "<YYYY-MM-DD>")


@pytest.fixture(scope="module")
def fragments() -> list[Path]:
    """Return every release-note fragment, without the file that states the rule.

    Returns:
        One path for each fragment that a change contributed.
    """
    return sorted(path for path in FRAGMENT_DIR.glob("*.md") if path.name != POLICY_FILE)


class TestFragmentDirectory:
    """The directory and its rule file both exist, so an author can find the rule."""

    def test_the_directory_exists(self) -> None:
        """A missing directory means a change has nowhere to put its release note."""
        assert FRAGMENT_DIR.is_dir(), f"The directory {FRAGMENT_DIR} does not exist"

    def test_the_rule_file_exists(self) -> None:
        """An author who opens the directory reads the rule from this file."""
        policy_path = FRAGMENT_DIR / POLICY_FILE
        assert policy_path.is_file(), f"The file {policy_path} does not exist"

    def test_the_directory_holds_markdown_only(self) -> None:
        """Another file type here is not a release note, so the coordinator would miss it."""
        for path in FRAGMENT_DIR.iterdir():
            assert path.suffix == ".md", f"{path.name} is not a Markdown file"


class TestFragmentNaming:
    """Every fragment name carries a value that no second change can choose."""

    def test_every_fragment_uses_an_allowed_name(self, fragments: list[Path]) -> None:
        """A name outside the three forms can collide with the name of another change."""
        for path in fragments:
            matched = any(pattern.match(path.name) for pattern in ALLOWED_NAMES)
            assert matched, (
                f"{path.name} does not match an allowed name. Use pr-<number>.md, "
                f"issue-<number>-<slug>.md, or <YYYY-MM-DD>-<slug>.md."
            )

    def test_no_fragment_uses_a_shared_name(self, fragments: list[Path]) -> None:
        """A generic name invites a second change to edit the same file."""
        for path in fragments:
            stem = path.stem.lower()
            assert stem not in SHARED_STEMS, f"{path.name} uses the shared name {stem!r}"

    def test_every_dated_fragment_names_a_real_date(self, fragments: list[Path]) -> None:
        """A date that no calendar holds cannot order the release notes."""
        for path in fragments:
            match = DATE_NAME.match(path.name)
            if match is None:
                continue  # The name uses the pull request form or the issue form.
            year, month, day = (int(part) for part in match.group(1).split("-"))
            date(year, month, day)  # A value outside the calendar raises ValueError.


class TestFragmentContent:
    """Every fragment states a change type and an observable effect."""

    def test_no_fragment_is_empty(self, fragments: list[Path]) -> None:
        """An empty fragment adds a file to the release and tells the reader nothing."""
        for path in fragments:
            assert path.read_text(encoding="utf-8").strip(), f"{path.name} holds no text"

    def test_every_fragment_states_a_change_type(self, fragments: list[Path]) -> None:
        """The coordinator groups the merged entries by this word."""
        for path in fragments:
            text = path.read_text(encoding="utf-8")
            found = [word for word in CHANGE_TYPES if word in text]
            assert found, f"{path.name} names no change type. Use one of {', '.join(CHANGE_TYPES)}."

    def test_every_fragment_holds_a_heading_and_a_bullet(self, fragments: list[Path]) -> None:
        """The heading names the change, and the bullet states the observable effect."""
        for path in fragments:
            lines = path.read_text(encoding="utf-8").splitlines()
            assert any(line.startswith("#") for line in lines), f"{path.name} holds no heading"
            assert any(line.lstrip().startswith("- ") for line in lines), f"{path.name} holds no bullet"

    def test_no_fragment_carries_a_version_stamp(self, fragments: list[Path]) -> None:
        """The release coordinator writes the version, because that stamp belongs to the release."""
        stamp = re.compile(r"^#+\s*(?:\[?version\s*)?\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}", re.IGNORECASE)
        for path in fragments:
            for line in path.read_text(encoding="utf-8").splitlines():
                assert not stamp.match(line.strip()), f"{path.name} carries the version heading {line.strip()!r}"


class TestPolicyStaysStated:
    """A rewrite of an instruction file cannot drop the rule in silence."""

    def test_each_guidance_file_names_the_fragment_directory(self) -> None:
        """An agent reads these files. A file that loses the rule sends the agent to CHANGELOG.md."""
        for relative_path in GUIDANCE_FILES:
            path = REPOSITORY_ROOT / relative_path
            assert path.is_file(), f"The guidance file {relative_path} does not exist"
            text = path.read_text(encoding="utf-8")
            assert "changelog.d" in text, f"{relative_path} no longer names the changelog.d directory"

    def test_the_rule_file_states_every_name_form(self) -> None:
        """An author picks a name from this file, so a dropped form sends the author elsewhere."""
        text = (FRAGMENT_DIR / POLICY_FILE).read_text(encoding="utf-8")
        for form in NAME_FORMS:
            assert form in text, f"{POLICY_FILE} no longer states the name form {form}"

    def test_the_changelog_warns_against_a_feature_branch_edit(self) -> None:
        """The warning is the last stop for an author who opens the shared file directly."""
        text = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "changelog.d" in text, "CHANGELOG.md no longer points an author at changelog.d"
