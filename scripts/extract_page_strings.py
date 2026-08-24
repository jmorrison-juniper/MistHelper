"""Extract the visible page strings of the portal templates for the T228 audit.

Why:
    ``tools/ste_linter`` grades a Markdown file and a Python file. Every page
    string of this portal lives in a Jinja template, so the linter never read
    one. T228 asks for an audit of those strings. This script turns the visible
    text of each template into one Markdown file, which the linter then grades
    with the same rules that every other document meets.

    The script removes what an operator never reads: the Jinja statements, the
    Jinja comments, the script bodies, the style bodies, and the tags. It keeps
    the sentences, and it keeps the attribute text that a reader does see, which
    is the placeholder, the title, and the aria-label.
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

TEMPLATE_ROOT = pathlib.Path("src/upgrade_portal/app/assets/templates")
OUTPUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "page-strings.md")

# WHY: A Jinja comment, a Jinja statement, and a Jinja expression are all author
# text that no operator reads. The script drops all three before it reads tags.
JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)
JINJA_STATEMENT = re.compile(r"\{%.*?%\}", re.DOTALL)
JINJA_EXPRESSION = re.compile(r"\{\{.*?\}\}", re.DOTALL)

# WHY: A script body and a style body hold code, and the STE rules grade prose.
#
# Each end tag pattern accepts what HTML accepts after the tag name: nothing, or
# white space and then anything up to the closing angle bracket. A browser reads
# `</script>`, `</script >`, and `</script foo="bar">` as the same end tag. A
# pattern that demanded `</script>` exactly would stop at the first of the other
# two forms and keep the code that follows it as prose. CodeQL reports that gap
# as `py/bad-tag-filter`. The optional group starts with one white space
# character, so `</scriptfoo>` still does not match.
SCRIPT_BODY = re.compile(r"<script\b.*?</script(?:\s[^>]*)?>", re.DOTALL | re.IGNORECASE)
STYLE_BODY = re.compile(r"<style\b.*?</style(?:\s[^>]*)?>", re.DOTALL | re.IGNORECASE)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# WHY: These three attributes carry text that reaches a reader or a screen
# reader. Every other attribute carries a name, a path, or a class.
READABLE_ATTRIBUTE = re.compile(r"\b(?:placeholder|title|aria-label)\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
ANY_TAG = re.compile(r"<[^>]+>", re.DOTALL)

# WHY: A template wraps one sentence over several source lines. A split on the
# source line would cut that sentence in half and grade two fragments. The
# sentinel marks the tag boundary alone, which is where a text node truly ends.
_NODE_BREAK = "\x00"


def _visible_text(source: str) -> list[str]:
    """Return every visible sentence of one template.

    Args:
        source: The whole template text.

    Returns:
        One entry for each non-empty line of visible text.
    """
    kept = READABLE_ATTRIBUTE.findall(source)  # The attribute text a reader does see.
    body = source
    for pattern in (JINJA_COMMENT, HTML_COMMENT, SCRIPT_BODY, STYLE_BODY, JINJA_STATEMENT, JINJA_EXPRESSION):
        body = pattern.sub(" ", body)  # Remove the author text and the code.
    body = ANY_TAG.sub(_NODE_BREAK, body)  # A tag boundary ends a text node, so each string stands alone.
    body = html.unescape(body)  # A reader sees the character, never the entity.
    nodes = body.split(_NODE_BREAK)  # One entry for each text node, wrapping included.
    lines = [" ".join(node.split()) for node in nodes]  # Collapse the wrap and the indent of each node.
    return [line for line in [*kept, *lines] if line]


def main() -> int:
    """Write one Markdown file that holds the visible strings of every template.

    Returns:
        Zero when the extraction wrote a file, and one when it found no template.
    """
    templates = sorted(TEMPLATE_ROOT.rglob("*.html"))
    if not templates:
        print(f"No template sits under {TEMPLATE_ROOT}.")
        return 1
    parts = ["# The page strings of the upgrade capture portal", ""]
    for template in templates:
        lines = _visible_text(template.read_text(encoding="utf-8"))
        if not lines:
            continue
        parts.append(f"## {template.as_posix()}")
        parts.append("")
        for line in lines:  # A blank line after each string, because a reader meets each one on its own.
            parts.append(line)
            parts.append("")
    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} from {len(templates)} templates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
