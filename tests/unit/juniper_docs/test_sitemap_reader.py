"""Unit tests for the sitemap reader (T017, FR-001, FR-002)."""

from __future__ import annotations

from src.juniper_docs.discovery.sitemap_reader import SitemapReader
from tests.unit.juniper_docs.conftest import FIXTURES, FakeCatalogClient


def test_read_index_keeps_only_us_en_children() -> None:
    """The reader keeps the two US and EN child sitemaps and drops the rest."""
    reader = SitemapReader(FakeCatalogClient())  # No remote read for a local index.
    children = reader.read_index(str(FIXTURES / "sitemap_index.xml"))  # Read the index.
    assert len(children) == 2  # Two US and EN children survive the filter.
    assert all("us-en" in child for child in children)  # Both carry the US and EN tokens.
    assert not any("de-de" in child or "ja-jp" in child for child in children)  # Others gone.


def test_read_child_extracts_every_url() -> None:
    """The reader extracts every document URL from one child sitemap."""
    reader = SitemapReader(FakeCatalogClient())  # No remote read for a local child.
    urls = reader.read_child(str(FIXTURES / "sitemap_subset.xml"))  # Read the child.
    assert len(urls) == 10  # The subset lists ten URL entries.
    assert any(url.endswith(".pdf") for url in urls)  # It includes a direct PDF URL.
    assert any("/topics/" in url for url in urls)  # It includes chapter pages.


def test_read_all_urls_follows_an_index_to_its_children() -> None:
    """An index source is followed to each US and EN child sitemap."""
    child_url = "https://www.juniper.net/documentation/sitemap/sitemap-us-en-1.xml"  # One child.
    index_url = "https://www.juniper.net/documentation/sitemap/sitemap.xml"  # The index URL.
    texts = {
        index_url: (FIXTURES / "sitemap_index.xml").read_text(encoding="utf-8"),  # The index.
        child_url: "<urlset><url><loc>https://www.juniper.net/documentation/us/en/a/</loc></url></urlset>",
    }
    client = FakeCatalogClient(
        texts=texts,
        fail_urls=("https://www.juniper.net/documentation/sitemap/sitemap-us-en-2.xml",),  # The other child fails.
    )
    urls = SitemapReader(client).read_all_urls(index_url)  # Follow the index to the children.
    assert "https://www.juniper.net/documentation/us/en/a/" in urls  # The child URL is read.


def test_read_all_urls_reads_a_single_child_directly() -> None:
    """A single urlset source is read directly without an index walk."""
    reader = SitemapReader(FakeCatalogClient())  # No remote read for a local child.
    urls = reader.read_all_urls(str(FIXTURES / "sitemap_subset.xml"))  # Read the subset.
    assert len(urls) == 10  # Every URL is returned from the single child.


def test_read_pdf_urls_keeps_only_direct_pdfs() -> None:
    """The marketing read keeps only the direct-PDF URLs of a flat sitemap."""
    reader = SitemapReader(FakeCatalogClient())  # No remote read for a local sitemap.
    pdfs = reader.read_pdf_urls(str(FIXTURES / "sitemap_marketing.xml"))  # Read the marketing set.
    assert len(pdfs) == 4  # The marketing fixture lists four direct PDFs.
    assert all(url.lower().endswith(".pdf") for url in pdfs)  # Every kept URL is a PDF.
    assert not any(url.endswith(".html") for url in pdfs)  # The one HTML entry is dropped.
