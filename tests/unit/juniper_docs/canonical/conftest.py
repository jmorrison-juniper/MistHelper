"""Provide a small temporary corpus with real state, downloads, and manifests."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import urlsplit

import pytest

from src.juniper_docs.acquire.downloader import CorpusDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.juniper_docs.harvest.manifest_writer import ManifestWriter
from src.juniper_docs.harvest.state_store import HarvestStateStore
from src.juniper_docs.models import DocumentType, InventoryRecord, PdfCandidate
from tests.unit.juniper_docs.conftest import FakeCatalogClient

type DownloadResult = tuple[str, str | None, int | None, str | None]
type RenderedManifests = tuple[list[dict[str, object]], list[dict[str, str]]]


class SmallCorpusHarness:
    """Own the temporary corpus and preserve each natural URL record."""

    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Open real state and observe actual atomic payload writes."""
        self.root = root
        self.store = HarvestStateStore(root / "harvest_state.db")
        self.client = FakeCatalogClient()
        allocator = PdfPathAllocator(self.store.owner_of_path, self.store)
        self.downloader = CorpusDownloader(self.client, root, allocator)
        self.payload_writes = MagicMock(wraps=CorpusDownloader._atomic_write)
        monkeypatch.setattr(CorpusDownloader, "_atomic_write", staticmethod(self.payload_writes))

    def seed(self, root_url: str, pdf_url: str, category: str) -> None:
        """Record an independent root, category, and resolved candidate history."""
        record = InventoryRecord(root_url, urlsplit(root_url).path.rstrip("/"), DocumentType.HTML_ROOT)
        alternate_url = pdf_url.removesuffix(".pdf") + "-alternate.pdf"
        candidates = [
            PdfCandidate(pdf_url, True, "The synthetic candidate was selected."),
            PdfCandidate(alternate_url, False, "The synthetic alternate was rejected."),
        ]
        self.store.add_document(record)
        self.store.set_category(root_url, category)
        self.store.set_resolved(root_url, pdf_url, candidates)

    def persist_success(self, root_url: str, result: DownloadResult) -> None:
        """Persist the returned path for every successful alias, including skips."""
        outcome, local_path, size, reason = result
        if outcome not in ("downloaded", "skipped") or local_path is None or size is None or reason is not None:
            raise AssertionError("A failed download cannot create a successful alias.")
        self.store.mark_downloaded(root_url, local_path, size)
        self.store.set_classified(root_url, None, None)

    def render_manifests(self) -> RenderedManifests:
        """Render both actual manifests and read their stored rows."""
        json_path, csv_path = ManifestWriter(self.store, self.root).write()
        json_rows: list[dict[str, object]] = json.loads(json_path.read_text(encoding="utf-8"))
        with csv_path.open("r", encoding="utf-8", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        return json_rows, csv_rows


@pytest.fixture
def corpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[SmallCorpusHarness]:
    """Inject one isolated corpus and close its state even when an assertion fails."""
    harness = SmallCorpusHarness(tmp_path / "corpus", monkeypatch)
    try:
        yield harness
    finally:
        harness.store.close()
