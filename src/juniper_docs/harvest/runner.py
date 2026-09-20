"""Drive the whole Juniper documentation harvest end to end.

The runner builds the configuration, wires the discovery, acquire, classify, and
harvest collaborators, and orchestrates one resumable, polite, fault-tolerant
run. It discovers the inventory, drops each superseded release note, resolves and
downloads each companion PDF, sorts each file into a category, derives a content
sub-category for an uncategorized document, and writes the manifest and summary.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import argparse  # Parse the command-line arguments into the configuration.
import logging  # Log the progress and the final summary.
import re  # Sanitize a category or sub-category folder name.
import shutil  # Move an uncategorized file into its sub-category folder.
import sqlite3  # Type the document rows read from the store.
import time  # Pace the requests so the crawl stays polite.
import urllib.error  # Classify a per-document network failure.
from dataclasses import dataclass, field  # Group the config and the collaborators.
from pathlib import Path  # Build every output path in a portable way.

from src.juniper_docs.acquire.catalog_client import (  # Shared HTTP client and host guard.
    HostUnreachableError,
    JvdCatalogClient,
)
from src.juniper_docs.acquire.downloader import CorpusDownloader  # Category-aware download.
from src.juniper_docs.acquire.http_config import HttpConfig  # Origin, timeout, SSL context.
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator  # Collision-safe path policy.
from src.juniper_docs.acquire.pdf_resolver import CompanionPdfResolver  # Companion resolve.
from src.juniper_docs.classify.asset_classifier import MarketingAssetClassifier  # Asset type.
from src.juniper_docs.classify.content_sampler import ContentSampler  # Bounded PDF sample.
from src.juniper_docs.classify.signal_scorer import SignalScorer  # Content sub-category.
from src.juniper_docs.classify.slug_classifier import UNCATEGORIZED, SlugClassifier  # Slug.
from src.juniper_docs.discovery.inventory_builder import InventoryBuilder  # Inventory build.
from src.juniper_docs.discovery.landing_page_reader import ProductLandingReader  # Landing pages.
from src.juniper_docs.discovery.release_note_selector import CorpusReleaseNoteSelector  # Filter.
from src.juniper_docs.discovery.sitemap_reader import SitemapReader  # Sitemap read.
from src.juniper_docs.harvest.manifest_writer import ManifestWriter  # Manifest render.
from src.juniper_docs.harvest.state_store import HarvestStateStore, StateStoreError  # Store.
from src.juniper_docs.models import (  # Shared types for the runner.
    ContentAnalysisResult,
    DocumentType,
    InventoryRecord,
    PdfCandidate,
    ResolveOutcome,
)

_LOGGER = logging.getLogger(__name__)  # Module logger for the runner.

DEFAULT_INDEX_URL = "https://www.juniper.net/documentation/sitemap/sitemap.xml"  # Live index.
DEFAULT_MARKETING_URL = "https://www.juniper.net/sitemaps/en_US.xml"  # Marketing sitemap.
DEFAULT_OUTPUT_DIR = Path("data/juniper_corpus")  # The output root under data/.
DISCOVERY_FLAG = "discovery_complete"  # The run-meta flag that enables a fresh resume.
SOURCE_DOCUMENTATION = "documentation"  # Read only the documentation sitemap index.
SOURCE_MARKETING = "marketing"  # Read only the marketing sitemap of direct PDFs.
SOURCE_PRODUCT_LANDING = "product-landing"  # Read only the product landing pages.
SOURCE_BOTH = "both"  # Read the documentation index and the marketing sitemap.
SOURCE_ALL = "all"  # Read the documentation, the marketing, and the product landing sources.
_SOURCE_CHOICES = (
    SOURCE_DOCUMENTATION,
    SOURCE_MARKETING,
    SOURCE_PRODUCT_LANDING,
    SOURCE_BOTH,
    SOURCE_ALL,
)  # Every source name a caller can select.
_DOCUMENTATION_SOURCES = (SOURCE_DOCUMENTATION, SOURCE_BOTH, SOURCE_ALL)  # Read documentation.
_MARKETING_SOURCES = (SOURCE_MARKETING, SOURCE_BOTH, SOURCE_ALL)  # Read the marketing sitemap.
_PRODUCT_LANDING_SOURCES = (SOURCE_PRODUCT_LANDING, SOURCE_ALL)  # Read the product landing pages.
_INVALID_NAME = re.compile(r'[<>:"/\\|?*]')  # Characters invalid in a Windows file name.


@dataclass(frozen=True)
class TuningConfig:
    """The numeric tuning values for the pace, the timeout, and the sample."""

    delay_seconds: float = 1.0  # The minimum delay between two requests.
    timeout_seconds: int = 90  # The per-request timeout, generous for a large PDF.
    max_sample_pages: int = 8  # The page cap for the bounded content sample.
    confidence_threshold: float = 0.25  # The minimum normalized score for a real label.


@dataclass(frozen=True)
class HarvestConfig:
    """The whole run configuration, built with safe defaults."""

    output_dir: Path = DEFAULT_OUTPUT_DIR  # The output root under data/.
    sitemap_source: str = DEFAULT_INDEX_URL  # The live index or a recorded subset.
    tls_mode: str = "auto"  # The TLS mode: auto, verify, or insecure.
    retry_failed: bool = False  # Reprocess documents whose stage is failed.
    tuning: TuningConfig = field(default_factory=TuningConfig)  # The numeric tuning group.
    source: str = SOURCE_DOCUMENTATION  # Which corpus to harvest; documentation by default.
    marketing_source: str = DEFAULT_MARKETING_URL  # The marketing sitemap or a subset.

    @classmethod
    def from_args(cls, argv: list[str] | None = None) -> HarvestConfig:
        """Build the configuration from the command-line arguments."""
        args = _parser().parse_args(argv)  # Parse the arguments with safe defaults.
        tuning = TuningConfig(
            args.delay_seconds, args.timeout_seconds, args.max_sample_pages, args.confidence_threshold
        )  # The numeric tuning group.
        return cls(
            Path(args.output_dir),
            args.sitemap_source,
            args.tls_mode,
            args.retry_failed,
            tuning,
            source=args.source,
            marketing_source=args.marketing_sitemap_source,
        )


@dataclass(frozen=True)
class AcquirePipeline:
    """The discovery and acquire collaborators for one run."""

    reader: SitemapReader  # Reads the sitemap index and child sitemaps.
    builder: InventoryBuilder  # Builds the deduplicated inventory.
    selector: CorpusReleaseNoteSelector  # Drops each superseded release note.
    resolver: CompanionPdfResolver  # Resolves one companion PDF per root.
    downloader: CorpusDownloader  # Downloads each PDF into its category folder.


@dataclass(frozen=True)
class ClassifyPipeline:
    """The classification collaborators for one run."""

    slug: SlugClassifier  # Classifies each document by its slug.
    sampler: ContentSampler  # Reads a bounded in-memory PDF text sample.
    scorer: SignalScorer  # Derives the content sub-category label.
    asset: MarketingAssetClassifier  # Classifies a marketing asset by its type.


class HarvestRunner:
    """Orchestrate the resumable, polite, fault-tolerant corpus harvest."""

    def __init__(self, config: HarvestConfig, client: JvdCatalogClient | None = None) -> None:
        """Build the store and wire the acquire, landing, and classify collaborators."""
        _LOGGER.info("Preparing the harvest runner")  # Log the intent.
        self.config = config  # The whole run configuration.
        self.store = HarvestStateStore(config.output_dir / "harvest_state.db")  # Durable store.
        self._allocator = PdfPathAllocator(self.store.owner_of_path)  # Collision-safe path policy.
        http_client = client or self._build_client(config)  # One shared HTTP client for reads.
        self.acquire = self._build_acquire(http_client)  # Discovery and acquire collaborators.
        self.landing = ProductLandingReader(http_client)  # Product landing page reader.
        self.classify = self._build_classify(config)  # Classify side.
        self._counters = {
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "dropped": 0,
            "no_pdf": 0,
            "unreachable": 0,
        }
        self._folder_pdfs: dict[str, str] = {}  # Folder to its shared companion PDF URL.
        self._last_request = 0.0  # The monotonic time of the last paced request.

    @staticmethod
    def _build_client(config: HarvestConfig) -> JvdCatalogClient:
        """Return an HTTP client whose SSL context matches the TLS mode."""
        context = HttpConfig.build_ssl_context(config.tls_mode)  # Verified or insecure.
        http = HttpConfig(context, config.tuning.timeout_seconds, config.tuning.delay_seconds)
        return JvdCatalogClient(http)  # The shared client for every network read.

    def _build_acquire(self, client: JvdCatalogClient) -> AcquirePipeline:
        """Return the acquire collaborators bound to the shared client."""
        return AcquirePipeline(
            SitemapReader(client),  # Sitemap reader.
            InventoryBuilder(),  # Inventory builder.
            CorpusReleaseNoteSelector(),  # Release-note filter.
            CompanionPdfResolver(client),  # Companion PDF resolver.
            CorpusDownloader(client, self.config.output_dir, self._allocator),  # Category-aware.
        )

    @staticmethod
    def _build_classify(config: HarvestConfig) -> ClassifyPipeline:
        """Return the classification collaborators built from the tuning values."""
        return ClassifyPipeline(
            SlugClassifier(),  # Slug classifier.
            ContentSampler(config.tuning.max_sample_pages),  # Bounded content sampler.
            SignalScorer(config.tuning.confidence_threshold),  # Content signal scorer.
            MarketingAssetClassifier(),  # Marketing asset-type classifier.
        )

    def run(self) -> int:
        """Run the whole harvest and return the process exit code."""
        _LOGGER.info("Starting the Juniper documentation harvest")  # Log the start.
        try:
            return self._run_pipeline()  # Discover, process, and report.
        except StateStoreError as error:  # A locked or damaged store fails closed.
            _LOGGER.error("The run failed closed: %s", error)  # Report the failure.
            return 1  # A store failure exits with a non-zero code.
        finally:
            self.store.close()  # Always release the database file.

    def _run_pipeline(self) -> int:
        """Discover or resume, process every document, and write the manifest."""
        self.store.check_integrity()  # Fail closed on a damaged store.
        if self.store.get_meta(DISCOVERY_FLAG) != "1":  # A cold start reads the sitemap.
            self._discover()  # Build and save the inventory.
        else:  # A resume reuses the recorded inventory with no sitemap read.
            _LOGGER.info("Resuming from the recorded inventory")  # Log the resume.
        self._process_all()  # Resolve, download, and classify each document.
        self._write_manifest()  # Render the manifest from the store.
        self._print_summary()  # Print the final summary counts.
        return 0  # Every document reached a final stage.

    def _discover(self) -> None:
        """Read each configured corpus and record its inventory before download."""
        _LOGGER.info("Discovering inventory for source %s", self.config.source)  # Log intent.
        if self.config.source in _DOCUMENTATION_SOURCES:  # Documentation corpus.
            self._discover_documentation()  # Read the documentation sitemap index.
        if self.config.source in _MARKETING_SOURCES:  # Marketing corpus.
            self._discover_marketing()  # Read the marketing sitemap of direct PDFs.
        if self.config.source in _PRODUCT_LANDING_SOURCES:  # Product landing corpus.
            self._discover_product_landing()  # Read each product landing page.
        self.store.set_meta(DISCOVERY_FLAG, "1")  # Mark discovery done for a resume.
        _LOGGER.info("Inventory recorded")  # The inventory is durable before any download.

    def _discover_documentation(self) -> None:
        """Read the documentation sitemap, build the inventory, and drop old notes."""
        _LOGGER.info("Discovering documentation from %s", self.config.sitemap_source)  # Intent.
        urls = self.acquire.reader.read_all_urls(self.config.sitemap_source)  # Every URL.
        records = self.acquire.builder.build(urls)  # The deduplicated inventory.
        self._save_inventory(records)  # Save every document before any download.
        self._drop_release_notes(records)  # Drop each superseded release note.
        _LOGGER.debug("Recorded %d documentation records", len(records))  # Result count.

    def _discover_marketing(self) -> None:
        """Read the marketing sitemap and record each direct-PDF asset."""
        _LOGGER.info("Discovering marketing assets from %s", self.config.marketing_source)  # Intent.
        urls = self.acquire.reader.read_pdf_urls(self.config.marketing_source)  # Direct PDFs.
        records = self.acquire.builder.build(urls)  # DIRECT_PDF records, deduplicated.
        self._save_marketing(records)  # Save each asset with its asset-type category.
        _LOGGER.debug("Recorded %d marketing records", len(records))  # Result count.

    def _discover_product_landing(self) -> None:
        """Read each product landing page and record its new direct-PDF references."""
        _LOGGER.info("Discovering product landing PDFs from %s", self.config.sitemap_source)  # Intent.
        urls = self.acquire.reader.read_all_urls(self.config.sitemap_source)  # Every sitemap URL.
        pages = self.landing.landing_pages(urls)  # The product landing pages only.
        pdfs = self._collect_landing_pdfs(pages)  # Fetch each page, paced, and collect its PDFs.
        records = self.acquire.builder.build(pdfs)  # DIRECT_PDF records, deduplicated by URL.
        fresh = [r for r in records if self.store.stage_of(r.source_url) is None]  # New URLs only.
        self._save_landing(fresh)  # Save each new asset with its slug category.
        self._drop_release_notes(fresh)  # Keep only the newest release note in each train.
        _LOGGER.debug("Recorded %d product landing records", len(fresh))  # Result count.

    def _collect_landing_pdfs(self, pages: list[str]) -> list[str]:
        """Return every unique PDF URL across the product landing pages, paced."""
        _LOGGER.info("Reading %d product landing pages", len(pages))  # Log the work size.
        pdfs: set[str] = set()  # Accumulate every unique PDF URL across the pages.
        for page in pages:  # Read one landing page at a time to stay polite.
            self._pace()  # Wait the configured delay before each page fetch.
            self._add_page_pdfs(page, pdfs)  # Add this page's PDF URLs, tolerating a failure.
        _LOGGER.debug("Collected %d unique product landing PDFs", len(pdfs))  # Result count.
        return sorted(pdfs)  # A stable order keeps the inventory reproducible.

    def _add_page_pdfs(self, page: str, pdfs: set[str]) -> None:
        """Add one landing page's PDF URLs to the set, tolerating a per-page failure."""
        try:
            pdfs.update(self.landing.pdf_urls_on_page(page))  # Add every PDF this page names.
        except (urllib.error.URLError, urllib.error.HTTPError) as error:  # One bad page.
            _LOGGER.warning("Skipping product landing page %s: %s", page, error)  # Record miss.

    def _save_landing(self, records: list[InventoryRecord]) -> None:
        """Save each new product landing asset with its slug category."""
        for record in records:  # Persist each fresh direct-PDF landing asset in turn.
            self.store.add_document(record)  # Insert the asset at the discovered stage.
            category = self.classify.slug.classify(record.root_slug)  # Slug category.
            self.store.set_category(record.source_url, category)  # Set it early for coverage.

    def _save_inventory(self, records: list[InventoryRecord]) -> None:
        """Save each document and set its slug category before any download."""
        for record in records:  # Persist every document at the discovered stage.
            self.store.add_document(record)  # Insert the document, ignoring a repeat.
            category = self.classify.slug.classify(record.root_slug)  # Slug category.
            self.store.set_category(record.source_url, category)  # Set it early for coverage.

    def _save_marketing(self, records: list[InventoryRecord]) -> None:
        """Save each marketing asset with its asset-type category, skipping a duplicate."""
        for record in records:  # Persist each direct-PDF marketing asset in turn.
            if self.store.stage_of(record.source_url) is not None:  # A documentation duplicate.
                continue  # Keep the existing record, so no duplicate and no reclassification.
            self.store.add_document(record)  # Insert the asset at the discovered stage.
            category = self.classify.asset.classify(record.source_url)  # Asset-type category.
            self.store.set_category(record.source_url, category)  # Set the marketing category.

    def _drop_release_notes(self, records: list[InventoryRecord]) -> None:
        """Drop each superseded release note and record the reason."""
        dropped = self.acquire.selector.filter_records(records)[1]  # The drop pairs only.
        for root_url, reason in dropped:  # Record each dropped release note.
            self.store.record_dropped(root_url, reason)  # Mark it dropped with the reason.
            self._counters["dropped"] += 1  # Count it for the summary.

    def _process_all(self) -> None:
        """Process every non-final document and log the progress."""
        rows = self.store.resume_documents(self.config.retry_failed)  # The work list.
        self._load_folder_pdfs()  # Reuse every answer that an earlier run recorded.
        total = len(rows)  # The total count for the progress log.
        _LOGGER.info("Processing %d documents", total)  # Log the work size.
        for index, row in enumerate(rows, start=1):  # Process one document at a time.
            _LOGGER.info("Processing %d of %d: %s", index, total, row["root_url"])  # Progress.
            self._process_document(row)  # Advance this document to a final stage.

    def _load_folder_pdfs(self) -> None:
        """Fill the folder map from every document that already resolved."""
        _LOGGER.info("Loading the resolved PDF answers of the earlier runs")  # Log intent.
        for row in self.store.document_rows():  # Walk every recorded document row.
            resolved = row["resolved_pdf_url"]  # The PDF this document resolved to.
            if resolved:  # Only a resolved document can answer for its folder.
                self._folder_pdfs.setdefault(_folder_of(str(row["root_url"])), str(resolved))
        _LOGGER.debug("Loaded %d folder answers", len(self._folder_pdfs))  # Result count.

    def _process_document(self, row: sqlite3.Row) -> None:
        """Advance one document, recording a per-document failure and continuing."""
        root = str(row["root_url"])  # The document root URL is the natural key.
        try:
            self._advance(row, root)  # Resolve, download, and classify this document.
        except HostUnreachableError as error:  # The host stayed silent, so the file is skipped.
            _LOGGER.warning("Document %s skipped: %s", root, error)  # Name the unreachable host.
            self.store.mark_failed(root, str(error))  # Record the skip with the host reason.
            self._counters["unreachable"] += 1  # Count it apart from a real failure.
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as error:  # One doc.
            _LOGGER.warning("Document %s failed: %s", root, error)  # Record the failure.
            self.store.mark_failed(root, str(error))  # Mark this document failed.
            self._counters["failed"] += 1  # Count it, and continue the run.

    def _advance(self, row: sqlite3.Row, root: str) -> None:
        """Resolve, download, and classify one document to a final stage."""
        pdf_url = self._resolved_url(row, root)  # Resolve or reuse the PDF URL.
        if pdf_url is None:  # The document has no PDF or the resolution failed.
            return  # The resolution already recorded a no-PDF or a failed outcome.
        self._pace()  # Wait the polite delay before the download.
        outcome, path, size, reason = self.acquire.downloader.download_document(pdf_url, self._dir_for(row))
        if path is None or size is None:  # The download failed or the body is not a PDF.
            self.store.mark_failed(root, reason or "download failed")  # Mark failed with reason.
            self._counters["failed"] += 1  # Count the failure, and continue.
            return  # A failed download never reaches the classified stage.
        self._counters[outcome] += 1  # Count the download or the skip.
        self.store.mark_downloaded(root, path, size)  # Record the durable download.
        self._classify_content(row, root, path, pdf_url)  # Classify with the real resolved URL.

    def _resolved_url(self, row: sqlite3.Row, root: str) -> str | None:
        """Return the companion PDF URL, resolving it when it is not yet known."""
        if row["resolved_pdf_url"]:  # A prior run already resolved this document.
            return str(row["resolved_pdf_url"])  # Reuse the stored URL, no fresh fetch.
        if row["doc_type"] == DocumentType.DIRECT_PDF.value:  # The source is the PDF.
            self.store.set_resolved(root, root, [PdfCandidate(root, True, "direct-pdf")])  # Direct.
            return root  # A direct PDF resolves to its own URL.
        shared = self._sibling_pdf(root)  # A sibling page answers without a network read.
        if shared is not None:  # Another page in the same folder already resolved.
            self.store.set_resolved(root, shared, [PdfCandidate(shared, True, "same-folder-sibling")])
            return shared  # Reuse the sibling answer, and skip one network request.
        self._pace()  # Wait the polite delay before the resolution fetch.
        chosen, candidates, outcome, reason = self.acquire.resolver.resolve_companion(root)  # Resolve.
        resolved = self._record_resolution(root, chosen, candidates, outcome, reason)  # Record it.
        if resolved is not None:  # Remember the answer for every later sibling page.
            self._folder_pdfs[_folder_of(root)] = resolved  # One entry serves the folder.
        return resolved  # The caller downloads this PDF.

    def _sibling_pdf(self, root: str) -> str | None:
        """Return the PDF that another page in the same folder already resolved to.

        The resolver reads ``<folder>/index.html`` or ``<folder>/__toc.js``, so
        every page in one folder resolves to the same file. An ancestor folder is
        not safe, because a subfolder can hold its own document. The page
        ``hardware/qfx10016/qfx10008/`` resolves to ``qfx10008.pdf``, not to the
        ``qfx10016.pdf`` of its parent, so an ancestor rule would lose a file.
        """
        shared = self._folder_pdfs.get(_folder_of(root))  # An exact folder match only.
        if shared is None:  # No sibling in this folder resolved yet.
            return None  # The caller performs the normal network resolution.
        _LOGGER.debug("Reusing the sibling PDF %s for %s", shared, root)  # Trace the reuse.
        return shared  # The sibling answer is authoritative for this folder.

    def _record_resolution(
        self, root: str, chosen: str | None, candidates: list[PdfCandidate], outcome: ResolveOutcome, reason: str
    ) -> str | None:
        """Record the resolution outcome and return the chosen PDF URL or None."""
        if outcome == ResolveOutcome.RESOLVED:  # The resolver chose a companion PDF.
            self.store.set_resolved(root, str(chosen), candidates)  # Record the choice.
            return chosen  # Proceed to the download.
        if outcome == ResolveOutcome.NO_PDF:  # A live page named no PDF, a clean outcome.
            self.store.mark_no_pdf(root, reason)  # Record the clean no-PDF outcome.
            self._counters["no_pdf"] += 1  # Count it apart from a real failure.
            return None  # There is nothing to download.
        self.store.mark_failed(root, reason)  # A real resolution failure, with the reason.
        self._counters["failed"] += 1  # Count the failure, and continue the run.
        return None  # There is nothing to download.

    def _dir_for(self, row: sqlite3.Row) -> Path:
        """Return the category folder for one document."""
        category = str(row["category"] or UNCATEGORIZED)  # The slug category folder name.
        return self.config.output_dir / _sanitize(category)  # The Windows-safe folder.

    def _classify_content(self, row: sqlite3.Row, root: str, local_path: str, pdf_url: str) -> None:
        """Derive the content sub-category, and place the file with the caller's URL.

        The caller passes the resolved PDF URL. The in-memory row can still hold a
        null URL from before this run resolved the document, so a re-read would
        pass the string "None" to the allocator and build a constant file name.
        """
        if str(row["category"]) != UNCATEGORIZED:  # Only uncategorized needs content.
            self.store.set_classified(root, None, None)  # Finalize a categorized document.
            return  # A categorized document needs no content sample.
        text = self.classify.sampler.sample(Path(local_path))  # In-memory sample only.
        name_hint = Path(local_path).name  # The file name names the product, so it guides the score.
        result = self.classify.scorer.score(text, name_hint)  # Derive the label, discard the text.
        final_path = self._place(local_path, result.sub_category, pdf_url)  # Place with the caller's real URL.
        self.store.mark_downloaded(root, str(final_path), final_path.stat().st_size)  # Update.
        self.store.record_scores(root, _score_rows(result))  # Persist the numeric scores.
        self.store.set_classified(root, result.sub_category, result.is_fallback)  # Finalize.

    def _place(self, local_path: str, label: str, resolved_url: str) -> Path:
        """Move an uncategorized file into its label folder without destroying a file."""
        source = Path(local_path)  # The current file path in the uncategorized folder.
        final_dir = self.config.output_dir / UNCATEGORIZED / _sanitize(label)  # Label folder.
        final_dir.mkdir(parents=True, exist_ok=True)  # Ensure the sub-category folder.
        target = final_dir / source.name  # The preferred final path under the label.
        if source.resolve() == target.resolve():  # The file already sits at the final path.
            return target  # A repeated placement needs no move, so the file stays.
        final, move = self._allocator.plan_file(target, resolved_url, source)  # Resolve the path.
        self._relocate(source, final, move)  # Move the file or drop the redundant duplicate.
        return final  # The runner records this real final path in the store.

    def _relocate(self, source: Path, final: Path, move: bool) -> None:
        """Move the source to the final path, or drop it when a copy already exists."""
        if move:  # The final path is free, so this is a distinct document.
            _LOGGER.info("Placing %s at %s", source.name, final)  # Log before the move.
            shutil.move(str(source), str(final))  # Move the file into the unique label path.
            _LOGGER.debug("Placed the file at %s", final)  # Report the completed move.
            return  # The distinct document now lives at its own path.
        _LOGGER.info("Dropping the redundant duplicate %s", source.name)  # Log before the delete.
        source.unlink()  # Remove the redundant download, so one stored file remains.
        _LOGGER.debug("Dropped the redundant duplicate of %s", final.name)  # One stored file remains.

    def _pace(self) -> None:
        """Wait so at least the configured delay passes between two requests."""
        wait = self.config.tuning.delay_seconds - (time.monotonic() - self._last_request)
        if wait > 0:  # The last request was too recent.
            _LOGGER.debug("Pacing the crawl for %.2f seconds", wait)  # Trace the wait.
            time.sleep(wait)  # Wait the remaining delay to stay polite.
        self._last_request = time.monotonic()  # Record the time of this request.

    def _write_manifest(self) -> None:
        """Render the manifest JSON and CSV from the store."""
        writer = ManifestWriter(self.store, self.config.output_dir)  # Build the writer.
        json_path, csv_path = writer.write()  # Render both manifest files.
        _LOGGER.info("Manifest written to %s and %s", json_path, csv_path)  # Report paths.

    def _print_summary(self) -> None:
        """Print the final summary with the counts and the total bytes."""
        summary = self.store.summary()  # The stage, category, and sub-category counts.
        _LOGGER.info("Summary by category: %s", summary["category"])  # Category counts.
        _LOGGER.info("Summary by sub-category: %s", summary["sub_category"])  # Label counts.
        _LOGGER.info(
            "Downloaded=%d skipped=%d no_pdf=%d failed=%d unreachable=%d dropped=%d total_bytes=%s",
            self._counters["downloaded"],
            self._counters["skipped"],
            self._counters["no_pdf"],
            self._counters["failed"],
            self._counters["unreachable"],
            self._counters["dropped"],
            summary["total_bytes"],
        )
        self._report_unreachable_hosts()  # Name every host that never answered.

    def _report_unreachable_hosts(self) -> None:
        """Log each host that the circuit breaker flagged as unreachable."""
        client = self.acquire.downloader.client  # The client owns the circuit breaker state.
        hosts = sorted(getattr(client, "unreachable_hosts", ()))  # A test fake may omit it.
        if not hosts:  # Every host answered, so there is nothing to report.
            return  # Keep the summary short when no host failed.
        _LOGGER.warning("Unreachable hosts: %d", len(hosts))  # State the count first.
        for host in hosts:  # Name each host so an operator can retry from another network.
            _LOGGER.warning("Host %s never answered, so its files were skipped", host)


