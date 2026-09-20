"""Unit tests for the harvest runner (T024, T041).

The tests mock every HTTP read with the fake client and the recorded fixtures.
They prove the cold run records the inventory before any download, resolves,
downloads, classifies, and writes the manifest, and that the run resumes with
no re-download, paces the requests, tolerates a per-document failure, and
reprocesses only the failed documents on a retry (SC-001, SC-003, SC-006, SC-008).
"""

from __future__ import annotations

import json
import ssl
import time
from pathlib import Path
from typing import Any

from src.juniper_docs.discovery.inventory_builder import InventoryBuilder
from src.juniper_docs.discovery.sitemap_reader import SitemapReader
from src.juniper_docs.harvest.runner import (
    DEFAULT_INDEX_URL,
    DEFAULT_MARKETING_URL,
    SOURCE_BOTH,
    SOURCE_MARKETING,
    HarvestConfig,
    HarvestRunner,
    TuningConfig,
    _sanitize,
)
from src.juniper_docs.models import DocumentType
from tests.unit.juniper_docs.conftest import FIXTURES, FakeCatalogClient

_SUBSET = str(FIXTURES / "sitemap_subset.xml")
_MARKETING = str(FIXTURES / "sitemap_marketing.xml")
_SAMPLE_PDF = (FIXTURES / "sample_uncategorized.pdf").read_bytes()
_MINIMAL_PDF = (FIXTURES / "minimal.pdf").read_bytes()
_UNCATEGORIZED_ROOT = "https://www.juniper.net/documentation/us/en/software/srx-routing-overview/"
_SHARED_JVD_PDF = "https://www.juniper.net/documentation/us/en/software/jvd/solution-overview-optics-base-01-01.pdf"


def _config(tmp_path: Path, delay: float = 0.0, retry: bool = False) -> HarvestConfig:
    """Return a config that writes under the test directory and reads the subset."""
    tuning = TuningConfig(delay_seconds=delay, timeout_seconds=5, max_sample_pages=8, confidence_threshold=2.0)
    return HarvestConfig(tmp_path, _SUBSET, "insecure", retry, tuning)  # Client is injected.


def _fake_for_subset(fail_roots: tuple[str, ...] = ()) -> FakeCatalogClient:
    """Return a fake client that serves an index page and a PDF for each root."""
    records = InventoryBuilder().build(SitemapReader(FakeCatalogClient()).read_all_urls(_SUBSET))
    texts: dict[str, str] = {}  # Root URL to index page HTML.
    payloads: dict[str, bytes] = {}  # PDF URL to PDF bytes.
    fail: list[str] = []  # URLs that raise a failure.
    for record in records:  # Build one response per document.
        _script_document(record, texts, payloads, fail, fail_roots)  # Script this document.
    return FakeCatalogClient(texts=texts, payloads=payloads, fail_urls=tuple(fail))


def _script_document(
    record: Any,
    texts: dict[str, str],
    payloads: dict[str, bytes],
    fail: list[str],
    fail_roots: tuple[str, ...],
) -> None:
    """Add the scripted index page and PDF payload for one document."""
    root = record.source_url  # The document root URL or direct PDF URL.
    if record.doc_type == DocumentType.DIRECT_PDF:  # A direct PDF needs only a payload.
        payloads[root] = _MINIMAL_PDF  # Serve a small valid PDF.
        return  # No index page for a direct PDF.
    name = root.rstrip("/").rsplit("/", 1)[-1]  # The document name segment.
    texts[root] = f'<a href="{name}.pdf">PDF</a>'  # An index page naming one PDF.
    fail.append(root.rstrip("/") + "/__toc.js")  # No table-of-contents script.
    pdf_url = root + name + ".pdf"  # The resolved companion PDF URL.
    payloads[pdf_url] = _SAMPLE_PDF if root == _UNCATEGORIZED_ROOT else _MINIMAL_PDF  # Payload.
    if root in fail_roots:  # This document is scripted to fail its download.
        fail.append(pdf_url)  # The PDF read raises a failure.


