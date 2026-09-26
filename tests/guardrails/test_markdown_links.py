"""Guardrail: every relative Markdown link points at a file that exists (issue #3442).

Why:
    The repository has no gate on Markdown links, so 87 dead links collected in
    the tree before anyone saw them. Three causes made them:

    1. `documentation/api/**` carried `$e/<Tag>/<operationId>` placeholders
       straight from the upstream Mist OpenAPI spec. A placeholder is not a
       link, and it resolves to nothing.
    2. `documentation/diagrams/` promised PNG fallback images that no commit
       ever added.
    3. Planning records under `specs/` used the wrong relative depth, or they
       named a file that the author never created.

    Issue #3429 then broke the README wiki table the same way. These tests read
    every tracked Markdown file, follow each relative link, and fail when a
    target file or a heading anchor is absent.

Scope:
    The tests check only links inside the repository. An external URL needs the
    network, so a unit test must not follow one. `documentation/wiki/` is
    exempt, because a wiki page links to a bare page name that resolves on the
    published wiki and never in the repository file view.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

# A wiki page links to a bare page name. That name resolves on the published
# wiki, never in the repository file view, so this tree stays out of scope.
EXEMPT_DIRECTORIES = ("documentation/wiki/",)

INLINE_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REFERENCE_DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+)>?\s*$", re.MULTILINE)
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
ATX_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)
HTML_ANCHOR = re.compile(r"<a\s+[^>]*(?:name|id)=[\"']([^\"']+)[\"']", re.IGNORECASE)

# A link that leaves the repository, or that the browser handles on its own.
EXTERNAL_SCHEME = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#|mailto:)", re.IGNORECASE)


def _strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code.

    A document often shows a link as an example. An example is not a link, so
    the test must not follow it.
    """
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            lines.append("")
            continue
        lines.append("" if inside else line)
    return INLINE_CODE.sub(lambda match: " " * len(match.group(0)), "\n".join(lines))


def _heading_slug(text: str) -> str:
    """Return the anchor that GitHub makes for a heading.

    GitHub lowercases the text, drops punctuation, then turns each space into
    one hyphen. It does not collapse a run of spaces into one hyphen.
    """
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text)


def _anchors_of(path: Path) -> set[str]:
    """Return every anchor that a reader can jump to inside one file."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    seen: Counter[str] = Counter()
    names: set[str] = set()
    for heading in ATX_HEADING.findall(_strip_code(raw)):
        base = _heading_slug(heading)
        if not base:
            continue
        # GitHub adds `-1`, `-2` and so on to a repeated heading.
        index = seen[base]
        seen[base] += 1
        names.add(base if index == 0 else f"{base}-{index}")
    names.update(HTML_ANCHOR.findall(raw))
    return names


def _tracked_markdown_files() -> list[Path]:
    """Return every tracked Markdown file that the guardrail checks."""
    completed = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "ls-files", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        REPOSITORY_ROOT / name
        for name in completed.stdout.splitlines()
        if name and not name.startswith(EXEMPT_DIRECTORIES)
    ]


def _broken_links() -> list[str]:
    """Return one message for each link that points at nothing."""
    anchor_cache: dict[Path, set[str]] = {}
    failures: list[str] = []
    for path in _tracked_markdown_files():
        try:
            body = _strip_code(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        targets = INLINE_LINK.findall(body) + REFERENCE_DEFINITION.findall(body)
        for target in targets:
            if EXTERNAL_SCHEME.match(target):
                continue
            file_part, _, anchor = target.partition("#")
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
            if file_part:
                resolved = (path.parent / unquote(file_part)).resolve()
                if not resolved.exists():
                    failures.append(f"{relative} -> {target} (no such file)")
                    continue
            else:
                resolved = path
            if anchor and resolved.is_file() and resolved.suffix.lower() == ".md":
                if resolved not in anchor_cache:
                    anchor_cache[resolved] = _anchors_of(resolved)
                if unquote(anchor).lower() not in anchor_cache[resolved]:
                    failures.append(f"{relative} -> {target} (no such anchor)")
    return failures


def test_markdown_files_are_tracked() -> None:
    """The guardrail reads real files, so an empty list means it found nothing."""
    assert _tracked_markdown_files(), "git ls-files returned no Markdown file"


def test_no_broken_relative_markdown_links() -> None:
    """Every relative link resolves to a file and, when given, to an anchor."""
    failures = _broken_links()
    if failures:
        listing = "\n".join(f"  {item}" for item in sorted(failures))
        pytest.fail(
            f"{len(failures)} broken Markdown link(s):\n{listing}\n\n"
            "Point the link at a file that exists, or remove the link and keep "
            "the text."
        )


def test_no_openapi_crossref_placeholders() -> None:
    """No page ships a `$e` or `$h` placeholder as a link.

    `scripts/generate_api_docs.py` resolves these to a real page. A placeholder
    in the tree means the resolver did not run, or someone pasted one by hand.
    """
    placeholder = re.compile(r"\[[^\]]*\]\(\$[a-z]/[^)]+\)")
    failures: list[str] = []
    for path in _tracked_markdown_files():
        try:
            body = _strip_code(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if placeholder.search(body):
            failures.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    assert not failures, (
        "Unresolved OpenAPI cross-reference placeholder in:\n"
        + "\n".join(f"  {item}" for item in sorted(failures))
    )
