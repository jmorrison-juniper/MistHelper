"""Convert downloaded PDF reference material into Markdown for later search.

This is a one-off reference-gathering utility, not part of the application or of
any CI gate. It needs one package that no requirements file declares:

    python -m pip install pypdf
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pypdf import PdfReader


class PdfMarkdownConverter:
    """Extract the text of one PDF and write it as a Markdown reference."""

    def __init__(self, source_path: Path, output_path: Path) -> None:
        """Store the source PDF path and the Markdown path to write."""
        self.source_path = source_path  # PDF that the crawl downloaded
        self.output_path = output_path  # Markdown file that an agent greps later

    def convert(self) -> int:
        """Write the Markdown file and return the page count."""
        logging.info("Reading PDF %s", self.source_path)  # Announce the read before it starts
        pages = self._read_pages()  # Pull the text of every page into memory
        logging.debug("Extracted %d pages", len(pages))  # Record how much text the read produced
        logging.info("Writing Markdown %s", self.output_path)  # Announce the write before it starts
        self.output_path.write_text(self._render(pages), encoding="utf-8")  # One atomic write
        logging.debug("Wrote %d bytes", self.output_path.stat().st_size)  # Record the written size
        return len(pages)  # The caller prints this count for the operator

    def _read_pages(self) -> list[str]:
        """Return the extracted text of each page in document order."""
        reader = PdfReader(str(self.source_path))  # pypdf accepts a str path on Windows
        return [page.extract_text() or "" for page in reader.pages]  # Empty text keeps image-only pages in order

    def _render(self, pages: list[str]) -> str:
        """Join the page text into one Markdown document with a heading per page."""
        title = f"# {self.source_path.stem}\n"  # Name the document so search results carry context
        origin = f"\nSource file: `{self.source_path.name}`\n"  # Let a reader trace text back to the PDF
        sections = [f"\n## Page {number}\n\n{text.strip()}\n" for number, text in enumerate(pages, start=1)]
        return title + origin + "".join(sections)  # Build the whole file before writing it


class PdfMarkdownCommand:
    """Parse the command line and convert each PDF that the operator names."""

    def run(self, argv: list[str] | None = None) -> int:
        """Convert every PDF passed on the command line and return the exit code."""
        arguments = self._parse(argv)  # Read the PDF paths the operator supplied
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")  # ASCII-only console output
        for source in arguments.pdf:  # Convert a whole batch in one invocation
            source_path = Path(source)  # pathlib keeps the path Windows-safe
            output_path = source_path.with_suffix(".md")  # The Markdown file sits beside its PDF
            pages = PdfMarkdownConverter(source_path, output_path).convert()  # Do the extraction
            logging.info("Converted %s (%d pages)", source_path.name, pages)  # Report the per-file result
        return 0  # A zero exit code tells the shell the batch succeeded

    def _parse(self, argv: list[str] | None) -> argparse.Namespace:
        """Return the parsed command-line arguments."""
        parser = argparse.ArgumentParser(description="Convert PDF reference material to Markdown.")
        parser.add_argument("pdf", nargs="+", help="One or more PDF files to convert.")  # Accept a batch
        return parser.parse_args(argv)  # argparse exits by itself on a bad argument


if __name__ == "__main__":
    raise SystemExit(PdfMarkdownCommand().run())  # Entry point for `python scripts/pdf_to_markdown.py`
