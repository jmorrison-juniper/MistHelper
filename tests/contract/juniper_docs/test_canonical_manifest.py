"""Assert additive manifest fields and durable alias lookup using actual artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from src.juniper_docs.acquire.downloader import CorpusDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.juniper_docs.harvest.manifest_writer import ManifestWriter
from src.juniper_docs.harvest.state_store import HarvestStateStore
from tests.unit.juniper_docs.canonical.conftest import SmallCorpusHarness


class TestCanonicalManifestContract:
    """Preserve every URL's metadata while counting a shared path once."""

    @pytest.mark.parametrize("format_name", ["json", "csv"])
    def test_alias_fields_and_physical_byte_summary(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, format_name: str
    ) -> None:
        """The artifact contains two complete source records and one physical payload."""
        corpus = SmallCorpusHarness(tmp_path / "corpus", monkeypatch)
        try:
            roots, urls, payload = self._seed(corpus)
            json_path, csv_path = ManifestWriter(corpus.store, corpus.root).write()
            if format_name == "json":
                entries = json.loads(json_path.read_text(encoding="utf-8"))
            else:
                with csv_path.open(encoding="utf-8", newline="") as stream:
                    entries = list(csv.DictReader(stream))
            assert [entry["source_url"] for entry in entries] == list(roots)
            assert [entry["resolved_pdf_url"] for entry in entries] == list(urls)
            assert [entry["original_pdf_name"] for entry in entries] == ["alpha.pdf", "beta.pdf"]
            assert [entry["category"] for entry in entries] == ["design", "hardware-guides"]
            assert [entry["content_sha256"] for entry in entries] == [hashlib.sha256(payload).hexdigest()] * 2
            assert [entry["status"] for entry in entries] == ["classified", "classified"]
            canonical = corpus.root / "design" / "alpha.pdf"
            assert [entry["local_path"] for entry in entries] == [str(canonical)] * 2
            assert corpus.store.summary()["total_bytes"] == len(payload)
            assert list(corpus.root.rglob("*.pdf")) == [canonical]
            assert canonical.read_bytes() == payload
            assert corpus.payload_writes.call_count == 1
            assert corpus.client.requests == list(urls)
        finally:
            corpus.store.close()

    @pytest.mark.parametrize("payload", [b"", b'{"broken_json":'])
    def test_invalid_response_has_null_payload_fields_and_a_failed_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: bytes
    ) -> None:
        """The actual downloader rejects an empty body or malformed JSON response."""
        corpus = SmallCorpusHarness(tmp_path / "corpus", monkeypatch)
        try:
            root, url = "https://example.test/source/", "https://example.test/invalid.pdf"
            corpus.seed(root, url, "design")
            corpus.client.payloads[url] = payload
            if payload:
                with pytest.raises(json.JSONDecodeError):
                    json.loads(payload)
            result = corpus.downloader.download_document(url, corpus.root / "design")
            assert result == ("failed", None, None, "permanent: not a PDF")
            corpus.store.mark_failed(root, str(result[3]))
            json_rows, csv_rows = corpus.render_manifests()
            assert (json_rows[0]["status"], json_rows[0]["error_reason"]) == ("failed", "permanent: not a PDF")
            for field in ("local_path", "file_size", "content_sha256"):
                assert json_rows[0][field] is None
                assert csv_rows[0][field] == ""
            assert json_rows[0]["original_pdf_name"] == "invalid.pdf"
            assert json_rows[0]["resolved_pdf_url"] == url
            assert corpus.payload_writes.call_count == 0
            assert list(corpus.root.rglob("*.pdf")) == []
        finally:
            corpus.store.close()

    @staticmethod
    def _seed(corpus: SmallCorpusHarness) -> tuple[tuple[str, str], tuple[str, str], bytes]:
        """Create independent natural roots, candidates, and categories."""
        roots = ("https://example.test/source/a/", "https://example.test/source/b/")
        urls = ("https://example.test/a/alpha.pdf", "https://example.test/b/beta.pdf")
        payload = b"%PDF-1.4\nOriginal contract payload without parser assumptions.\n"
        for root, url, category in zip(roots, urls, ("design", "hardware-guides"), strict=True):
            corpus.seed(root, url, category)
            corpus.client.payloads[url] = payload
            result = corpus.downloader.download_document(url, corpus.root / category)
            corpus.persist_success(root, result)
        return roots, urls, payload

    def test_restart_maps_both_urls_to_the_manifest_path_without_fetch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A new allocator finds every persisted alias independently of its category."""
        corpus = SmallCorpusHarness(tmp_path / "corpus", monkeypatch)
        try:
            roots, urls, payload = self._seed(corpus)
            before = [dict(row) for row in corpus.store.document_rows()]
            corpus.store.close()
            corpus.store = HarvestStateStore(corpus.root / "harvest_state.db")
            corpus.client.payloads.clear()
            corpus.client.requests.clear()
            downloader = CorpusDownloader(
                corpus.client, corpus.root, PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
            )
            canonical = corpus.root / "design" / "alpha.pdf"
            for url in urls:
                assert downloader.download_document(url, corpus.root / "unrelated") == (
                    "skipped",
                    str(canonical),
                    len(payload),
                    None,
                )
            assert [dict(row) for row in corpus.store.document_rows()] == before
            assert [row["root_url"] for row in corpus.store.document_rows()] == list(roots)
            assert corpus.client.requests == []
            assert corpus.payload_writes.call_count == 1
            assert canonical.read_bytes() == payload
        finally:
            corpus.store.close()

    def test_manifest_retains_previous_fields_and_has_no_body_storage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The new fields extend the contract without replacing existing provenance."""
        corpus = SmallCorpusHarness(tmp_path / "corpus", monkeypatch)
        try:
            self._seed(corpus)
            json_rows, csv_rows = corpus.render_manifests()
            expected = {
                "source_url",
                "resolved_pdf_url",
                "category",
                "sub_category",
                "local_path",
                "file_size",
                "status",
                "chosen_pdf",
                "rejected_candidates",
                "drop_reason",
                "error_reason",
                "content_sha256",
                "original_pdf_name",
            }
            assert set(json_rows[0]) == expected
            assert set(csv_rows[0]) == expected
            assert json_rows[0]["rejected_candidates"] == ["https://example.test/a/alpha-alternate.pdf"]
            assert csv_rows[0]["rejected_candidates"] == "https://example.test/a/alpha-alternate.pdf"
            assert "Original contract payload" not in json.dumps(json_rows)
            for table in (
                "documents",
                "pdf_candidates",
                "content_scores",
                "dropped_release_notes",
                "run_meta",
                "content_cache",
            ):
                columns = {row[1] for row in corpus.store._conn.execute(f"PRAGMA table_info({table})")}
                assert not {"text", "body", "payload", "body_text"}.intersection(columns)
        finally:
            corpus.store.close()