def _manifest(tmp_path: Path) -> dict[str, dict]:
    """Return the rendered manifest keyed by the source URL."""
    data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))  # Read JSON.
    return {entry["source_url"]: entry for entry in data}  # Key each entry by its URL.


def _marketing_pdf_urls() -> list[str]:
    """Return the direct-PDF URLs the reader extracts from the marketing fixture."""
    return SitemapReader(FakeCatalogClient()).read_pdf_urls(_MARKETING)  # No network read.


def _marketing_config(tmp_path: Path, source: str = SOURCE_MARKETING) -> HarvestConfig:
    """Return a config that reads the marketing fixture under the test directory."""
    tuning = TuningConfig(delay_seconds=0.0, timeout_seconds=5, max_sample_pages=8, confidence_threshold=2.0)
    return HarvestConfig(
        tmp_path, _SUBSET, "insecure", False, tuning, source=source, marketing_source=_MARKETING
    )  # The client is injected in each test.


def _fake_for_marketing() -> FakeCatalogClient:
    """Return a fake client that serves a small valid PDF for each marketing asset."""
    payloads = {url: _MINIMAL_PDF for url in _marketing_pdf_urls()}  # One PDF per asset.
    return FakeCatalogClient(payloads=payloads)  # A direct PDF needs no index page.


def _fake_for_both() -> FakeCatalogClient:
    """Return a fake client that serves the documentation and the marketing responses."""
    client = _fake_for_subset()  # The documentation index pages and companion PDFs.
    for url in _marketing_pdf_urls():  # Add a payload for each marketing asset.
        client.payloads.setdefault(url, _MINIMAL_PDF)  # Keep any existing documentation payload.
    return client  # One client serves both corpora for a combined run.


def test_inventory_recorded_before_any_download(tmp_path: Path) -> None:
    """Discovery records the whole inventory before any PDF is fetched (SC-001)."""
    client = _fake_for_subset()  # A client that would serve every PDF.
    runner = HarvestRunner(_config(tmp_path), client=client)  # Build the runner.
    runner._discover()  # Run discovery only, with no processing.
    rows = runner.store.document_rows()  # Read the recorded inventory.
    runner.store.close()  # Release the database file.
    assert len(rows) == 8  # Every unique document is recorded.
    assert client.requests == []  # No PDF was fetched during discovery.


def test_cold_run_downloads_classifies_and_writes_manifest(tmp_path: Path) -> None:
    """The cold run downloads, classifies, and writes a complete manifest (SC-001)."""
    code = HarvestRunner(_config(tmp_path), client=_fake_for_subset()).run()  # Cold run.
    assert code == 0  # Every document reached a final stage.
    manifest = _manifest(tmp_path)  # Read the rendered manifest.
    assert len(manifest) == 8  # The manifest covers every document (SC-004).
    srx = manifest[_UNCATEGORIZED_ROOT]  # The uncategorized document.
    assert srx["category"] == "uncategorized"  # It matched no slug keyword.
    assert srx["sub_category"] == "srx__configuration__routing"  # The file name names the domain.
    assert srx["status"] == "classified"  # It reached the final classified stage.


def test_cold_run_drops_one_superseded_release_note(tmp_path: Path) -> None:
    """The cold run drops exactly the superseded release note (SC-002)."""
    HarvestRunner(_config(tmp_path), client=_fake_for_subset()).run()  # Cold run.
    dropped = [entry for entry in _manifest(tmp_path).values() if entry["status"] == "dropped"]
    assert len(dropped) == 1  # Exactly one release note is dropped.
    assert dropped[0]["drop_reason"] == "superseded-by-newer-train-member"  # The reason.


