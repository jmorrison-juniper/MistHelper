"""Guardrail: every relative Markdown link points at a file that exists (issue #3442).

Why:
    The repository had no gate on Markdown links, so 87 dead links collected in
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

Source:
    Issue #3515 moved the link checker to the `markdown-link-check` command of
    misthelper-devtools. This file keeps the MistHelper scope and the OpenAPI
    placeholder check, which only MistHelper needs.
"""

from __future__ import annotations

import re
from pathlib import Path

from misthelper_devtools.markdown_link_check import MarkdownLinkChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

# A wiki page links to a bare page name. That name resolves on the published
# wiki, never in the repository file view, so this tree stays out of scope.
EXEMPT_GLOBS = ("documentation/wiki/**",)

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
OPENAPI_PLACEHOLDER = re.compile(r"\[[^\]]*\]\(\$[a-z]/[^)]+\)")


def _checker() -> MarkdownLinkChecker:
    """Return the shared link checker with the MistHelper scope."""
    return MarkdownLinkChecker(REPOSITORY_ROOT, EXEMPT_GLOBS)


def _strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code.

    A document often shows a placeholder as an example. An example is not a
    link, so the placeholder check must not report it.
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


def test_markdown_files_are_tracked_and_the_wiki_is_exempt() -> None:
    """The checker reads real files, and it skips the wiki tree only."""
    relative = [path.relative_to(REPOSITORY_ROOT).as_posix() for path in _checker().tracked_markdown_files()]
    assert "README.md" in relative, "git ls-files returned no README.md"
    assert any(name.startswith("documentation/") for name in relative), "no documentation page was scanned"
    assert not [name for name in relative if name.startswith("documentation/wiki/")]


def test_no_broken_relative_markdown_links() -> None:
    """Every relative link resolves to a file and, when given, to an anchor."""
    failures = [failure.report_line() for failure in _checker().broken_links()]
    listing = "\n".join(f"  {item}" for item in sorted(failures))
    assert not failures, (
        f"{len(failures)} broken Markdown link(s):\n{listing}\n\n"
        "Point the link at a file that exists, or remove the link and keep "
        "the text."
    )


def test_no_openapi_crossref_placeholders() -> None:
    """No page ships a `$e` or `$h` placeholder as a link.

    `scripts/generate_api_docs.py` resolves these to a real page. A placeholder
    in the tree means the resolver did not run, or someone pasted one by hand.
    """
    failures: list[str] = []
    for path in _checker().tracked_markdown_files():
        try:
            body = _strip_code(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if OPENAPI_PLACEHOLDER.search(body):
            failures.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    assert not failures, "Unresolved OpenAPI cross-reference placeholder in:\n" + "\n".join(
        f"  {item}" for item in sorted(failures)
    )
