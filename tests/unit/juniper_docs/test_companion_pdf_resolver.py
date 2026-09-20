"""Unit tests for the companion PDF resolver (T020, FR-010a, FR-010b, FR-012)."""

from __future__ import annotations

from src.juniper_docs.acquire.pdf_resolver import CompanionPdfResolver, JvdPdfResolver
from src.juniper_docs.models import ResolveOutcome
from tests.unit.juniper_docs.conftest import FakeCatalogClient, read_fixture

_ROOT = "https://www.juniper.net/documentation/us/en/software/multi-pdf-guide/"


def _toc(root: str) -> str:
    """Return the sibling table-of-contents URL for one root."""
    return root.rstrip("/") + "/__toc.js"  # The resolver reads this second.


def test_name_match_wins_and_records_rejects() -> None:
    """The name-matching whole-document PDF wins and the rest are rejected."""
    client = FakeCatalogClient(
        texts={_ROOT: read_fixture("root_index_multi_pdf.html")},  # The multi-PDF page.
        fail_urls=(_toc(_ROOT),),  # No table-of-contents script.
    )
    chosen, candidates, outcome, _reason = CompanionPdfResolver(client).resolve_companion(_ROOT)
    assert chosen == _ROOT + "multi-pdf-guide.pdf"  # The name match is chosen.
    assert outcome == ResolveOutcome.RESOLVED  # The document resolved to a PDF.
    winners = [row for row in candidates if row.chosen]  # Every chosen candidate.
    assert len(winners) == 1 and winners[0].reason == "name-match"  # Exactly one, by name.
    assert len([row for row in candidates if not row.chosen]) == 3  # Three rejected candidates.


def test_same_folder_first_when_no_name_match() -> None:
    """The first same-folder PDF wins when no name matches the slug."""
    root = "https://x/docs/guide/"  # A root whose name matches no candidate.
    html = '<a href="aaa.pdf">A</a><a href="bbb.pdf">B</a>'  # Two same-folder PDFs.
    client = FakeCatalogClient(texts={root: html}, fail_urls=(_toc(root),))  # No TOC.
    chosen, candidates, _outcome, _reason = CompanionPdfResolver(client).resolve_companion(root)
    assert chosen == root + "aaa.pdf"  # The first same-folder PDF wins.
    assert next(row.reason for row in candidates if row.chosen) == "same-folder-first"  # Rule.


def test_largest_when_neither_name_nor_folder_decides() -> None:
    """The largest PDF wins when name and folder do not decide."""
    root = "https://x/docs/guide/"  # A root whose name matches no candidate.
    html = '<a href="sub1/x.pdf">X</a><a href="sub2/y.pdf">Y</a>'  # Two sub-folder PDFs.
    sizes = {root + "sub1/x.pdf": 100, root + "sub2/y.pdf": 500}  # The larger is y.pdf.
    client = FakeCatalogClient(texts={root: html}, sizes=sizes, fail_urls=(_toc(root),))
    chosen, candidates, _outcome, _reason = CompanionPdfResolver(client).resolve_companion(root)
    assert chosen == root + "sub2/y.pdf"  # The largest file wins the final tiebreak.
    assert next(row.reason for row in candidates if row.chosen) == "largest"  # The rule.


def test_no_pdf_found_returns_no_pdf_outcome() -> None:
    """A live root that names no PDF yields a clean no-PDF outcome."""
    root = "https://x/docs/empty/"  # A live root with no PDF anywhere.
    client = FakeCatalogClient(texts={root: "<p>no pdf here</p>"}, fail_urls=(_toc(root),))
    chosen, candidates, outcome, reason = CompanionPdfResolver(client).resolve_companion(root)
    assert chosen is None  # No PDF was found.
    assert candidates == []  # No candidate was recorded.
    assert outcome == ResolveOutcome.NO_PDF  # A live page with no PDF is a clean no-PDF.
    assert reason == "no companion PDF found"  # The recorded no-PDF reason.


def test_base_resolver_returns_a_direct_pdf() -> None:
    """The base resolver returns a URL that already names a PDF unchanged."""
    resolver = JvdPdfResolver(FakeCatalogClient())  # No fetch is needed.
    assert resolver.resolve("https://x/docs/report.pdf") == "https://x/docs/report.pdf"


def test_base_resolver_reads_the_index_page_first() -> None:
    """The base resolver finds the PDF named on the index page."""
    page = "https://x/docs/guide/index.html"  # The index page URL.
    client = FakeCatalogClient(texts={page: '<a href="whole.pdf">PDF</a>'})  # Names a PDF.
    assert JvdPdfResolver(client).resolve(page) == "https://x/docs/guide/whole.pdf"


def test_base_resolver_falls_back_to_the_toc() -> None:
    """The base resolver reads the TOC script when the index names no PDF."""
    page = "https://x/docs/guide/index.html"  # The index page URL.
    toc = "https://x/docs/guide/__toc.js"  # The sibling TOC script URL.
    client = FakeCatalogClient(texts={page: "<p>no pdf</p>", toc: 'pdf: "whole.pdf"'})
    assert JvdPdfResolver(client).resolve(page) == "https://x/docs/guide/whole.pdf"


def test_base_resolver_returns_none_when_the_page_fails() -> None:
    """The base resolver returns None when the index page cannot be read."""
    page = "https://x/docs/guide/index.html"  # The index page URL.
    client = FakeCatalogClient(fail_urls=(page,))  # The page read fails.
    assert JvdPdfResolver(client).resolve(page) is None  # No PDF is resolved.


def test_resolver_walks_up_when_the_composed_root_is_not_served() -> None:
    """The resolver walks up to the product root when the composed root errors (defect 2)."""
    composed = "https://x/hardware/srx5800/jrr200/"  # A composed root that returns an error.
    parent = "https://x/hardware/srx5800/"  # The product root that serves the PDF.
    client = FakeCatalogClient(
        texts={parent: '<a href="srx5800-gettingstarted.pdf">PDF</a>'},  # Product page PDF.
        fail_urls=(composed, _toc(composed)),  # The composed root and its TOC both error.
    )
    chosen, _candidates, outcome, _reason = CompanionPdfResolver(client).resolve_companion(composed)
    assert outcome == ResolveOutcome.RESOLVED  # The walk-up found the product PDF.
    assert chosen == parent + "srx5800-gettingstarted.pdf"  # The PDF at the product root.


def test_resolver_reports_failed_when_no_level_is_reachable() -> None:
    """The resolver reports a real failure when no level serves a live page (defect 4)."""
    composed = "https://x/hardware/ghost/variant/"  # A root whose levels all error.
    fail = (
        composed,
        _toc(composed),
        "https://x/hardware/ghost/",
        "https://x/hardware/ghost/__toc.js",
        "https://x/hardware/",
        "https://x/hardware/__toc.js",
    )  # Every walk-up level errors.
    client = FakeCatalogClient(fail_urls=fail)  # No live page anywhere.
    chosen, _candidates, outcome, reason = CompanionPdfResolver(client).resolve_companion(composed)
    assert chosen is None  # Nothing resolved.
    assert outcome == ResolveOutcome.FAILED  # A real resolution failure, not a clean no-PDF.
    assert reason.startswith(("permanent", "transient"))  # The reason names the failure kind.