def test_subcategory_folder_holds_the_uncategorized_file(tmp_path: Path) -> None:
    """The uncategorized file lands in its content sub-category folder (US2)."""
    HarvestRunner(_config(tmp_path), client=_fake_for_subset()).run()  # Cold run.
    label_dir = tmp_path / "uncategorized" / "srx__configuration__routing"  # Label folder.
    assert label_dir.is_dir()  # The sub-category folder exists.
    assert any(label_dir.glob("*.pdf"))  # The file lands in the label folder.


def test_resume_redownloads_zero_completed(tmp_path: Path) -> None:
    """A restart re-downloads zero completed documents (SC-003)."""
    assert HarvestRunner(_config(tmp_path), client=_fake_for_subset()).run() == 0  # First run.
    second = HarvestRunner(_config(tmp_path), client=_RaisingClient()).run()  # A restart.
    assert second == 0  # The restart processes no completed document, so it never fetches.


def test_pacing_waits_between_two_requests(tmp_path: Path) -> None:
    """The runner waits at least the configured delay between two requests (SC-008)."""
    runner = HarvestRunner(_config(tmp_path, delay=0.05), client=_fake_for_subset())  # Runner.
    runner._pace()  # The first request does not wait.
    start = time.monotonic()  # Start the clock before the second request.
    runner._pace()  # The second request waits the delay.
    elapsed = time.monotonic() - start  # Measure the wait.
    runner.store.close()  # Release the database file.
    assert elapsed >= 0.04  # The runner waited about the configured delay.


def test_per_document_failure_is_recorded_and_run_exits_zero(tmp_path: Path) -> None:
    """A per-document failure is recorded and the run still exits zero (SC-006)."""
    client = _fake_for_subset(fail_roots=(_UNCATEGORIZED_ROOT,))  # One document fails.
    code = HarvestRunner(_config(tmp_path), client=client).run()  # Run with one failure.
    assert code == 0  # One bad document never stops the run.
    assert _manifest(tmp_path)[_UNCATEGORIZED_ROOT]["status"] == "failed"  # It is recorded.


def test_non_pdf_body_marks_the_document_failed(tmp_path: Path) -> None:
    """A non-PDF response body marks the document failed (FR-014)."""
    client = _fake_for_subset()  # Serve every document normally first.
    client.payloads[_UNCATEGORIZED_ROOT + "srx-routing-overview.pdf"] = b"<html>error</html>"
    code = HarvestRunner(_config(tmp_path), client=client).run()  # Run with a bad body.
    assert code == 0  # The run continues past the rejected body.
    assert _manifest(tmp_path)[_UNCATEGORIZED_ROOT]["status"] == "failed"  # It is failed.


def test_live_page_with_no_pdf_is_recorded_as_no_pdf(tmp_path: Path) -> None:
    """A live page that names no PDF is a clean no_pdf, not a failure (defect 4)."""
    client = _fake_for_subset()  # Serve every document normally first.
    client.texts[_UNCATEGORIZED_ROOT] = "<p>this page names no pdf</p>"  # A live no-PDF page.
    code = HarvestRunner(_config(tmp_path), client=client).run()  # Run the harvest.
    assert code == 0  # A no-PDF document never stops the run.
    entry = _manifest(tmp_path)[_UNCATEGORIZED_ROOT]  # The no-PDF document entry.
    assert entry["status"] == "no_pdf"  # It is recorded as a clean no-PDF outcome.
    assert entry["error_reason"] == "no companion PDF found"  # The recorded reason.


def test_no_pdf_is_not_counted_as_a_failure(tmp_path: Path) -> None:
    """A no_pdf document is a distinct status from a failed one (defect 4)."""
    client = _fake_for_subset()  # Serve every document normally first.
    client.texts[_UNCATEGORIZED_ROOT] = "<p>no pdf</p>"  # One live no-PDF page.
    HarvestRunner(_config(tmp_path), client=client).run()  # Run the harvest.
    statuses = {entry["status"] for entry in _manifest(tmp_path).values()}  # The statuses seen.
    assert "no_pdf" in statuses  # The no-PDF status appears in the manifest.
    assert "failed" not in statuses  # No document is recorded as a real failure.


