"""Unit tests for the inventory builder (T018, FR-003, FR-004)."""

from __future__ import annotations

from src.juniper_docs.discovery.inventory_builder import InventoryBuilder
from src.juniper_docs.models import DocumentType

_BASE = "https://www.juniper.net/documentation/us/en/software"


def test_chapter_pages_map_to_one_parent_root() -> None:
    """Two chapter pages under one root collapse to a single document."""
    urls = [
        f"{_BASE}/guide/topics/concept/intro.html",  # First chapter page.
        f"{_BASE}/guide/topics/task/setup.html",  # Second chapter page.
    ]
    records = InventoryBuilder().build(urls)  # Build the inventory from the chapters.
    assert len(records) == 1  # Both chapters map to one document root.
    assert records[0].source_url == f"{_BASE}/guide/"  # The parent root URL.
    assert records[0].doc_type == DocumentType.HTML_ROOT  # It is an HTML root.


def test_duplicate_url_is_removed() -> None:
    """A URL that appears twice yields exactly one inventory record."""
    urls = [f"{_BASE}/guide/", f"{_BASE}/guide/"]  # The same root twice.
    records = InventoryBuilder().build(urls)  # Build the inventory.
    assert len(records) == 1  # The duplicate collapses to one record.


def test_direct_pdf_and_html_root_split() -> None:
    """A direct PDF and an HTML root produce records of the right type."""
    urls = [f"{_BASE}/report.pdf", f"{_BASE}/guide/"]  # One direct PDF and one root.
    records = {record.doc_type: record for record in InventoryBuilder().build(urls)}
    assert records[DocumentType.DIRECT_PDF].source_url == f"{_BASE}/report.pdf"  # Direct.
    assert records[DocumentType.HTML_ROOT].source_url == f"{_BASE}/guide/"  # HTML root.


def test_slug_drops_the_locale_and_documentation_prefix() -> None:
    """The slug drops the documentation and locale segments for classification."""
    records = InventoryBuilder().build([f"{_BASE}/junos-configuration-guide/"])  # One root.
    assert records[0].root_slug == "software/junos-configuration-guide"  # Normalized slug.


def test_html_url_never_gains_a_trailing_slash() -> None:
    """A legacy .html page keeps its exact URL as the root (defect 1 regression)."""
    url = (
        "https://www.juniper.net/documentation/en_US/ctp9.1/information-products/"
        "topic-collections/ctp-server-software/ctpview-server/topic-45714.html"
    )  # The real topic-collections page shape from the smoke run.
    records = InventoryBuilder().build([url])  # Build the inventory for one legacy page.
    root = records[0].source_url  # The composed document root URL.
    assert not root.endswith(".html/")  # The bug appended a slash to a .html URL.
    assert root == url  # The page itself is the root, with no trailing slash.


def test_index_html_maps_to_its_directory() -> None:
    """An index page maps to its directory so it dedups with topic siblings."""
    url = f"{_BASE}/virtual-chassis/index.html"  # An index page under a document root.
    records = InventoryBuilder().build([url])  # Build the inventory for one index page.
    assert records[0].source_url == f"{_BASE}/virtual-chassis/"  # The directory is the root.


def test_other_chapter_pages_map_to_the_guide_root() -> None:
    """A chapter under Other maps to the guide root that holds the one PDF."""
    guide = f"{_BASE}/sd-on-prem-user-guide"  # The guide root holds the TOC script.
    urls = [f"{guide}/Other/threat-map-overview.html", f"{guide}/Other/create-dns-filter.html"]
    records = InventoryBuilder().build(urls)  # Two chapters of the same guide.
    assert len(records) == 1  # Both chapters collapse into one work item.
    assert records[0].source_url == f"{guide}/"  # The guide root carries the PDF.


def test_a_product_subfolder_is_never_treated_as_a_chapter() -> None:
    """A product subfolder keeps its own root, because it holds its own guide."""
    urls = [f"{_BASE}/qfx10016/", f"{_BASE}/qfx10016/qfx10008/"]  # Two real products.
    records = InventoryBuilder().build(urls)  # Build the inventory for both.
    assert len({record.source_url for record in records}) == 2  # Each keeps its root.
