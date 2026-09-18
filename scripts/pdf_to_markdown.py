"""Convert a Juniper PDF reference document into Markdown for later search.

The converter reads each PDF with pdfplumber, which pyproject.toml declares. It
writes YAML front matter, then the body text. A line whose font stands above the
body font size becomes a heading. A bullet glyph becomes a Markdown list item. A
page marker closes each page, so a citation can name the source page.

The body font size is counted over every page of the document before any line is
classified. A sample of the first pages returns the front matter size, which is
smaller than the body size, and that error marks the whole document as headings.
The body size is the tallest size that carries a tenth of the characters or more.
A measured run shows why the plain modal size is not enough: a code listing at 7
points can hold more characters than the prose at 10 points.

Rebuild the corpus with:

    python scripts/pdf_to_markdown.py <downloaded.pdf> --output-root markdown

This is a reference-gathering utility. It is not part of the application, and it
reads no network resource.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from collections import Counter
from importlib import import_module
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)  # Use a module logger so tests can identify this log source.

# One drawn line of a page: the text, the modal font size, and the bold state.
TextLine = tuple[str, float, bool]
# One row of the conversion manifest: the source, the status, and the 2 counts.
ManifestRow = dict[str, str | int]


class MarkdownTextRules:
    """Hold the glyph rules, the noise rules, and the heading rule of the body."""

    GLYPHS = {
        "\ufb00": "ff",  # a ligature breaks a search for the word that holds it
        "\ufb01": "fi",  # the same rule for the fi ligature
        "\ufb02": "fl",  # the same rule for the fl ligature
        "\ufb03": "ffi",  # the same rule for the ffi ligature
        "\ufb04": "ffl",  # the same rule for the ffl ligature
        "\u2018": "'",  # a curly mark breaks a search for a quoted command
        "\u2019": "'",  # the same rule for the right single mark
        "\u201c": '"',  # the same rule for the left double mark
        "\u201d": '"',  # the same rule for the right double mark
        "\u2013": "-",  # an en dash reads as a hyphen in a command example
        "\u2014": "-",  # an em dash reads as a hyphen in a command example
        "\u00a0": " ",  # a no-break space hides a word boundary from a search
        "\ufffd": "",  # the reader writes this mark when a glyph has no mapping
    }
    BULLETS = "\u2022\u2023\u25aa\u25cf\u25e6\u2043\u00b7\uf0b7\uf0a7"  # the glyphs that start a list item
    FOLIO = re.compile(r"^(?:x{0,3}(?:ix|iv|v?i{0,3})|\d{1,4}|page\s+\d{1,4}|\d{1,4}\s+of\s+\d{1,4})$", re.IGNORECASE)
    CONTENTS = re.compile(r".+?(?:\|\s*|\.{3,}\s*)\d+(?=\s|$)")  # one contents entry, which ends in a page number

    def normalize(self, text: str) -> str:
        """Return the line with plain glyphs and with a Markdown list item mark."""
        cleaned = text  # keep the source line until every glyph rule has run
        for glyph, plain in self.GLYPHS.items():  # a ligature and a curly mark defeat a grep
            cleaned = cleaned.replace(glyph, plain)  # the plain form is what an engineer types
        cleaned = " ".join(cleaned.split())  # a PDF reader leaves runs of space between words
        if cleaned.startswith("#"):  # a body line such as "# of ports" is a heading in Markdown
            cleaned = f"\\{cleaned}"  # the escape keeps the line as body text
        if cleaned and cleaned[0] in self.BULLETS:  # a leading bullet glyph marks a list item
            return "- " + cleaned[1:].strip()  # the Markdown form of the same item
        return cleaned  # a normal body line needs no mark

    def is_noise(self, text: str, headers: frozenset[str]) -> bool:
        """Return True when the line is empty, a running header, or a folio."""
        if not text:  # an empty line carries no information into the Markdown file
            return True
        if text in headers:  # a running header repeats on every page and adds no content
            return True
        return len(text) <= 12 and bool(self.FOLIO.match(text))  # a folio holds a number alone

    def split_contents(self, text: str) -> list[str]:
        """Return one line for each contents entry that a joined run holds."""
        matches = list(self.CONTENTS.finditer(text))  # each match ends with its page number
        if len(matches) < 2:  # a body line holds 1 page number at most, so it stays whole
            return [text]  # this branch keeps the body text unchanged
        parts = [match.group(0).strip() for match in matches]  # one output line for each entry
        tail = text[matches[-1].end() :].strip()  # the text that follows the last page number
        logger.debug("Split a contents run into %d entries", len(parts))  # record the split
        return parts + [tail] if tail else parts  # the tail is a contents entry without a number

    def repeated_headers(self, pages: list[list[TextLine]]) -> frozenset[str]:
        """Return the text of each line that repeats at the top or the bottom of a page."""
        if len(pages) < 3:  # a short document cannot prove that a line repeats
            return frozenset()
        edges: Counter[str] = Counter()  # count the first line and the last line of each page
        for lines in pages:  # the running header sits at one of the two page edges
            texts = [text.strip() for text, _size, _bold in lines if text.strip()]
            edges.update(set(texts[:1] + texts[-1:]))  # the set stops a 1 line page counting twice
        limit = max(3, len(pages) // 2)  # a header must cover half of the pages to qualify
        return frozenset(text for text, count in edges.items() if count >= limit)

    def heading(self, text: str, size: float, bold: bool, body_size: float) -> str:
        """Return the line with its Markdown heading mark, from the font size."""
        if text.startswith("- ") or len(text) > 100:  # a list item and a long run are body text
            return text
        if self.CONTENTS.fullmatch(text):  # a contents entry points at a page, so it is not a heading
            return text
        if size >= body_size * 1.4:  # a title stands far above the body size
            return f"## {text}"
        if size >= body_size * 1.15:  # a section heading stands above the body size
            return f"### {text}"
        if size > body_size + 0.25 or (bold and size >= body_size and len(text) <= 80):  # a subheading
            return f"#### {text}"
        return text  # every other line is body text

    def cap_headings(self, lines: list[str]) -> list[str]:
        """Return the lines with each weak heading demoted, when the heading share is too high."""
        solid = [line for line in lines if line.strip()]  # a blank line joins 2 paragraphs
        heads = [line for line in solid if line.startswith("#")]  # every heading of the document
        if not solid or len(heads) <= 0.25 * len(solid):  # the measured ceiling of research Decision 15
            return lines
        logger.debug("Demoting the weak headings of a document at %d of %d", len(heads), len(solid))
        return [line[5:] if line.startswith("#### ") else line for line in lines]  # the weakest signal


class PdfLineReader:
    """Read one PDF and return its lines with the measured body font size."""

    def __init__(self, source_path: Path) -> None:
        """Store the path of the PDF file that this reader opens."""
        self.source_path = source_path  # the reader opens this file once

    def read_document(self) -> tuple[dict[str, str], list[list[TextLine]], float]:
        """Return the metadata, the lines of each page, and the body font size."""
        logger.info("Reading PDF %s", self.source_path)  # announce the read before it starts
        logger.info("Loading the PDF reader for %s", self.source_path)  # defer the heavy import until conversion
        pdfplumber: Any = import_module("pdfplumber")  # load the optional converter dependency only when used
        logger.debug("Loaded the PDF reader for %s", self.source_path)  # record that conversion can start
        sizes: Counter[float] = Counter()  # the size count of every character of every page
        pages: list[list[TextLine]] = []  # one entry for each page, in document order
        with pdfplumber.open(str(self.source_path)) as document:  # pdfplumber closes the file
            metadata = {str(key): str(value) for key, value in document.metadata.items()}
            for page in document.pages:  # every page feeds the size count, because a sample lies
                pages.append(self._page_lines(page, sizes))
                page.flush_cache()  # release the character cache, so a 1,000 page guide fits
        body_size = self._body_size(sizes)  # the count of the whole document gives this value
        logger.debug("Read %d pages, body size %s", len(pages), body_size)  # record the result
        return metadata, pages, body_size

    def _body_size(self, sizes: Counter[float]) -> float:
        """Return the tallest font size that carries a tenth of the characters or more."""
        if not sizes:  # a PDF that holds an image only gives no character
            return 0.0
        floor = 0.10 * sum(sizes.values())  # a size below this share describes a note, not the body
        common = [size for size, count in sizes.items() if count >= floor]  # the sizes of the text
        logger.debug("Measured %d common sizes from %d distinct sizes", len(common), len(sizes))
        return max(common) if common else sizes.most_common(1)[0][0]  # the modal size is the fallback

    X_TOLERANCE = 1.0  # the space width that pdfplumber assumes between 2 words

    def _page_lines(self, page: Any, sizes: Counter[float]) -> list[TextLine]:
        """Return the drawn lines of one page and add their sizes to the count."""
        lines: list[TextLine] = []  # the lines of this page, in reading order
        # The pdfplumber default of 3 points merges adjacent words in a Juniper
        # PDF, so "set class" becomes "setclass". Issue #2946 holds the evidence.
        for raw in page.extract_text_lines(x_tolerance=self.X_TOLERANCE):
            chars = raw["chars"]  # each line carries its characters, so a per line size exists
            sizes.update(round(float(char["size"]), 1) for char in chars)  # feed the size count
            lines.append(self._line_style(str(raw["text"]), chars))
        return lines

    def _line_style(self, text: str, chars: list[dict[str, Any]]) -> TextLine:
        """Return the text of one line with its modal font size and its bold state."""
        counted = Counter(round(float(char["size"]), 1) for char in chars)  # the sizes of this line
        fonts = Counter(str(char["fontname"]) for char in chars)  # the fonts of this line
        size = counted.most_common(1)[0][0] if counted else 0.0  # the modal size describes the line
        bold = "bold" in fonts.most_common(1)[0][0].lower() if fonts else False  # Lato-Bold is bold
        return text.strip(), size, bold

    def measure(self) -> tuple[dict[str, str], int, float]:
        """Return the metadata, the page count, and the body size, holding no page.

        A whole document read keeps every page until the end, so an 81 MB guide
        reaches more than 20 GB. This pass keeps only a size counter, so memory
        stays flat. It still reads every page, so the body size never comes from
        a sample.
        """
        logger.info("Measuring the body size of %s", self.source_path)  # announce the first pass
        pdfplumber: Any = import_module("pdfplumber")  # load the optional dependency only when used
        sizes: Counter[float] = Counter()  # the size count of every character of every page
        with pdfplumber.open(str(self.source_path)) as document:  # pdfplumber closes the file
            metadata = {str(key): str(value) for key, value in document.metadata.items()}
            total = len(document.pages)  # the part writer needs the count before it splits
            for index in range(total):  # every page feeds the count, because a sample lies
                page = document.pages[index]
                for char in page.chars:  # the character size decides the body size
                    if str(char.get("text", "")).strip():
                        sizes[round(float(char["size"]), 1)] += 1
                page.flush_cache()  # release the page, so the reader does not grow
        body_size = self._body_size(sizes)  # the count of the whole document gives this value
        logger.debug("Measured %d pages, body size %s", total, body_size)  # record the result
        return metadata, total, body_size

    def read_range(self, start: int, stop: int) -> list[list[TextLine]]:
        """Return the lines of one page range, then release every page it read."""
        logger.info("Reading pages %d to %d of %s", start + 1, stop, self.source_path)
        pdfplumber: Any = import_module("pdfplumber")  # load the optional dependency only when used
        unused: Counter[float] = Counter()  # the size count already came from the first pass
        pages: list[list[TextLine]] = []  # only this range lives in memory
        with pdfplumber.open(str(self.source_path)) as document:  # pdfplumber closes the file
            for index in range(start, stop):
                page = document.pages[index]
                pages.append(self._page_lines(page, unused))
                page.flush_cache()  # release the page inside the range
        logger.debug("Read %d pages of the range", len(pages))  # record the size of the range
        return pages


class PdfMarkdownConverter:
    """Extract the text of one PDF and write it as a Markdown reference."""

    RULES = MarkdownTextRules()  # the rules hold no state, so one instance serves every document
    FIELDS = {
        "Title": "title",  # the staged corpus writes the title first, after the source file
        "Author": "author",  # 68.0 percent of the staged files hold an author
        "Subject": "subject",  # 11.2 percent of the staged files hold a subject
        "CreationDate": "creationDate",  # 98.8 percent of the staged files hold this date
        "ModDate": "modDate",  # 98.5 percent of the staged files hold this date
    }

    def __init__(self, source_path: Path, output_path: Path, source_root: Path | None = None) -> None:
        """Store the source path, the Markdown path, and the root of the citation."""
        self.source_path = source_path  # the PDF that the corpus holds
        self.output_path = output_path  # the Markdown file that an agent greps later
        self.source_root = source_root  # the source_file field is relative to this root

    def convert(self) -> ManifestRow:
        """Write the Markdown file and return one manifest row."""
        logger.info("Converting PDF %s", self.source_path)  # announce the work before it starts
        metadata, pages, body_size = PdfLineReader(self.source_path).read_document()
        headers = self.RULES.repeated_headers(pages)  # find the running header before rendering
        rendered = [self._render_page(lines, number, body_size, headers) for number, lines in enumerate(pages, 1)]
        capped = self.RULES.cap_headings("".join(rendered).splitlines())  # hold the heading share
        body = "\n".join(capped) + "\n"  # each page already ends with its own blank line
        flat = not any(line.startswith("#") for line in capped)  # one font size gives no heading
        body = f"## {body}" if flat and not body.startswith("<!--") else body  # FR-028 needs 1 heading
        text = self._front_matter(metadata, len(pages)) + body  # the front matter opens the file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)  # the output tree mirrors the source
        self.output_path.write_text(text, encoding="utf-8")  # one atomic write for each document
        logger.debug("Wrote %d characters to %s", len(text), self.output_path)  # record the size
        return self._row(len(pages), len(body))

    def _render_page(self, lines: list[TextLine], number: int, body_size: float, headers: frozenset[str]) -> str:
        """Return the Markdown text of one page, which ends with its page marker."""
        allowance = 6 if number == 1 else len(lines)  # FR-028 caps the cover page at 6 headings
        out: list[str] = []  # the kept lines of this page, in reading order
        for text, size, bold in lines:  # one drawn line gives one output line at most
            parts = self.RULES.split_contents(text)  # a joined contents run gives many lines
            for part in parts:  # each part carries the font of the line that held it
                clean = self.RULES.normalize(part)  # apply the glyph rules before any test
                if self.RULES.is_noise(clean, headers):  # a folio and a running header leave here
                    continue
                marked = clean if len(parts) > 1 else self.RULES.heading(clean, size, bold, body_size)
                marked = clean if marked.startswith("#") and allowance <= 0 else marked  # the cap
                allowance -= 1 if marked.startswith("#") else 0  # count the headings of this page
                level = marked.split(" ")[0] if marked.startswith("#") else ""  # the heading level
                divided = bool(level) and bool(out) and out[-1].startswith(f"{level} ") and len(out[-1]) < 40
                if number == 1 and divided:  # FR-029 joins a cover title that a line break divides
                    out[-1] = f"{out[-1]} {marked[len(level) + 1 :]}"
                    continue
                out.append(marked)
        out.append(f"<!-- page {number} -->")  # the marker lets a citation name the source page
        return "\n\n".join(out) + "\n\n"  # the staged corpus separates each line with a blank line

    def _front_matter(self, metadata: dict[str, str], pages: int) -> str:
        """Return the YAML front matter, which holds 2 fields always and 5 when they exist."""
        source = self._relative_source()  # the citation names a path below the corpus root
        fields = [f'source_file: "{source}"']  # this field appears in 100 percent of the files
        for key, name in self.FIELDS.items():  # a PDF without an author gives no author field
            raw = " ".join(metadata.get(key, "").split())  # a metadata value can hold a newline
            value = self.RULES.normalize(raw) if raw else ""  # the body rules also clean a title
            fields += [f'{name}: "{value.replace(chr(34), chr(39))}"'] if value else []  # keep the YAML valid
        fields.append(f"pages: {pages}")  # this field appears in 100 percent of the files
        return "---\n" + "\n".join(fields) + "\n---\n\n"

    def _relative_source(self) -> str:
        """Return the source path that the front matter and the manifest cite."""
        if self.source_root is None:  # a single file run cites the file name alone
            return self.source_path.name
        return self.source_path.relative_to(self.source_root).as_posix()  # a corpus run cites the tree

    def _row(self, pages: int, chars: int) -> ManifestRow:
        """Return the manifest row of this document, with its quality status."""
        density = chars / pages if pages else 0.0  # FR-027 measures characters for each page
        status = "converted" if density >= 200 else "review"  # a thin document needs a human
        logger.debug("Document gives %.1f characters for each page", density)  # record the density
        return {"source": self._relative_source(), "status": status, "pages": pages, "chars": chars}


class PdfPartConverter(PdfMarkdownConverter):
    """Write one Markdown file for each page range of a very large PDF.

    A whole document conversion holds every page until the end. An 81 MB guide
    then reaches more than 20 GB of memory and never finishes. This converter
    reads one range at a time, so memory stays near 0.4 GB.

    The output also suits a reader better. A skill opens the range that holds
    the answer instead of loading one file of many megabytes.
    """

    def __init__(
        self, source_path: Path, output_path: Path, source_root: Path | None = None, pages_per_part: int = 250
    ) -> None:
        """Store the paths, the citation root, and the page count of each part."""
        super().__init__(source_path, output_path, source_root)
        self.pages_per_part = pages_per_part  # the page count that one part file holds

    def convert(self) -> ManifestRow:
        """Write one part for each page range and return one manifest row."""
        logger.info("Converting %s in parts of %d pages", self.source_path, self.pages_per_part)
        reader = PdfLineReader(self.source_path)
        metadata, total, body_size = reader.measure()  # the first pass holds no page
        folder = self.output_path.with_suffix("")  # the parts live in a folder named for the file
        folder.mkdir(parents=True, exist_ok=True)
        written = self._write_parts(reader, metadata, total, body_size)
        logger.debug("Wrote %d parts holding %d characters", len(written), sum(written))
        return self._row(total, sum(written))

    def _write_parts(self, reader: PdfLineReader, metadata: dict[str, str], total: int, body_size: float) -> list[int]:
        """Write each part file and return the character count of each one."""
        folder = self.output_path.with_suffix("")  # the same folder that convert made
        counts: list[int] = []  # one character count for each written part
        for number, start in enumerate(range(0, total, self.pages_per_part), start=1):
            stop = min(start + self.pages_per_part, total)
            pages = reader.read_range(start, stop)  # only this range lives in memory
            body = self._render_range(pages, start, body_size)
            head = self._part_front_matter(metadata, number, start, stop)
            target = folder / f"part-{number:03d}.md"
            target.write_text(head + body, encoding="utf-8")  # one atomic write for each part
            counts.append(len(body))
        return counts

    def _render_range(self, pages: list[list[TextLine]], start: int, body_size: float) -> str:
        """Return the Markdown of one page range, with the page numbers of the source."""
        headers = self.RULES.repeated_headers(pages)  # the running header of this range
        rendered = [
            self._render_page(lines, start + offset, body_size, headers) for offset, lines in enumerate(pages, 1)
        ]
        capped = self.RULES.cap_headings("".join(rendered).splitlines())  # hold the heading share
        return "\n".join(capped) + "\n"

    def _part_front_matter(self, metadata: dict[str, str], number: int, start: int, stop: int) -> str:
        """Return the front matter of one part, which names its range in the source."""
        base = self._front_matter(metadata, stop - start).rstrip()[: -len("---")].rstrip()
        extra = [f"part: {number}", f'page_range: "{start + 1}-{stop}"']
        return base + "\n" + "\n".join(extra) + "\n---\n\n"


class PdfMarkdownCommand:
    """Parse the command line and convert each PDF that the operator names."""

    def run(self, argv: list[str] | None = None) -> int:
        """Convert every PDF that the command line names and return the exit code."""
        arguments = self._parse(argv)  # read the paths and the options that the operator gave
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")  # ASCII output
        logger.info("Starting the conversion with %d workers", arguments.workers)  # announce the run
        started = time.monotonic()  # the manifest reports the run time for a capacity estimate
        rows = self._convert_all(arguments)  # the pool does the work
        seconds = time.monotonic() - started  # the elapsed time of the whole batch
        logger.debug("Converted %d files in %.1f seconds", len(rows), seconds)  # record the result
        if arguments.manifest:  # the corpus rebuild needs one row for each source file
            self._write_manifest(Path(arguments.manifest), rows, seconds)
        return 0 if all(row["status"] != "failed" for row in rows) else 1  # a failure fails the run

    def _parse(self, argv: list[str] | None) -> argparse.Namespace:
        """Return the parsed command line arguments."""
        parser = argparse.ArgumentParser(description="Convert PDF reference material to Markdown.")
        parser.add_argument("pdf", nargs="*", help="One or more PDF files to convert.")
        workers_help = "Worker processes. The default is the processor count."  # T017 states the default
        parser.add_argument("--workers", type=int, default=None, help=workers_help)
        parser.add_argument("--list-file", default=None, help="A text file that holds one PDF path for each line.")
        parser.add_argument("--source-root", default=None, help="The folder that the source_file field is relative to.")
        parser.add_argument("--output-root", default=None, help="The folder that receives the Markdown tree.")
        parser.add_argument("--manifest", default=None, help="The JSON file that receives one row for each source.")
        part_help = "Page count of one part file. A larger PDF writes a folder of parts."
        parser.add_argument("--pages-per-part", type=int, default=250, help=part_help)
        split_help = "Megabyte size above which a PDF writes parts instead of one file."
        parser.add_argument("--split-above-mb", type=int, default=40, help=split_help)
        arguments = parser.parse_args(argv)  # argparse exits by itself on a bad argument
        if arguments.workers is None:  # only the default path needs the host processor probe
            arguments.workers = self._default_worker_count()  # defer the processor probe to runtime
        return arguments  # the command uses the resolved worker count

    @staticmethod
    def _default_worker_count() -> int:
        """Return the worker count that the host reports for this run."""
        logger.info("Reading the processor count for the PDF converter")  # the host probe can vary by runner
        worker_count = os.cpu_count() or 1  # fall back to one worker when the platform reports no count
        logger.debug("Using %d worker processes as the default", worker_count)  # record the chosen fan-out
        return worker_count  # the parser writes this value into the arguments

    def _sources(self, arguments: argparse.Namespace) -> list[str]:
        """Return every source path, from the command line and from the list file."""
        sources = list(arguments.pdf)  # the paths that the operator typed
        if arguments.list_file:  # a corpus rebuild names 4,006 paths, which no command line carries
            listed = Path(arguments.list_file).read_text(encoding="utf-8").splitlines()
            sources += [line.strip() for line in listed if line.strip()]  # 1 path for each line
        logger.debug("Collected %d source paths", len(sources))  # record the size of the batch
        return sources

    def _convert_all(self, arguments: argparse.Namespace) -> list[ManifestRow]:
        """Convert each named PDF across the worker pool and return the manifest rows."""
        source_root = Path(arguments.source_root) if arguments.source_root else None  # citation root
        output_root = Path(arguments.output_root) if arguments.output_root else None  # output tree
        jobs = [(source, source_root, output_root) for source in self._sources(arguments)]
        split_bytes = arguments.split_above_mb * 1024 * 1024  # a larger file writes parts
        jobs = [(*job, split_bytes, arguments.pages_per_part) for job in jobs]  # carry both settings
        logger.info("Converting %d PDF files", len(jobs))  # announce the batch before it starts
        if arguments.workers <= 1:  # one worker keeps the traceback of a test in this process
            return [self.convert_one(job) for job in jobs]
        logger.info("Loading the process pool for %d workers", arguments.workers)  # defer spawn support to conversion
        from concurrent.futures import ProcessPoolExecutor  # isolate Windows spawn cost from module import

        logger.debug("Loaded the process pool for %d workers", arguments.workers)  # record that parallel work can start
        with ProcessPoolExecutor(max_workers=arguments.workers) as pool:  # a page read is CPU bound
            return list(pool.map(self.convert_one, jobs, chunksize=1))  # 1 file for each dispatch balances

    @staticmethod
    def convert_one(job: tuple[str, Path | None, Path | None, int, int]) -> ManifestRow:
        """Convert one PDF inside a worker process and return its manifest row."""
        source, source_root, output_root, split_bytes, pages_per_part = job  # one tuple for each file
        source_path = Path(source)  # pathlib keeps the path correct on Windows and on Linux
        relative = source_path.relative_to(source_root) if source_root else Path(source_path.name)
        output_path = (output_root / relative).with_suffix(".md") if output_root else source_path.with_suffix(".md")
        try:  # one damaged PDF must not stop a run of 4,006 documents
            if split_bytes and source_path.stat().st_size > split_bytes:
                # A whole document read of a large guide exhausts memory, so write parts.
                return PdfPartConverter(source_path, output_path, source_root, pages_per_part).convert()
            return PdfMarkdownConverter(source_path, output_path, source_root).convert()
        except Exception as error:  # pdfminer raises many error types for a damaged file
            logging.error("Failed to convert %s: %s", source_path, error)  # name the file and the cause
            return {"source": source, "status": "failed", "pages": 0, "chars": 0}

    def _write_manifest(self, path: Path, rows: list[ManifestRow], seconds: float) -> None:
        """Write the JSON manifest that holds one row for each source file."""
        logger.info("Writing the conversion manifest %s", path)  # announce the write
        counts: Counter[str] = Counter(str(row["status"]) for row in rows)  # the status of each row
        pages = sum(int(row["pages"]) for row in rows)  # the total page count of the run
        chars = sum(int(row["chars"]) for row in rows)  # the total character count of the run
        report = {"status_counts": dict(counts), "pages": pages, "chars": chars, "seconds": round(seconds, 1)}
        path.parent.mkdir(parents=True, exist_ok=True)  # the manifest sits beside the Markdown tree
        path.write_text(json.dumps({**report, "files": rows}, indent=1), encoding="utf-8")
        logger.debug("Manifest holds %d rows and %d pages", len(rows), pages)  # record the result


if __name__ == "__main__":
    raise SystemExit(PdfMarkdownCommand().run())  # entry point for python scripts/pdf_to_markdown.py