def test_retry_failed_reprocesses_only_failed(tmp_path: Path) -> None:
    """A retry run reprocesses only the failed document (FR-034)."""
    first = HarvestRunner(_config(tmp_path), client=_fake_for_subset(fail_roots=(_UNCATEGORIZED_ROOT,)))
    assert first.run() == 0  # The first run fails one document.
    retry_client = _fake_for_subset()  # A client that now serves every document.
    assert HarvestRunner(_config(tmp_path, retry=True), client=retry_client).run() == 0  # Retry.
    assert _manifest(tmp_path)[_UNCATEGORIZED_ROOT]["status"] == "classified"  # Now classified.
    assert all(_UNCATEGORIZED_ROOT in url for url in retry_client.requests)  # Only that one.


def test_marketing_run_sorts_each_asset_by_type(tmp_path: Path) -> None:
    """A marketing run sorts each asset into its asset-type category (US1)."""
    code = HarvestRunner(_marketing_config(tmp_path), client=_fake_for_marketing()).run()  # Run.
    assert code == 0  # Every marketing asset reached a final stage.
    categories = {entry["category"] for entry in _manifest(tmp_path).values()}  # The categories.
    assert "datasheets" in categories  # The datasheet lands in the datasheet category.
    assert "case-studies" in categories  # The case study lands in the case-study category.
    assert "solution-briefs" in categories  # The solution brief lands in its category.


def test_marketing_asset_downloads_without_resolution(tmp_path: Path) -> None:
    """A marketing asset flows straight to the downloader as a direct PDF (FR-011)."""
    HarvestRunner(_marketing_config(tmp_path), client=_fake_for_marketing()).run()  # Run.
    datasheet = next(e for e in _manifest(tmp_path).values() if e["category"] == "datasheets")
    assert datasheet["status"] == "classified"  # The asset reached the final classified stage.
    assert datasheet["sub_category"] is None  # A marketing asset needs no content label.
    assert (tmp_path / "datasheets").is_dir()  # The asset lands in its category folder.


def test_both_source_merges_documentation_and_marketing_without_a_duplicate(tmp_path: Path) -> None:
    """The marketing assets merge with the documentation set with no duplicate (merge)."""
    code = HarvestRunner(_marketing_config(tmp_path, source=SOURCE_BOTH), client=_fake_for_both()).run()
    assert code == 0  # The combined run finished with every document at a final stage.
    data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))  # The raw list.
    matching = [entry for entry in data if entry["source_url"] == _SHARED_JVD_PDF]  # Shared URL.
    assert len(matching) == 1  # The shared JVD PDF appears exactly once, so no duplicate.
    assert matching[0]["category"] == "design"  # The documentation classification is kept.


def test_both_source_adds_the_marketing_only_assets(tmp_path: Path) -> None:
    """The combined run adds each marketing asset that the documentation set lacks."""
    HarvestRunner(_marketing_config(tmp_path, source=SOURCE_BOTH), client=_fake_for_both()).run()
    categories = {entry["category"] for entry in _manifest(tmp_path).values()}  # The categories.
    assert "datasheets" in categories  # The marketing datasheet joins the corpus.
    assert "configuration-guides" in categories  # A documentation category is still present.


def test_marketing_config_from_args_defaults_to_documentation() -> None:
    """The default source is documentation, so an existing caller is unaffected."""
    config = HarvestConfig.from_args([])  # Parse with no arguments.
    assert config.source == "documentation"  # The default preserves the old behavior.
    assert config.marketing_source == DEFAULT_MARKETING_URL  # The default marketing sitemap.