def _parser() -> argparse.ArgumentParser:
    """Return the argument parser with a safe default for each option."""
    parser = argparse.ArgumentParser(description="Harvest the Juniper documentation corpus")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))  # Output root.
    parser.add_argument("--delay-seconds", type=float, default=1.0)  # Polite delay.
    parser.add_argument("--timeout-seconds", type=int, default=90)  # Request timeout.
    parser.add_argument("--max-sample-pages", type=int, default=8)  # Sample page cap.
    parser.add_argument("--confidence-threshold", type=float, default=0.25)  # Label floor.
    parser.add_argument("--tls-mode", choices=("auto", "verify", "insecure"), default="auto")
    parser.add_argument("--retry-failed", action="store_true")  # Reprocess failed rows.
    parser.add_argument("--sitemap-source", default=DEFAULT_INDEX_URL)  # Index or subset.
    parser.add_argument(
        "--source", choices=_SOURCE_CHOICES, default=SOURCE_DOCUMENTATION
    )  # Which corpus to harvest; documentation keeps the existing default behavior.
    parser.add_argument("--marketing-sitemap-source", default=DEFAULT_MARKETING_URL)  # Marketing.
    return parser  # The caller parses the process arguments.


def _folder_of(url: str) -> str:
    """Return the folder of one document URL, which keys the sibling PDF map."""
    trimmed = url.rstrip("/")  # A directory URL and a page URL must key the same.
    if trimmed.lower().endswith(".html"):  # A page URL carries a file name to drop.
        return trimmed.rsplit("/", 1)[0]  # The folder holds the shared TOC script.
    return trimmed  # A directory URL is already the folder.


def _sanitize(name: str) -> str:
    """Return a Windows-safe folder name for one category or label."""
    cleaned = _INVALID_NAME.sub("-", name)  # Replace each invalid character.
    cleaned = cleaned.strip(" .")  # Trim a trailing dot or space.
    return cleaned or "unnamed"  # Never return an empty folder name.


def _score_rows(result: ContentAnalysisResult) -> list[tuple[str, str, float]]:
    """Return the store rows for one content analysis result."""
    rows: list[tuple[str, str, float]] = []  # The signal group, name, and score triples.
    for key, score in result.scores.items():  # Split each group-and-name key.
        group, name = key.split(":", 1)  # The key joins the group and the signal name.
        rows.append((group, name, score))  # Add one row per detected signal.
    return rows  # The store records these numeric scores, never any body text.


if __name__ == "__main__":
    raise SystemExit(HarvestRunner(HarvestConfig.from_args()).run())  # Run as a script.
