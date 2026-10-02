"""Keep every canonical alias readable through harvesting and path consumers."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.juniper_docs.classify.content_sampler import ContentSampler
from src.juniper_docs.classify.manual_sorter import ManualDocumentSorter
from src.juniper_docs.classify.reclassifier import CorpusReclassifier
from src.juniper_docs.harvest.runner import HarvestConfig, HarvestRunner, TuningConfig
from src.juniper_docs.harvest.state_store import HarvestStateStore, StateStoreError
from src.juniper_docs.models import ContentAnalysisResult
from tests.unit.juniper_docs.conftest import FakeCatalogClient

if TYPE_CHECKING:
    from tests.unit.juniper_docs.canonical.conftest import SmallCorpusHarness


class OriginalPdf:
    """Construct a small original PDF for the real existing parser."""

    @staticmethod
    def build() -> bytes:
        """Create one page of original synthetic text with complete PDF structure."""
        text = b"BT /F1 12 Tf 72 720 Td (Original synthetic corpus validation text.) Tj ET\n"
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"endstream",
        ]
        result = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, contents in enumerate(objects, start=1):
            offsets.append(len(result))
            result.extend(str(index).encode() + b" 0 obj\n" + contents + b"\nendobj\n")
        xref = len(result)
        result.extend(b"xref\n0 6\n0000000000 65535 f \n")
        for offset in offsets[1:]:
            result.extend(f"{offset:010d} 00000 n \n".encode())
        result.extend(b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n")
        return bytes(result)

    @staticmethod
    def seed_shared(corpus: SmallCorpusHarness) -> tuple[tuple[str, str], Path, bytes]:
        """Record two original names and labels against one complete payload."""
        roots = ("https://example.test/a/", "https://example.test/b/")
        urls = ("https://example.test/a/alpha-config.pdf", "https://example.test/b/beta-hardware.pdf")
        payload = OriginalPdf.build()
        for root, url in zip(roots, urls, strict=True):
            corpus.seed(root, url, "uncategorized")
            corpus.client.payloads[url] = payload
            result = corpus.downloader.download_document(url, corpus.root / "uncategorized")
            corpus.persist_success(root, result)
            corpus.store.set_classified(root, "old-label", False)
        canonical = corpus.root / "uncategorized" / "alpha-config.pdf"
        canonical.chmod(0o640)
        return roots, canonical, payload


class AliasScorer:
    """Select independent labels from each original URL name."""

    def __init__(self) -> None:
        """Observe every name supplied to the real classification consumer."""
        self.names: list[str] = []

    def score(self, text: str, source_name: str = "") -> ContentAnalysisResult:
        """Return derived metadata only, without retaining the sampled body."""
        self.names.append(source_name)
        label = "alpha-label" if source_name.startswith("alpha") else "beta-label"
        return ContentAnalysisResult(label, ("synthetic",), {"technology_domain:synthetic": 1.0}, False)


class TestSharedPathConsumers:
    """Exercise real parser, state, and physical path operations."""

    def test_reclassification_keeps_canonical_file_and_independent_alias_labels(
        self, corpus: SmallCorpusHarness
    ) -> None:
        """Shared payloads stay in place while each original name controls its label."""
        roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        before = canonical.stat()
        scorer = AliasScorer()
        stats = CorpusReclassifier(corpus.root, ContentSampler(), scorer, dry_run=False).run()
        rows = corpus.store.document_rows()
        assert (stats.inspected, stats.changed, stats.unchanged, stats.unreadable) == (2, 2, 0, 0)
        assert scorer.names == ["alpha-config.pdf", "beta-hardware.pdf"]
        assert [row["root_url"] for row in rows] == list(roots)
        assert [row["sub_category"] for row in rows] == ["alpha-label", "beta-label"]
        assert [row["local_path"] for row in rows] == [str(canonical)] * 2
        assert canonical.read_bytes() == payload
        assert canonical.stat().st_mtime_ns == before.st_mtime_ns
        assert stat.S_IMODE(canonical.stat().st_mode) == 0o640
        assert list(corpus.root.rglob("*.pdf")) == [canonical]
        assert all(row["original_pdf_name"] in scorer.names for row in rows)

    def test_manual_sort_moves_one_payload_and_updates_all_aliases(self, corpus: SmallCorpusHarness) -> None:
        """One physical move keeps every source path valid and the second pass is unchanged."""
        roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        sorter = ManualDocumentSorter(corpus.root, apply_changes=True)
        first = sorter.run(corpus.store.db_path)
        target = corpus.root / "configuration-guides" / "alpha-config.pdf"
        assert (first.inspected, first.moved, first.unsorted, first.missing) == (2, 1, 0, 0)
        rows = corpus.store.document_rows()
        assert [row["root_url"] for row in rows] == list(roots)
        assert [row["local_path"] for row in rows] == [str(target)] * 2
        assert [row["original_pdf_name"] for row in rows] == ["alpha-config.pdf", "beta-hardware.pdf"]
        assert target.read_bytes() == payload
        assert not canonical.exists()
        assert stat.S_IMODE(target.stat().st_mode) == 0o640
        assert list(corpus.root.rglob("*.pdf")) == [target]
        url = "https://example.test/b/beta-hardware.pdf"
        requests = list(corpus.client.requests)
        assert corpus.downloader.download_document(url, corpus.root / "other") == (
            "skipped",
            str(target),
            len(payload),
            None,
        )
        assert corpus.client.requests == requests
        assert corpus.payload_writes.call_count == 1
        before = [dict(row) for row in rows]
        second = sorter.run(corpus.store.db_path)
        assert (second.inspected, second.moved, second.missing) == (2, 0, 0)
        assert [dict(row) for row in corpus.store.document_rows()] == before
        assert target.read_bytes() == payload
        for entries in corpus.render_manifests():
            assert [row["local_path"] for row in entries] == [str(target)] * 2

    @pytest.mark.parametrize("consumer", ["manual", "reclassify"])
    def test_default_dry_run_preserves_payload_and_state(self, corpus: SmallCorpusHarness, consumer: str) -> None:
        """A dry run changes no document, cache, payload, or schema version."""
        _roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        rows = [dict(row) for row in corpus.store.document_rows()]
        cache = [dict(row) for row in corpus.store.content_rows(str(corpus.root.resolve()))]
        before = canonical.stat()
        if consumer == "manual":
            result = ManualDocumentSorter(corpus.root).run(corpus.store.db_path)
            assert result.moved == 1
        else:
            result = CorpusReclassifier(corpus.root, ContentSampler(), AliasScorer()).run()
            assert result.changed == 2
        assert [dict(row) for row in corpus.store.document_rows()] == rows
        assert [dict(row) for row in corpus.store.content_rows(str(corpus.root.resolve()))] == cache
        assert canonical.read_bytes() == payload
        assert canonical.stat().st_mtime_ns == before.st_mtime_ns
        assert stat.S_IMODE(canonical.stat().st_mode) == 0o640
        assert list(corpus.root.rglob("*.db.bak*")) == []

    def test_failed_manual_transaction_restores_the_source_and_all_pointers(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A pre-commit failure keeps the original readable path for every alias."""
        _roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        before = [dict(row) for row in corpus.store.document_rows()]
        monkeypatch.setattr(
            HarvestStateStore, "relocate_content", MagicMock(side_effect=StateStoreError("Synthetic placement lock."))
        )
        with pytest.raises(StateStoreError, match="Synthetic placement lock"):
            ManualDocumentSorter(corpus.root, apply_changes=True).run(corpus.store.db_path)
        assert canonical.read_bytes() == payload
        assert [dict(row) for row in corpus.store.document_rows()] == before
        assert list(corpus.root.rglob("*.pdf")) == [canonical]

    def test_novel_url_after_sort_uses_the_existing_digest_index_without_a_walk(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A live allocator finds a consumer's moved payload before another write."""
        _roots, _canonical, payload = OriginalPdf.seed_shared(corpus)
        ManualDocumentSorter(corpus.root, apply_changes=True).run(corpus.store.db_path)
        url = "https://example.test/c/third.pdf"
        corpus.seed(url, url, "design")
        corpus.client.payloads[url] = payload
        with monkeypatch.context() as faults:
            faults.setattr(
                Path, "rglob", MagicMock(side_effect=AssertionError("A download cannot repeat corpus discovery."))
            )
            faults.setattr(
                PdfPathAllocator,
                "_digest_file",
                MagicMock(side_effect=AssertionError("A moved validated payload must not repeat its hash.")),
            )
            result = corpus.downloader.download_document(url, corpus.root / "design")
        final = corpus.root / "configuration-guides" / "alpha-config.pdf"
        assert result == ("skipped", str(final), len(payload), None)
        assert final.read_bytes() == payload
        assert corpus.payload_writes.call_count == 1
        assert len(corpus.client.requests) == 3
        assert [row["local_path"] for row in corpus.store.document_rows()] == [str(final)] * 3


class OfflineScope:
    """Construct local sitemap inputs for every existing crawl source."""

    def __init__(self, tmp_path: Path, source: str) -> None:
        """Provide original PDF bytes and local-only responses for all scopes."""
        self.pdfs = (
            "https://www.juniper.net/documentation/us/en/software/synthetic/configuration/alpha.pdf",
            "https://www.juniper.net/assets/synthetic/datasheet-beta.pdf",
            "https://www.juniper.net/documentation/us/en/hardware/synthetic/gamma.pdf",
            "https://www.juniper.net/documentation/us/en/software/synthetic/configuration/delta.pdf",
        )
        self.landing = "https://www.juniper.net/documentation/product/synthetic-fixture/"
        documentation = self._sitemap(tmp_path / "documentation.xml", [self.pdfs[0], self.landing])
        marketing = self._sitemap(tmp_path / "marketing.xml", list(self.pdfs[:2]))
        html = "".join(f'<a href="{url}">Original fixture PDF</a>' for url in self.pdfs[2:])
        self.client = FakeCatalogClient(
            texts={self.landing: html}, payloads=dict.fromkeys(self.pdfs, OriginalPdf.build())
        )
        self.config = HarvestConfig(
            tmp_path / "corpus",
            documentation,
            "verify",
            False,
            TuningConfig(delay_seconds=0),
            source=source,
            marketing_source=marketing,
        )

    @staticmethod
    def _sitemap(path: Path, urls: list[str]) -> str:
        """Write a local original sitemap rather than reading a remote corpus."""
        locations = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
        path.write_text(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + locations + "</urlset>", encoding="utf-8"
        )
        return str(path)


class TestWholeHarvest:
    """Prove discovery scopes and final-document resume through the actual runner."""

    @pytest.mark.parametrize(
        ("source", "root_count", "fetch_count"),
        [("documentation", 2, 2), ("marketing", 2, 2), ("product-landing", 2, 2), ("both", 3, 3), ("all", 5, 4)],
    )
    def test_all_scopes_share_equal_payloads_without_losing_inventory(
        self, tmp_path: Path, source: str, root_count: int, fetch_count: int
    ) -> None:
        """The source selection changes inventory, not the global content policy."""
        scope = OfflineScope(tmp_path, source)
        runner = HarvestRunner(scope.config, client=scope.client)
        assert runner.run() == 0
        entries = json.loads((scope.config.output_dir / "manifest.json").read_text(encoding="utf-8"))
        assert len(entries) == root_count
        assert {entry["status"] for entry in entries} == {"classified"}
        paths = {entry["local_path"] for entry in entries}
        assert len(paths) == 1
        canonical = Path(next(iter(paths)))
        assert canonical.read_bytes() == OriginalPdf.build()
        assert list(scope.config.output_dir.rglob("*.pdf")) == [canonical]
        assert runner._counters["downloaded"] == 1
        assert runner._counters["skipped"] == root_count - 1
        assert runner._counters["failed"] == 0
        assert sum(url in scope.pdfs for url in scope.client.requests) == fetch_count
        assert all(
            entry["original_pdf_name"] in {"alpha.pdf", "datasheet-beta.pdf", "gamma.pdf", "delta.pdf"}
            for entry in entries
        )

    def test_final_document_resume_recovers_missing_canonical_for_all_roots(self, tmp_path: Path) -> None:
        """A classified stage cannot conceal a deleted payload during restart."""
        scope = OfflineScope(tmp_path, "all")
        assert HarvestRunner(scope.config, client=scope.client).run() == 0
        entries = json.loads((scope.config.output_dir / "manifest.json").read_text(encoding="utf-8"))
        Path(entries[0]["local_path"]).unlink()
        scope.client.requests.clear()
        second = HarvestRunner(scope.config, client=scope.client)
        assert second.run() == 0
        repaired = json.loads((scope.config.output_dir / "manifest.json").read_text(encoding="utf-8"))
        assert {entry["source_url"] for entry in repaired} == {entry["source_url"] for entry in entries}
        assert {entry["status"] for entry in repaired} == {"classified"}
        paths = {entry["local_path"] for entry in repaired}
        assert len(paths) == 1
        assert Path(next(iter(paths))).read_bytes() == OriginalPdf.build()
        assert len(scope.client.requests) == 1
        assert scope.client.requests[0] in scope.pdfs
        assert second._counters["downloaded"] == 1
        assert second._counters["skipped"] == 4

    def test_state_failure_stops_before_success_counters(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A required association failure cannot increase download or skip counters."""
        scope = OfflineScope(tmp_path, "marketing")
        runner = HarvestRunner(scope.config, client=scope.client)
        monkeypatch.setattr(
            runner.store, "associate_content", MagicMock(side_effect=StateStoreError("Synthetic receipt failure."))
        )
        assert runner.run() == 1
        assert runner._counters["downloaded"] == 0
        assert runner._counters["skipped"] == 0
        with HarvestStateStore(scope.config.output_dir / "harvest_state.db") as store:
            assert {row["stage"] for row in store.document_rows()} <= {"discovered", "resolved"}
            assert all(row["local_path"] is None for row in store.document_rows())


class TestPlacementFailureDecisions:
    """Prove coupled failure and collision behavior with original local files."""

    @pytest.mark.parametrize("kind", ["missing", "unsorted", "collision"])
    def test_manual_sort_reports_missing_and_unsorted_or_preserves_collisions(
        self, corpus: SmallCorpusHarness, kind: str
    ) -> None:
        """A path outcome never deletes an original or invents a successful move."""
        root = "https://example.test/configuration/" if kind == "collision" else "https://example.test/opaque/"
        url = "https://example.test/original/report.pdf"
        corpus.seed(root, url, "uncategorized")
        payload = OriginalPdf.build()
        corpus.client.payloads[url] = payload
        result = corpus.downloader.download_document(url, corpus.root / "uncategorized")
        corpus.persist_success(root, result)
        source = Path(str(result[1]))
        target = corpus.root / "configuration-guides" / "report.pdf"
        if kind == "missing":
            source.unlink()
        elif kind == "collision":
            target.parent.mkdir()
            target.write_bytes(b"%PDF Original independent collision.")
        stats = ManualDocumentSorter(corpus.root, apply_changes=True).run(corpus.store.db_path)
        if kind == "collision":
            final = target.with_name("report-2.pdf")
            assert (stats.moved, stats.missing, stats.unsorted) == (1, 0, 0)
            assert target.read_bytes() == b"%PDF Original independent collision."
            assert final.read_bytes() == payload
            assert corpus.store.document_rows()[0]["local_path"] == str(final)
        else:
            assert (stats.moved, stats.missing, stats.unsorted) == ((0, 1, 0) if kind == "missing" else (0, 0, 1))
            assert corpus.store.document_rows()[0]["local_path"] == str(source)

    def test_reclassification_failure_leaves_shared_aliases_and_original_payload(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An intended label update cannot hide an uncommitted state failure."""
        _roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        before = [dict(row) for row in corpus.store.document_rows()]
        monkeypatch.setattr(
            HarvestStateStore, "reclassify_document", MagicMock(side_effect=StateStoreError("Synthetic label lock."))
        )
        with pytest.raises(StateStoreError, match="Synthetic label lock"):
            CorpusReclassifier(corpus.root, ContentSampler(), AliasScorer(), dry_run=False).run()
        assert [dict(row) for row in corpus.store.document_rows()] == before
        assert canonical.read_bytes() == payload
        assert list(corpus.root.rglob("*.pdf")) == [canonical]

    def test_equal_content_placement_does_not_delete_a_historical_source(self, corpus: SmallCorpusHarness) -> None:
        """A path operation can rebind aliases without deleting either old copy."""
        _roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        final = corpus.root / "other" / "equal.pdf"
        final.parent.mkdir()
        final.write_bytes(payload)
        config = HarvestConfig(corpus.root, tuning=TuningConfig(delay_seconds=0))
        runner = HarvestRunner(config, client=corpus.client)
        try:
            runner._relocate(canonical, canonical, False)
            runner._relocate(canonical, final, False)
        finally:
            runner.store.close()
        assert canonical.read_bytes() == payload
        assert final.read_bytes() == payload
        assert [row["local_path"] for row in corpus.store.document_rows()] == [str(final)] * 2
        reclassifier = CorpusReclassifier(corpus.root, ContentSampler(), AliasScorer())
        reclassifier._relocate(canonical, canonical, False)
        reclassifier._relocate(canonical, final, False)
        assert canonical.read_bytes() == final.read_bytes() == payload

    def test_runner_precommit_placement_failure_restores_the_only_payload(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failed move transaction retains all old readable alias pointers."""
        _roots, canonical, payload = OriginalPdf.seed_shared(corpus)
        final = corpus.root / "other" / canonical.name
        final.parent.mkdir()
        runner = HarvestRunner(HarvestConfig(corpus.root), client=corpus.client)
        before = [dict(row) for row in corpus.store.document_rows()]
        try:
            monkeypatch.setattr(
                runner.store, "relocate_content", MagicMock(side_effect=StateStoreError("Synthetic move lock."))
            )
            with pytest.raises(StateStoreError, match="Synthetic move lock"):
                runner._relocate(canonical, final, True)
        finally:
            runner.store.close()
        assert canonical.read_bytes() == payload
        assert not final.exists()
        assert [dict(row) for row in corpus.store.document_rows()] == before
