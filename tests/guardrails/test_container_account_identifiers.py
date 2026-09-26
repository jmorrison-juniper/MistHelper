"""Guardrail: the documented container account identifier stays true (issue #3465).

Why:
    The install documents tell a Linux operator to give the `data` folder to the
    container account by number. `Containerfile` created that account with
    `useradd -r`, which lets the base image pick the number. The number moved
    from 999 to 994 when the base image changed, and nothing held the documents
    to the new value. An operator who followed the document then gave the folder
    to an account that does not exist in the image, which produces the very
    permission error that the document claims to correct.

    These tests read `Containerfile` for the pinned number, then fail when a
    document names a different one.
"""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTAINERFILE_PATH = REPOSITORY_ROOT / "Containerfile"
DOCKERFILE_PATH = REPOSITORY_ROOT / "Dockerfile"

# Every document that names the container account number for an operator.
DOCUMENTS_THAT_NAME_THE_ACCOUNT = (
    Path("README.md"),
    Path("documentation") / "container-deployment.md",
    Path("documentation") / "wiki" / "Container-Setup.md",
)

# `useradd -u <number>` and `groupadd -g <number>` hold the pinned identifiers.
USER_IDENTIFIER_PATTERN = re.compile(r"useradd\s+(?:[^\r\n]*?\s)?-u\s+(\d+)")
GROUP_IDENTIFIER_PATTERN = re.compile(r"groupadd\s+(?:[^\r\n]*?\s)?-g\s+(\d+)")

# An ownership command that an operator copies, such as
# `podman unshare chown -R 1000:1000 data`.
OWNERSHIP_PATTERN = re.compile(r"chown\s+-R\s+(\d+):(\d+)\s")


def read_pinned_user_identifier() -> str:
    """Return the numeric user identifier that `Containerfile` pins."""
    match = USER_IDENTIFIER_PATTERN.search(CONTAINERFILE_PATH.read_text(encoding="utf-8"))
    assert match is not None, "Containerfile must pin the account with `useradd -u <number>` (issue #3465)."
    return match.group(1)


def read_pinned_group_identifier() -> str:
    """Return the numeric group identifier that `Containerfile` pins."""
    match = GROUP_IDENTIFIER_PATTERN.search(CONTAINERFILE_PATH.read_text(encoding="utf-8"))
    assert match is not None, "Containerfile must pin the group with `groupadd -g <number>` (issue #3465)."
    return match.group(1)


class TestContainerfilePinsTheAccount:
    """`Containerfile` states the account number instead of accepting a default."""

    def test_containerfile_pins_the_user_identifier(self) -> None:
        """The build file names the user identifier."""
        assert read_pinned_user_identifier() == "1000"

    def test_containerfile_pins_the_group_identifier(self) -> None:
        """The build file names the group identifier."""
        assert read_pinned_group_identifier() == "1000"

    def test_dockerfile_holds_the_same_bytes(self) -> None:
        """The Docker copy carries the same pinned account."""
        assert DOCKERFILE_PATH.read_bytes() == CONTAINERFILE_PATH.read_bytes()


class TestDocumentsNameThePinnedAccount:
    """Every operator document names the number that the image holds."""

    def test_no_document_names_a_different_ownership_target(self) -> None:
        """An ownership command names the pinned identifiers only."""
        expected = (read_pinned_user_identifier(), read_pinned_group_identifier())
        found: list[str] = []  # Collect each command that names the wrong account.
        for relative_path in DOCUMENTS_THAT_NAME_THE_ACCOUNT:
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            for owner, group in OWNERSHIP_PATTERN.findall(text):
                if (owner, group) != expected:
                    found.append(f"{relative_path.as_posix()} names {owner}:{group}")
        assert found == [], f"A document names an account that the image does not hold: {found}"

    def test_every_document_names_the_pinned_identifier(self) -> None:
        """Each document states the number, so a reader can confirm it."""
        expected = read_pinned_user_identifier()
        missing = [
            relative_path.as_posix()
            for relative_path in DOCUMENTS_THAT_NAME_THE_ACCOUNT
            if f"UID {expected}" not in (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        ]
        assert missing == [], f"A document does not name the pinned account number: {missing}"