def test_marketing_config_from_args_selects_both_sources() -> None:
    """The source and marketing overrides apply from the command line."""
    config = HarvestConfig.from_args(["--source", "both", "--marketing-sitemap-source", "m.xml"])
    assert config.source == SOURCE_BOTH  # The source override applies.
    assert config.marketing_source == "m.xml"  # The marketing source override applies.


class _RaisingClient:
    """A client that raises on any fetch, proving a resume makes no request."""

    def fetch_text(self, url: str) -> str:
        """Raise because a completed resume must not re-read any page."""
        raise AssertionError(f"unexpected re-read of {url}")  # No fetch is allowed.

    def fetch_bytes(self, url: str) -> bytes:
        """Raise because a completed resume must not re-download any file."""
        raise AssertionError(f"unexpected re-download of {url}")  # No fetch is allowed.

    def fetch_size(self, url: str) -> int | None:
        """Return None because a completed resume probes no size."""
        return None  # No size probe happens on a completed resume.


def test_config_from_args_uses_safe_defaults() -> None:
    """A cold run needs no argument, so every default is safe."""
    config = HarvestConfig.from_args([])  # Parse with no arguments.
    assert config.tls_mode == "auto"  # The default TLS mode is auto.
    assert config.sitemap_source == DEFAULT_INDEX_URL  # The default source is the index.
    assert config.tuning.delay_seconds == 1.0  # The default delay is one second.
    assert config.retry_failed is False  # The default does not retry failures.


def test_config_from_args_applies_overrides() -> None:
    """Each argument overrides its default value."""
    config = HarvestConfig.from_args(
        ["--tls-mode", "insecure", "--delay-seconds", "0.5", "--retry-failed"]
    )  # Parse with overrides.
    assert config.tls_mode == "insecure"  # The TLS mode override applies.
    assert config.tuning.delay_seconds == 0.5  # The delay override applies.
    assert config.retry_failed is True  # The retry flag applies.


def test_build_client_selects_the_tls_context(tmp_path: Path) -> None:
    """The runner builds a client whose context matches the TLS mode."""
    client = HarvestRunner._build_client(_config(tmp_path))  # Insecure config.
    assert client.config.ssl_context.verify_mode == ssl.CERT_NONE  # The insecure context.


def test_sanitize_makes_a_windows_safe_name() -> None:
    """The sanitizer replaces invalid characters and never returns an empty name."""
    assert _sanitize("a<b>c:d/e") == "a-b-c-d-e"  # Each invalid character is replaced.
    assert _sanitize("   ") == "unnamed"  # An empty result becomes a safe default.


def test_a_sibling_page_reuses_the_folder_pdf(tmp_path: Path) -> None:
    """A second page in one folder reuses the sibling answer, so no new fetch runs."""
    runner = HarvestRunner(_config(tmp_path), client=_fake_for_subset())  # A real runner.
    folder = "https://www.juniper.net/documentation/us/en/software/guide-a"  # One folder.
    runner._folder_pdfs[folder] = f"{folder}/guide-a.pdf"  # A sibling already resolved.
    shared = runner._sibling_pdf(f"{folder}/chapter-two.html")  # Another page, same folder.
    assert shared == f"{folder}/guide-a.pdf"  # The runner answers from the folder map.


def test_a_subfolder_document_is_never_answered_by_its_parent(tmp_path: Path) -> None:
    """An ancestor folder must not answer, because a subfolder holds its own document."""
    runner = HarvestRunner(_config(tmp_path), client=_fake_for_subset())  # A real runner.
    parent = "https://www.juniper.net/documentation/us/en/hardware/qfx10016"  # The parent.
    runner._folder_pdfs[parent] = f"{parent}/qfx10016.pdf"  # The parent resolved its guide.
    shared = runner._sibling_pdf(f"{parent}/qfx10008/")  # A different product below it.
    assert shared is None  # The parent never answers, so qfx10008.pdf is not lost.
