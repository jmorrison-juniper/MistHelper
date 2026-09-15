"""Download Session Smart Router documentation pages and store them as Markdown.

This is a one-off reference-gathering utility, not part of the application or of
any CI gate. It needs one package that no requirements file declares:

    python -m pip install html2text
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import html2text
import requests

BASE_URL = "https://docs.128technology.com/docs/"
ARTICLE_PATTERN = re.compile(r"<article\b.*</article>", re.DOTALL)


class SsrDocumentPage:
    """Download one documentation page and write it as a Markdown reference."""

    def __init__(self, slug: str, output_dir: Path) -> None:
        """Store the page slug and the directory that receives the Markdown file."""
        self.slug = slug  # Page identifier in the SSN documentation URL
        self.output_path = output_dir / f"{slug}.md"  # Markdown file to write

    def fetch(self) -> int:
        """Download the page, convert it, and return the byte count written."""
        logging.info("Downloading SSR page %s", self.slug)  # Announce the network call
        html = self._download()  # Retrieve the rendered page
        logging.debug("Received %d bytes of HTML", len(html))  # Record the response size
        logging.info("Converting page %s to Markdown", self.slug)  # Announce the transform
        self.output_path.write_text(self._convert(html), encoding="utf-8")  # One atomic write
        written = self.output_path.stat().st_size  # Measure the stored reference
        logging.debug("Wrote %d bytes to %s", written, self.output_path)  # Record the result
        return written  # The caller reports this size to the operator

    def _download(self) -> str:
        """Return the raw HTML of the documentation page."""
        response = requests.get(f"{BASE_URL}{self.slug}", timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()  # A failed download must stop the run, not write junk
        return response.text

    def _convert(self, html: str) -> str:
        """Return the Markdown form of the page body."""
        match = ARTICLE_PATTERN.search(html)  # Docusaurus wraps the body in <article>
        body = match.group(0) if match else html  # Fall back to the whole page if absent
        converter = html2text.HTML2Text()  # Fresh converter avoids shared state
        converter.body_width = 0  # Keep the original line breaks so tables stay readable
        converter.ignore_images = True  # Screenshots add no value to a text reference
        return f"# {self.slug}\n\nSource: {BASE_URL}{self.slug}\n\n{converter.handle(body)}"


class SsrDocumentSet:
    """Fetch every SSR page that the NOC runbook work needs."""

    SLUGS = (
        "cli_reference",
        "cli_stats_reference",
        "ts_applications",
        "events_alarms",
        "concepts_pcli",
    )

    def __init__(self, output_dir: Path) -> None:
        """Store the directory that receives every Markdown reference."""
        self.output_dir = output_dir  # Destination folder for the whole set

    def run(self) -> int:
        """Fetch every page and return the count of files written."""
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
        self.output_dir.mkdir(parents=True, exist_ok=True)  # Create the folder on first run
        for slug in self.SLUGS:  # Fetch the pages one at a time to stay polite to the server
            written = SsrDocumentPage(slug, self.output_dir).fetch()  # Do the work
            logging.info("Saved %s.md (%d bytes)", slug, written)  # Report each file
        return len(self.SLUGS)  # Total count for the final summary


if __name__ == "__main__":
    COUNT = SsrDocumentSet(Path("documentation") / "references" / "ssr").run()
    logging.info("Saved %d SSR reference pages", COUNT)  # Final summary for the operator
