"""Markdown helpers: the link style of each page set and the text of a table cell."""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import re  # Replaces the characters that break a table cell.
from dataclasses import dataclass  # Holds one link style as an immutable value.

REPOSITORY_URL = "https://github.com/jmorrison-juniper/MistHelper/blob/main/"  # The source link base of the wiki.
MAX_HANDLER_LENGTH = 160  # A longer handler text is cut, so the page stays readable.
EVIDENCE_LABELS = {  # The page label of each evidence kind.
    "call": "Call",
    "reference": "Reference",
    "name": "Name",
    "curated": "Curated",
    "path": "Path",
    "channel": "Channel",
}
CATEGORY_ORDER = (  # The page order of the categories, from the most used category to the least used one.
    "safe",
    "interactive_safe",
    "destructive",
    "interactive",
    "websocket",
    "resource_intensive",
    "continuous_loop",
    "unregistered",
)


@dataclass(frozen=True)
class LinkStyle:
    """The link rules of one page set: the documentation folder or the wiki."""

    source_prefix: str  # The prefix of a link to a source file.
    wiki: bool  # True for the wiki page set, which links to other pages by page name.

    def source(self, relative: str) -> str:
        """Return the link to one repository file, such as src/export/site_exporter.py."""
        return f"{self.source_prefix}{relative}"  # A relative link, or an absolute GitHub link.

    def index_page(self) -> str:
        """Return the link to the index page."""
        return "Menu-API-Endpoints" if self.wiki else "README.md"  # The wiki uses page names.

    def category_page(self, category: str) -> str:
        """Return the link to the page of one category."""
        if self.wiki:  # A wiki page name, such as Menu-API-Endpoints-Interactive-Safe.
            return f"Menu-API-Endpoints-{MarkdownText.title_slug(category)}"
        return f"{MarkdownText.slug(category)}.md"  # A file name, such as interactive-safe.md.

    def category_file(self, category: str) -> str:
        """Return the file name of the page of one category."""
        return f"{self.category_page(category)}.md" if self.wiki else self.category_page(category)


DOCS_STYLE = LinkStyle("../../", wiki=False)  # documentation/menu-api/ is two folders below the root.
WIKI_STYLE = LinkStyle(REPOSITORY_URL, wiki=True)  # The wiki cannot use a relative repository link.


class MarkdownText:
    """Build the text parts of a page."""

    @staticmethod
    def slug(category: str) -> str:
        """Return the file slug of a category, such as interactive-safe."""
        return category.replace("_", "-")  # A hyphen is the file name style of the documentation folder.

    @staticmethod
    def title_slug(category: str) -> str:
        """Return the wiki slug of a category, such as Interactive-Safe."""
        return "-".join(word.capitalize() for word in category.split("_"))  # The wiki page name style.

    @staticmethod
    def cell(text: str) -> str:
        """Return text that is safe in a table cell."""
        flat = " ".join(text.split())  # A line break ends a table row.
        return flat.replace("|", "\\|")  # A pipe ends a table cell.

    @staticmethod
    def code(text: str) -> str:
        """Return an inline code span that is safe in a table cell."""
        safe = MarkdownText.cell(text).replace("`", "'")  # A backtick ends the code span.
        return f"`{safe}`"  # The text inside one code span.

    @staticmethod
    def handler(text: str) -> str:
        """Return the handler text, cut to a readable length."""
        flat = " ".join(text.split())  # One line of text.
        if len(flat) <= MAX_HANDLER_LENGTH:  # A short handler stays whole.
            return flat
        return flat[: MAX_HANDLER_LENGTH - 3].rstrip() + "..."  # Show that the text continues.

    @staticmethod
    def anchor(heading: str) -> str:
        """Return the GitHub anchor of a heading."""
        lowered = heading.strip().lower()  # GitHub anchors are lowercase.
        kept = re.sub(r"[^a-z0-9 _-]", "", lowered)  # GitHub drops the punctuation.
        return kept.replace(" ", "-")  # GitHub turns each space into a hyphen.
