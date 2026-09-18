"""Tests for the PDF to Markdown converter in scripts/pdf_to_markdown.py.

The tests build a small PDF file in a temporary folder, convert it, and measure
the Markdown output against the structural contract in check V15 of
specs/2754-hardening-junos-skill/quickstart.md.

The fixture builder writes the PDF bytes by hand. No package that writes a PDF
file is declared in this repository, and the hardening feature forbids a new
dependency.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import ClassVar

from scripts.pdf_to_markdown import (
    MarkdownTextRules,
    PdfLineReader,
    PdfMarkdownCommand,
    PdfMarkdownConverter,
    PdfPartConverter,
)  # import the converter pieces under test

logger = logging.getLogger(__name__)  # Use the module logger for fixture diagnostics.

# One drawn line of a fixture page: the text, the font size, and the bold state.
TextLine = tuple[str, float, bool]


class PdfFixtureBuilder:
    """Build a small PDF file so a test can measure the converter output."""

    def __init__(self, directory: Path) -> None:
        """Store the folder that receives each built PDF file."""
        self.directory = directory  # pytest gives one temporary folder for each test

    def build(self, name: str, pages: list[list[TextLine]], metadata: dict[str, str] | None = None) -> Path:
        """Write one PDF file with the given pages and return its path."""
        logger.info("Building PDF fixture %s", name)  # announce the write before it starts
        objects, info_number = self._objects(pages, metadata or {})  # build every PDF object body
        path = self.directory / name  # pathlib keeps the path correct on Windows and on Linux
        path.write_bytes(self._serialize(objects, info_number))  # one atomic write of the whole file
        logger.debug("Built fixture with %d bytes", path.stat().st_size)  # record the produced size
        return path  # the test converts this file

    def _objects(self, pages: list[list[TextLine]], metadata: dict[str, str]) -> tuple[list[str], int]:
        """Return the body of each PDF object and the number of the metadata object."""
        fields = " ".join(f"/{key} ({value})" for key, value in metadata.items())  # info dictionary entries
        entries = [
            "<</Type/Catalog/Pages 2 0 R>>",  # object 1, the document catalog
            "",  # object 2, the page tree, which the kid list completes below
            "<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding 5 0 R>>",  # object 3, the body font
            "<</Type/Font/Subtype/Type1/BaseFont/Helvetica-Bold/Encoding 5 0 R>>",  # object 4, the bold font
            "<</Type/Encoding/BaseEncoding/WinAnsiEncoding/Differences[1/quoteright 2/bullet]>>",  # object 5
            f"<<{fields}>>",  # object 6, the metadata that the front matter test reads
        ]
        kids: list[int] = []  # the object number of each page, for the page tree
        for lines in pages:  # one content stream and one page object for each page
            stream = self._content(lines)  # the drawing commands of this page
            entries.append(f"<</Length {len(stream)}>>\nstream\n{stream}\nendstream")  # the content object
            box = "/MediaBox[0 0 612 792]/Resources<</Font<</F1 3 0 R/F2 4 0 R>>>>"  # the frame and the fonts
            entries.append(f"<</Type/Page/Parent 2 0 R{box}/Contents {len(entries)} 0 R>>")  # the page object
            kids.append(len(entries))  # the page object number, which the page tree needs
        kid_list = " ".join(f"{kid} 0 R" for kid in kids)  # the reference list of the page tree
        entries[1] = f"<</Type/Pages/Kids[{kid_list}]/Count {len(kids)}>>"  # complete object 2
        return entries, 6  # object 6 always holds the metadata

    def _content(self, lines: list[TextLine]) -> str:
        """Return the content stream that draws each line of one page."""
        parts = ["BT"]  # begin the text object of this page
        top = 750  # the first baseline sits near the top of the page
        for text, size, bold in lines:  # draw each line below the line above it
            escaped = text.replace("\\", "\\\\").replace("(", r"\(").replace(")", r"\)")  # PDF string escapes
            escaped = escaped.replace("\u2019", "\\001").replace("\u2022", "\\002")  # the two mapped glyphs
            parts.append(f"1 0 0 1 72 {top} Tm /{'F2' if bold else 'F1'} {size} Tf ({escaped}) Tj")  # draw it
            top -= int(size) + 6  # leave a gap so each line keeps its own row
        parts.append("ET")  # end the text object
        return "\n".join(parts)  # the reader needs one stream for each page

    def _serialize(self, objects: list[str], info_number: int) -> bytes:
        """Return the whole PDF file, with a correct cross reference table."""
        out = bytearray(b"%PDF-1.4\n")  # the header that every reader expects
        offsets: list[int] = []  # the byte offset of each object, for the cross reference table
        for number, body in enumerate(objects, start=1):  # PDF object numbers start at 1
            offsets.append(len(out))  # record the offset before the object body
            out += f"{number} 0 obj\n{body}\nendobj\n".encode("latin-1")  # PDF syntax is byte oriented
        start = len(out)  # the trailer points the reader at the cross reference table
        out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1") + b"0000000000 65535 f \n"  # the free entry
        for offset in offsets:  # one fixed width entry for each object
            out += f"{offset:010d} 00000 n \n".encode("latin-1")  # the format is exactly 20 bytes
        tail = f"trailer\n<</Size {len(objects) + 1}/Root 1 0 R/Info {info_number} 0 R>>"  # the file trailer
        out += f"{tail}\nstartxref\n{start}\n%%EOF\n".encode("latin-1")  # the reader starts at this offset
        return bytes(out)  # the builder writes these bytes to disk


class TestOutputContract:
    """Measure the converter output against the 5 rows of check V15."""

    METADATA: ClassVar[dict[str, str]] = {
        "Title": "Junos Device Hardening Guide",  # the front matter title field
        "Author": "Juniper Networks, Inc.",  # the front matter author field
        "Subject": "Protect the management plane of a Junos device.",  # the front matter subject field
        "CreationDate": "D:20260916120000-07'00'",  # the front matter creationDate field
        "ModDate": "D:20260916120000-07'00'",  # the front matter modDate field
    }
    GUIDE: ClassVar[list[list[TextLine]]] = [
        [
            ("Junos Device Hardening Guide", 18.0, False),  # the cover title, above the body size
            ("Published 2026-09-16", 12.0, False),  # the cover date, above the body size
            ("This guide explains how an operator protects the management plane of a Junos device.", 10.0, False),
            ("The guide covers the console port, the user accounts, and the authentication services.", 10.0, False),
            ("The guide also covers the log files and the time service of each platform.", 10.0, False),
        ],
        [
            ("Protect the management plane", 14.0, False),  # a section heading, above the body size
            ("Set a filter on the loopback interface, because that filter protects the routing engine.", 10.0, False),
            ("\u2022 Apply the filter to the input of the loopback interface.", 10.0, False),  # a bullet glyph
            ("The operator\u2019s account needs a class that holds the correct permissions.", 10.0, False),
            ("Confirm the state of the device with a show command after each change.", 10.0, False),
        ],
        [
            ("Read the log files", 14.0, True),  # a bold section heading, above the body size
            ("Send each log message to a remote host, because local storage holds a small file only.", 10.0, False),
            ("A remote host keeps the evidence when an attacker clears the local file.", 10.0, False),
            ("Set the time service, because a log message without a correct time proves little.", 10.0, False),
            ("2", 10.0, False),  # a folio line, which the output must not hold
        ],
    ]

    def _convert(self, tmp_path: Path) -> str:
        """Build the sample guide, convert it, and return the Markdown text."""
        source = PdfFixtureBuilder(tmp_path).build("guide.pdf", self.GUIDE, self.METADATA)  # the fixture PDF
        output = tmp_path / "guide.md"  # the converter writes beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        return output.read_text(encoding="utf-8")  # every assertion reads this text

    def test_front_matter_holds_required_fields(self, tmp_path: Path) -> None:
        """The front matter holds the 2 required fields and the 5 metadata fields."""
        text = self._convert(tmp_path)  # convert the sample guide
        assert text.startswith("---\n"), "the file must open with YAML front matter"  # row 1 of check V15
        block = text.split("---\n")[1]  # the front matter sits between the first two markers
        required = ("source_file:", "pages:")  # these 2 fields appear in 100 percent of the staged files
        assert all(field in block for field in required), f"the front matter misses a required field: {block}"
        optional = ("title:", "author:", "subject:", "creationDate:", "modDate:")  # the metadata gives these
        assert all(field in block for field in optional), f"the front matter misses a metadata field: {block}"

    def test_pages_field_equals_source_page_count(self, tmp_path: Path) -> None:
        """The pages field equals the page count of the source PDF."""
        text = self._convert(tmp_path)  # convert the sample guide
        block = text.split("---\n")[1]  # read the front matter block only
        assert f"pages: {len(self.GUIDE)}" in block, f"the pages field must give {len(self.GUIDE)}: {block}"

    def test_heading_count_before_first_page_marker(self, tmp_path: Path) -> None:
        """The file holds 1 heading or more, and 6 headings or less before the first page marker."""
        lines = self._convert(tmp_path).splitlines()  # measure the output line by line
        body = lines[lines.index("---", 1) + 1 :]  # drop the front matter, which also holds a marker line
        headings = [line for line in body if line.startswith("#")]  # every Markdown heading of the file
        assert headings, "the file must hold at least 1 heading"  # row 3 of check V15
        marker = next((index for index, line in enumerate(body) if line.startswith("<!-- page")), len(body))
        early = [line for line in body[:marker] if line.startswith("#")]  # the headings of the cover page
        assert len(early) <= 6, f"the cover page holds {len(early)} headings, and the limit is 6"

    def test_density_gives_two_hundred_characters_for_each_page(self, tmp_path: Path) -> None:
        """The body text gives 200 characters or more for each page of the source."""
        text = self._convert(tmp_path)  # convert the sample guide
        body = text.split("---\n", 2)[2]  # the text that follows the front matter
        density = len(body) / len(self.GUIDE)  # the floor of FR-027 counts characters for each page
        assert density >= 200, f"the density is {density:.1f} characters for each page, and the floor is 200"

    def test_glyph_output_holds_no_ligature_and_no_curly_quote(self, tmp_path: Path) -> None:
        """The output holds no ligature and no curly quotation mark."""
        text = self._convert(tmp_path)  # convert the sample guide
        ligatures = [glyph for glyph in "\ufb00\ufb01\ufb02\ufb03\ufb04" if glyph in text]  # the 5 Latin ligatures
        assert not ligatures, f"the output holds a ligature: {ligatures}"  # row 5 of check V15
        quotes = [glyph for glyph in "\u2018\u2019\u201c\u201d" if glyph in text]  # the 4 curly quotation marks
        assert not quotes, f"the output holds a curly quotation mark: {quotes}"  # row 5 of check V15


class TestHeadingRule:
    """Prove that the body font size is measured for each document and over every page."""

    SENTENCE = "The operator protects the management plane for page {page} and line {line}."

    def _pages(self, body_size: float, title_size: float, count: int) -> list[list[TextLine]]:
        """Return a document whose body uses one size and whose title stands above it."""
        body = self._body_lines(body_size, 1)  # the first page needs unique body text
        first: list[TextLine] = [("The Hardening Guide", title_size, False), *body]  # the cover page
        tail = [self._body_lines(body_size, page) for page in range(2, count + 1)]  # keep edges unique
        return [first] + tail  # the pages let the running header rule keep all body lines

    def _body_lines(self, body_size: float, page: int, count: int = 4) -> list[TextLine]:
        """Return unique body lines, so no page edge looks like a running header."""
        return [
            (self.SENTENCE.format(page=page, line=line), body_size, False)  # distinct text must survive
            for line in range(1, count + 1)  # each line differs from the next line
        ]

    def _share(self, tmp_path: Path, name: str, pages: list[list[TextLine]]) -> tuple[str, float]:
        """Convert one document and return its text with the share of heading lines."""
        source = PdfFixtureBuilder(tmp_path).build(name, pages)  # write the fixture PDF
        output = tmp_path / f"{Path(name).stem}.md"  # the Markdown file sits beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        text = output.read_text(encoding="utf-8")  # read the Markdown once for stable measurement
        lines = self._body_output_lines(text)  # exclude metadata, blanks, and page markers from the share
        headings = [line for line in lines if line.startswith("#")]  # every heading of the file
        return text, len(headings) / max(len(lines), 1)  # return text plus measured heading share

    def _body_output_lines(self, text: str) -> list[str]:
        """Return body lines that can carry a heading decision."""
        body = text.split("---\n", 2)[2]  # front matter must not affect the heading share
        return [
            line  # keep only content that the heading rule classified
            for line in body.splitlines()  # read the rendered body line by line
            if line.strip() and not line.startswith("<!-- page")  # page markers are citations, not content
        ]

    def _front_lines(self, size: float, page: int) -> list[TextLine]:
        """Return unique front matter lines that use the small sample size."""
        return [
            (
                f"The preface page {page} line {line} states how to read this guide safely.",
                size,
                False,
            )  # keep sample text unique
            for line in range(1, 5)  # the sample pages carry enough text to set a wrong body size
        ]

    def test_body_size_is_computed_not_constant(self, tmp_path: Path) -> None:
        """Two documents with different body sizes each give a heading and a small heading share."""
        small, small_share = self._share(tmp_path, "small.pdf", self._pages(10.0, 16.0, 5))
        assert "## The Hardening Guide" in small, "the 16 point title must become a heading"
        large, large_share = self._share(tmp_path, "large.pdf", self._pages(14.0, 20.0, 5))
        assert "## The Hardening Guide" in large, "the 20 point title must become a heading"
        assert small_share <= 0.25, f"the 10 point document marks {small_share:.1%} of its lines as headings"
        assert large_share <= 0.25, f"a constant threshold promotes the 14 point body: {large_share:.1%}"

    def test_body_size_uses_every_page(self, tmp_path: Path) -> None:
        """The front matter size of the first pages must not become the body size."""
        pages: list[list[TextLine]] = [[("The Hardening Guide", 16.0, False), *self._front_lines(8.0, 1)]]
        pages.append(self._front_lines(8.0, 2))  # a two page sample sees the wrong size only
        pages += [self._body_lines(10.0, page) for page in range(3, 9)]  # the full document body is 10 point
        source = PdfFixtureBuilder(tmp_path).build("mixed.pdf", pages)  # write the fixture PDF
        _metadata, _pages, body_size = PdfLineReader(source).read_document()  # measure all pages before render
        assert body_size == 10.0, f"the full document body size must be 10.0, not {body_size}"  # catch sampling
        output = tmp_path / "mixed.md"  # the Markdown file sits beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        lines = self._body_output_lines(output.read_text(encoding="utf-8"))  # measure classified content only
        share = len([line for line in lines if line.startswith("#")]) / len(lines)  # the heading share
        assert share <= 0.25, f"a sample of the first pages returns 8.0 and promotes the body: {share:.1%}"

    def test_body_size_survives_a_bimodal_document(self, tmp_path: Path) -> None:
        """A character weighted histogram ignores many short large lines."""
        short = [(f"A{line}", 14.0, False) for line in range(1, 7)]  # line weighting picks this size
        long = self._body_lines(10.0, 1, 4)  # character weighting picks this size as the real body
        source = PdfFixtureBuilder(tmp_path).build("bimodal.pdf", [short + long])  # write the fixture PDF
        _metadata, _pages, body_size = PdfLineReader(source).read_document()  # measure the body size directly
        assert (
            body_size == 10.0
        ), f"the body size must be 10.0, not the large-line size {body_size}"  # catch line weighting

    def test_heading_marks_a_bold_subheading(self, tmp_path: Path) -> None:
        """A bold line at the body size becomes a subheading."""
        pages: list[list[TextLine]] = [[("Protect the console port", 10.0, True), *self._body_lines(10.0, 1, 3)]]
        pages += [self._body_lines(10.0, page) for page in range(2, 5)]  # give the body the modal size
        source = PdfFixtureBuilder(tmp_path).build("bold.pdf", pages)  # write the fixture PDF
        output = tmp_path / "bold.md"  # the Markdown file sits beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        assert "#### Protect the console port" in output.read_text(encoding="utf-8")  # prove bold body-size subheading


class TestNoiseRules:
    """Prove that a running header, a folio line, and a joined contents run are handled."""

    SENTENCE = "Set a filter on the loopback interface, because that filter protects the engine."

    def _convert(self, tmp_path: Path, name: str, pages: list[list[TextLine]]) -> str:
        """Convert one fixture document and return its Markdown text."""
        source = PdfFixtureBuilder(tmp_path).build(name, pages)  # write the fixture PDF
        output = tmp_path / f"{Path(name).stem}.md"  # the Markdown file sits beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        return output.read_text(encoding="utf-8")  # every assertion reads this text

    def test_running_header_removed(self, tmp_path: Path) -> None:
        """A line that repeats at the top of each page leaves the output."""
        header: TextLine = ("Junos OS Hardening Guide", 10.0, False)  # the same text on every page
        pages = [[header, (self.SENTENCE, 10.0, False), (str(number), 10.0, False)] for number in range(1, 6)]
        text = self._convert(tmp_path, "header.pdf", pages)  # convert the 5 page fixture
        assert "Junos OS Hardening Guide" not in text, "the running header must leave the body"
        assert self.SENTENCE in text, "the body text must stay in the file"

    def test_folio_line_removed(self, tmp_path: Path) -> None:
        """A roman numeral, a page number, and a page label leave the output."""
        folios = ["ii", "iii", "12", "Page 4", "3 of 40"]  # the 5 folio shapes that a guide writes
        pages = [[(folio, 10.0, False), (self.SENTENCE, 10.0, False)] for folio in folios]
        pages.append([("ii. Set the policy on the interface.", 10.0, False)])  # a real list item
        lines = self._convert(tmp_path, "folio.pdf", pages).splitlines()  # convert the fixture
        survivors = [line for line in lines if line.strip() in folios]  # a folio must not survive
        assert not survivors, f"a folio line survives in the output: {survivors}"
        assert "ii. Set the policy on the interface." in lines, "a list item must survive the rule"

    def test_contents_row_stays_on_one_line(self, tmp_path: Path) -> None:
        """A joined contents run gives one output line for each contents entry."""
        joined = "PKI Overview  |  3 PKI in Junos OS  |  7 PKI Components in Junos OS  |  10"
        body = "Read the guide for the filter  |  12"  # a body line holds 1 page number at most
        title: TextLine = ("Table of Contents", 14.0, False)  # a real guide opens the page with a title
        pages: list[list[TextLine]] = [[title, (joined, 10.0, False), (body, 10.0, False)]]
        lines = [line for line in self._convert(tmp_path, "contents.pdf", pages).splitlines() if line.strip()]
        assert "PKI Overview | 3" in lines, f"each contents entry needs its own line: {lines}"
        assert "PKI in Junos OS | 7" in lines, f"each contents entry needs its own line: {lines}"
        assert "Read the guide for the filter | 12" in lines, "a body line with 1 page number stays whole"


class TestGlyphRules:
    """Prove that a ligature, a curly mark, and a bullet glyph reach their plain form."""

    def test_glyph_ligature_and_curly_mark_become_plain(self) -> None:
        """The text rules replace each ligature and each curly quotation mark."""
        rules = MarkdownTextRules()  # the rules hold no state, so a test builds one instance
        assert rules.normalize("A \ufb01lter and a \ufb02ag") == "A filter and a flag"  # 2 ligatures
        assert rules.normalize("the device\u2019s \u201cclass\u201d") == 'the device\'s "class"'

    def test_glyph_bullet_becomes_a_list_item(self, tmp_path: Path) -> None:
        """A line that starts with a bullet glyph becomes a Markdown list item."""
        pages: list[list[TextLine]] = [[("\u2022 Apply the filter to the loopback interface.", 10.0, False)]]
        source = PdfFixtureBuilder(tmp_path).build("bullet.pdf", pages)  # write the fixture PDF
        output = tmp_path / "bullet.md"  # the Markdown file sits beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        text = output.read_text(encoding="utf-8")  # read the produced Markdown
        assert "- Apply the filter to the loopback interface." in text, f"the bullet needs a list mark: {text}"

    def test_glyph_hash_line_is_escaped(self) -> None:
        """A body line that starts with a hash must not become a Markdown heading."""
        rules = MarkdownTextRules()  # the rules hold no state, so a test builds one instance
        assert rules.normalize("# of ports 128") == "\\# of ports 128"  # a table row keeps its text
        assert rules.normalize("Set the filter") == "Set the filter"  # a normal line is unchanged


class TestCommandOutput:
    """Prove the layout rule, the density status, and the conversion manifest."""

    COMMANDS: ClassVar[list[str]] = [
        "set system login class operator permissions view",  # the first line of the example
        "set system login user noc class operator",  # the second line of the example
        "set system services ssh root-login deny",  # the third line of the example
        "set system syslog host 192.0.2.10 any notice",  # the fourth line of the example
    ]

    def test_layout_keeps_command_block_order(self, tmp_path: Path) -> None:
        """A configuration example keeps one output line for each drawn line, in order."""
        title: TextLine = ("Configure the login class", 14.0, False)  # a real example carries a title
        pages: list[list[TextLine]] = [[title, *((command, 10.0, False) for command in self.COMMANDS)]]
        source = PdfFixtureBuilder(tmp_path).build("layout.pdf", pages)  # write the fixture PDF
        output = tmp_path / "layout.md"  # the Markdown file sits beside the fixture
        PdfMarkdownConverter(source, output).convert()  # the call under test
        lines = [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
        found = [line for line in lines if line.startswith("set ")]  # the example lines of the output
        assert found == self.COMMANDS, f"the command block lost its reading order: {found}"

    def test_density_marks_the_review_status(self, tmp_path: Path) -> None:
        """A document below 200 characters for each page carries the review status."""
        pages: list[list[TextLine]] = [[("Thin page.", 10.0, False)] for _ in range(3)]  # 10 characters
        source = PdfFixtureBuilder(tmp_path).build("thin.pdf", pages)  # write the fixture PDF
        row = PdfMarkdownConverter(source, tmp_path / "thin.md").convert()  # the call under test
        assert row["status"] == "review", f"a thin document needs the review status: {row}"
        assert row["pages"] == 3, f"the row must report the page count: {row}"

    def test_manifest_holds_one_row_for_each_source(self, tmp_path: Path) -> None:
        """The command writes a manifest with one row for each named source file."""
        builder = PdfFixtureBuilder(tmp_path)  # both fixtures share one builder
        pages: list[list[TextLine]] = [[(command, 10.0, False) for command in self.COMMANDS]]
        sources = [str(builder.build(f"doc{number}.pdf", pages)) for number in (1, 2)]  # 2 fixtures
        manifest = tmp_path / "_conversion-manifest.json"  # the corpus rebuild reads this file
        PdfMarkdownCommand().run([*sources, "--workers", "1", "--manifest", str(manifest)])
        report = json.loads(manifest.read_text(encoding="utf-8"))  # read the written manifest
        assert len(report["files"]) == 2, f"the manifest needs 1 row for each source: {report}"
        assert report["status_counts"] and report["pages"] == 2, f"the manifest needs the counts: {report}"


class TestPartConverter:
    """Prove that a large document writes parts and still measures every page."""

    @staticmethod
    def _pages(count: int) -> list[list[TextLine]]:
        """Return a fixture whose front matter is smaller than its body."""
        front = [[(f"Contents entry number {number}", 8.0, False)] for number in range(4)]
        body = [[(f"The operator reads page {number} of the guide.", 10.0, False)] for number in range(count - 4)]
        return front + body  # the front matter leads, as a real guide does

    def test_part_converter_writes_one_file_for_each_range(self, tmp_path: Path) -> None:
        """A part run writes one Markdown file for each page range."""
        source = PdfFixtureBuilder(tmp_path).build("big.pdf", self._pages(10))
        target = tmp_path / "big.md"  # the folder takes the name of this file
        row = PdfPartConverter(source, target, None, 4).convert()  # the call under test
        parts = sorted((tmp_path / "big").glob("part-*.md"))  # the written part files
        assert len(parts) == 3, f"10 pages in ranges of 4 need 3 parts: {parts}"
        assert row["pages"] == 10, f"the row must report every page: {row}"

    def test_part_front_matter_names_its_page_range(self, tmp_path: Path) -> None:
        """Each part states the part number and the page range of the source."""
        source = PdfFixtureBuilder(tmp_path).build("ranged.pdf", self._pages(10))
        PdfPartConverter(source, tmp_path / "ranged.md", None, 4).convert()
        first = (tmp_path / "ranged" / "part-001.md").read_text(encoding="utf-8")
        second = (tmp_path / "ranged" / "part-002.md").read_text(encoding="utf-8")
        assert 'page_range: "1-4"' in first, f"the first part covers pages 1 to 4: {first[:200]}"
        assert 'page_range: "5-8"' in second, f"the second part covers pages 5 to 8: {second[:200]}"

    def test_part_body_size_uses_every_page(self, tmp_path: Path) -> None:
        """The measure pass reads every page, so the front matter size never wins."""
        source = PdfFixtureBuilder(tmp_path).build("measured.pdf", self._pages(12))
        _, total, body_size = PdfLineReader(source).measure()  # the call under test
        assert total == 12, f"the measure pass must count every page: {total}"
        assert body_size == 10.0, f"the body size must be the body, not the contents: {body_size}"


class TestGlyphsInMetadata:
    """Prove that the glyph rules reach the front matter and the unmapped mark."""

    def test_front_matter_holds_no_curly_mark(self, tmp_path: Path) -> None:
        """A curly mark in the PDF metadata must reach the file as a plain mark."""
        # The fixture writer stores metadata in latin-1, which holds no curly mark,
        # so this test drives the front matter builder with the metadata directly.
        converter = PdfMarkdownConverter(tmp_path / "x.pdf", tmp_path / "x.md")
        head = converter._front_matter({"Title": "The Operator\u2019s Guide"}, 3)
        assert "\u2019" not in head, f"a curly mark must not survive: {head!r}"
        assert "Operator's Guide" in head, f"the plain mark must replace it: {head!r}"

    def test_unmapped_glyph_mark_is_removed(self) -> None:
        """The reader writes U+FFFD for a glyph with no mapping, so the rule drops it."""
        rules = MarkdownTextRules()  # the rules hold no state
        cleaned = rules.normalize("set system host-name \ufffdlab-router")
        assert "\ufffd" not in cleaned, f"the unmapped mark must go: {cleaned!r}"
        assert cleaned == "set system host-name lab-router", f"the command must stay: {cleaned!r}"
