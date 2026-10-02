"""Measure canonical lookup, restart work, and changes to real stored files."""

from __future__ import annotations

import ctypes
import hashlib
import os
import sys
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, BinaryIO
from unittest.mock import MagicMock

import pytest

from src.juniper_docs.acquire.downloader import CorpusDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.juniper_docs.harvest.state_store import HarvestStateStore

if TYPE_CHECKING:
    from tests.unit.juniper_docs.canonical.conftest import SmallCorpusHarness


class TestCanonicalIndex:
    """Exercise actual file recovery and valid URL aliases."""

    @staticmethod
    def seed_pair(corpus: SmallCorpusHarness) -> tuple[tuple[str, str], tuple[str, str], bytes, Path]:
        """Create two independent names for one original payload."""
        roots = ("https://example.test/docs/a/", "https://example.test/docs/b/")
        urls = ("https://example.test/first/alpha.pdf", "https://example.test/second/beta.pdf")
        payload = b"%PDF-1.4\nOriginal canonical index payload.\n"
        for root, url, category in zip(roots, urls, ("design", "hardware-guides"), strict=True):
            corpus.seed(root, url, category)
            corpus.client.payloads[url] = payload
            result = corpus.downloader.download_document(url, corpus.root / category)
            corpus.persist_success(root, result)
        return roots, urls, payload, corpus.root / "design" / "alpha.pdf"

    def test_restart_reuses_every_alias_without_fetch_or_hash(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Persisted aliases reuse the real payload without another hash pass."""
        roots, urls, payload, canonical = self.seed_pair(corpus)
        corpus.store.close()
        corpus.store = HarvestStateStore(corpus.root / "harvest_state.db")
        hash_spy = MagicMock(side_effect=AssertionError("An unchanged restart must not hash a stored payload."))
        monkeypatch.setattr(PdfPathAllocator, "_digest_file", staticmethod(hash_spy))
        allocator = PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
        corpus.downloader = CorpusDownloader(corpus.client, corpus.root, allocator)
        corpus.client.payloads.clear()
        corpus.client.requests.clear()
        for root, url in zip(roots, urls, strict=True):
            result = corpus.downloader.download_document(url, corpus.root / "another-category")
            assert result == ("skipped", str(canonical), len(payload), None)
            assert corpus.store.stage_of(root) == "classified"
        assert corpus.client.requests == []
        assert corpus.payload_writes.call_count == 1
        assert hash_spy.call_count == 0
        assert len(corpus.store.content_rows(str(corpus.root.resolve()))) == 1
        assert [row["local_path"] for row in corpus.store.document_rows()] == [str(canonical)] * 2

    def test_missing_payload_repairs_both_aliases(self, corpus: SmallCorpusHarness) -> None:
        """A new verified write repairs every pointer without losing source metadata."""
        roots, urls, payload, canonical = self.seed_pair(corpus)
        canonical.unlink()
        result = corpus.downloader.download_document(urls[1], corpus.root / "hardware-guides")
        repaired = corpus.root / "hardware-guides" / "beta.pdf"
        assert result == ("downloaded", str(repaired), len(payload), None)
        rows = corpus.store.document_rows()
        assert [row["root_url"] for row in rows] == list(roots)
        assert [row["local_path"] for row in rows] == [str(repaired)] * 2
        assert [row["category"] for row in rows] == ["design", "hardware-guides"]
        assert [row["original_pdf_name"] for row in rows] == ["alpha.pdf", "beta.pdf"]
        assert repaired.read_bytes() == payload
        assert corpus.client.requests == [*urls, urls[1]]
        assert corpus.payload_writes.call_count == 2
        assert list(corpus.root.rglob("*.pdf")) == [repaired]

    def test_same_size_corruption_with_restored_mtime_never_skips(self, corpus: SmallCorpusHarness) -> None:
        """Change time detects different bytes even when size and modification time match."""
        roots, urls, payload, canonical = self.seed_pair(corpus)
        before = canonical.stat()
        damaged = b"%PDF" + b"x" * (len(payload) - 4)
        canonical.write_bytes(damaged)
        os.utime(canonical, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = canonical.stat()
        assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)
        assert after.st_ctime_ns != before.st_ctime_ns
        result = corpus.downloader.download_document(urls[0], canonical.parent)
        recovered = canonical.with_name(f"alpha-{PdfPathAllocator._short_hash(urls[0])}.pdf")
        assert result == ("downloaded", str(recovered), len(payload), None)
        assert canonical.read_bytes() == damaged
        assert recovered.read_bytes() == payload
        assert [row["local_path"] for row in corpus.store.document_rows()] == [str(recovered)] * len(roots)
        assert corpus.client.requests == [*urls, urls[0]]
        assert corpus.payload_writes.call_count == 2
        assert set(corpus.root.rglob("*.pdf")) == {canonical, recovered}

    def test_allocator_does_not_share_content_across_corpus_roots(
        self, corpus: SmallCorpusHarness, tmp_path: Path
    ) -> None:
        """A corpus binding cannot silently include another output root."""
        allocator = corpus.downloader._allocator
        with pytest.raises(ValueError, match="two corpus roots"):
            allocator.index_corpus(tmp_path / "another-corpus")
        assert allocator._cache.root == corpus.root.resolve()
        assert list(corpus.root.rglob("*.pdf")) == []


class TestHashWork:
    """Count actual discovery, fetched hashes, stored hashes, and writes."""

    def test_many_distinct_url_aliases_do_not_repeat_the_corpus_walk(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One thousand requests publish twenty payloads with bounded stored hash work."""
        observations = self._observe(monkeypatch, corpus)
        payloads = [b"%PDF-1.4\n" + str(index).encode().ljust(8183, b".") for index in range(20)]
        with MemoryMeasure() as memory:
            for index in range(1000):
                url = f"https://example.test/{index}/document-{index}.pdf"
                corpus.seed(url, url, f"category-{index % 7}")
                corpus.client.payloads[url] = payloads[index % 20]
                result = corpus.downloader.download_document(url, corpus.root / f"category-{index % 7}")
                assert result[0] == ("downloaded" if index < 20 else "skipped")
                assert result[2:] == (len(payloads[index % 20]), None)
                corpus.persist_success(url, result)
        assert memory.peak < 64 * 1024 * 1024
        assert observations.walks.call_count == 1
        physical = list(corpus.root.rglob("*.pdf"))
        assert len(physical) == 20
        assert sum(path.stat().st_size for path in physical) == sum(map(len, payloads))
        assert len(corpus.client.requests) == 1000
        assert corpus.payload_writes.call_count == 20
        assert observations.fetched.call_count == 1000
        assert observations.stored.call_count == 20
        assert sum(len(entry.args[0]) for entry in observations.fetched.call_args_list) == 50 * sum(map(len, payloads))
        assert sum(entry.args[0].stat().st_size for entry in observations.stored.call_args_list) == sum(
            map(len, payloads)
        )
        assert len(corpus.store.content_rows(str(corpus.root.resolve()))) == 20
        assert corpus.store.summary()["total_bytes"] == sum(map(len, payloads))
        assert observations.stats.call_count < 512000
        self._assert_restart_work(corpus, observations)

    @staticmethod
    def _assert_restart_work(corpus: SmallCorpusHarness, observations: HashObservations) -> None:
        """Repeat all one thousand aliases after reopening every durable component."""
        corpus.store.close()
        corpus.store = HarvestStateStore(corpus.root / "harvest_state.db")
        for observer in (observations.walks, observations.fetched, observations.stored):
            observer.reset_mock()
        corpus.client.requests.clear()
        corpus.client.payloads.clear()
        corpus.downloader = CorpusDownloader(
            corpus.client, corpus.root, PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
        )
        rows = corpus.store.document_rows()
        for row in rows:
            result = corpus.downloader.download_document(str(row["resolved_pdf_url"]), corpus.root / "resume")
            assert result == ("skipped", row["local_path"], row["file_size"], None)
        assert len(rows) == 1000
        assert {row["stage"] for row in rows} == {"classified"}
        assert observations.walks.call_count == 1
        assert observations.fetched.call_count == 0
        assert observations.stored.call_count == 0
        assert corpus.client.requests == []
        assert corpus.payload_writes.call_count == 20

    @staticmethod
    def _observe(monkeypatch: pytest.MonkeyPatch, corpus: SmallCorpusHarness) -> HashObservations:
        """Observe real operations without replacing their results."""
        original_walk = Path.rglob
        walks = MagicMock(wraps=original_walk)
        monkeypatch.setattr(Path, "rglob", lambda path, pattern: walks(path, pattern))
        fetched = MagicMock(wraps=PdfPathAllocator._digest_bytes)
        stored = MagicMock(wraps=PdfPathAllocator._digest_file)
        stats = FileStatMeasure()
        monkeypatch.setattr(PdfPathAllocator, "_digest_bytes", staticmethod(fetched))
        monkeypatch.setattr(PdfPathAllocator, "_digest_file", staticmethod(stored))
        monkeypatch.setattr(os, "stat", stats.stat)
        monkeypatch.setattr(os, "lstat", stats.lstat)
        monkeypatch.setattr(os, "fstat", stats.fstat)
        allocator = PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
        corpus.downloader = CorpusDownloader(corpus.client, corpus.root, allocator)
        return HashObservations(walks, fetched, stored, stats)

    def test_streamed_hash_never_requests_more_than_one_mebibyte(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The actual stored-file hasher uses bounded reads for a larger payload."""
        path = tmp_path / "large-original.pdf"
        payload = b"%PDF" + b"z" * (3 * 1024 * 1024 + 17)
        path.write_bytes(payload)
        original_open = Path.open
        requests: list[int] = []
        monkeypatch.setattr(
            Path,
            "open",
            lambda source, *arguments, **options: BoundedReader(original_open(source, *arguments, **options), requests),
        )
        with MemoryMeasure() as memory:
            digest = PdfPathAllocator._digest_file(path)
        assert digest == hashlib.sha256(payload).hexdigest()
        assert requests == [1024 * 1024] * 5
        assert memory.peak < 3 * 1024 * 1024

    def test_unchanged_body_with_changed_identity_rehashes_once(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A metadata change requires one verification hash, not another fetch."""
        _roots, urls, payload, canonical = TestCanonicalIndex.seed_pair(corpus)
        reading = canonical.stat()
        os.utime(canonical, ns=(reading.st_atime_ns, reading.st_mtime_ns + 1000000))
        spy = MagicMock(wraps=PdfPathAllocator._digest_file)
        monkeypatch.setattr(PdfPathAllocator, "_digest_file", staticmethod(spy))
        assert corpus.downloader.download_document(urls[0], canonical.parent) == (
            "skipped",
            str(canonical),
            len(payload),
            None,
        )
        assert spy.call_count == 1
        assert corpus.client.requests == list(urls)
        assert corpus.payload_writes.call_count == 1


class BoundedReader:
    """Observe read sizes on the actual open binary descriptor."""

    def __init__(self, handle: BinaryIO, requests: list[int]) -> None:
        """Retain the real descriptor and a shared read-size record."""
        self.handle = handle
        self.requests = requests

    def __enter__(self) -> BoundedReader:
        """Keep the real open descriptor for identity validation."""
        return self

    def __exit__(self, *_error: object) -> None:
        """Close the real file after hashing or failure."""
        self.handle.close()

    def fileno(self) -> int:
        """Expose the descriptor used by the production identity check."""
        return self.handle.fileno()

    def read(self, size: int) -> bytes:
        """Reject an unbounded read instead of accepting a weak performance proof."""
        self.requests.append(size)
        if size <= 0 or size > 1024 * 1024:
            raise AssertionError("The stored-file hash requested an unbounded read.")
        return self.handle.read(size)


class FileStatMeasure:
    """Count actual Python stat calls without retaining their argument history."""

    def __init__(self) -> None:
        """Keep original functions and one bounded integer count."""
        self.call_count = 0
        self.functions: dict[str, Callable[..., os.stat_result]] = {
            "stat": os.stat,
            "lstat": os.lstat,
            "fstat": os.fstat,
        }

    def stat(self, *arguments: object, **options: object) -> os.stat_result:
        """Count the real pathname stat operation."""
        self.call_count += 1
        return self.functions["stat"](*arguments, **options)

    def lstat(self, *arguments: object, **options: object) -> os.stat_result:
        """Count the real link-aware identity operation."""
        self.call_count += 1
        return self.functions["lstat"](*arguments, **options)

    def fstat(self, *arguments: object, **options: object) -> os.stat_result:
        """Count the real descriptor identity operation."""
        self.call_count += 1
        return self.functions["fstat"](*arguments, **options)


@dataclass(frozen=True)
class HashObservations:
    """Keep independent observations of actual fetch, hash, walk, and stat work."""

    walks: MagicMock
    fetched: MagicMock
    stored: MagicMock
    stats: FileStatMeasure


class TestIndexFailures:
    """Require explicit failures for unreadable or unsupported file identities."""

    @pytest.mark.parametrize("boundary", ["stat", "open", "hash"])
    def test_local_permission_failures_never_create_a_successful_receipt(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch, boundary: str
    ) -> None:
        """An injected file failure retains existing aliases and their exact bytes."""
        _roots, urls, payload, canonical = TestCanonicalIndex.seed_pair(corpus)
        before = [dict(row) for row in corpus.store.document_rows()]
        with monkeypatch.context() as faults:
            self._inject_failure(faults, canonical, boundary)
            result = corpus.downloader.download_document(urls[0], canonical.parent)
        assert result == ("failed", None, None, "permanent: local corpus operation failed: Synthetic access denied.")
        assert [dict(row) for row in corpus.store.document_rows()] == before
        assert canonical.read_bytes() == payload
        assert corpus.client.requests == list(urls)
        assert corpus.payload_writes.call_count == 1

    @staticmethod
    def _inject_failure(monkeypatch: pytest.MonkeyPatch, canonical: Path, boundary: str) -> None:
        """Fail one real file boundary without a host-dependent skip."""
        failure = MagicMock(side_effect=PermissionError("Synthetic access denied."))
        if boundary == "hash":
            reading = canonical.stat()
            os.utime(canonical, ns=(reading.st_atime_ns, reading.st_mtime_ns + 1000000))
            monkeypatch.setattr(PdfPathAllocator, "_digest_file", staticmethod(failure))
        else:
            original = Path.lstat if boundary == "stat" else Path.open
            method = "lstat" if boundary == "stat" else "open"
            monkeypatch.setattr(
                Path,
                method,
                lambda path, *arguments, **options: (
                    failure() if path == canonical else original(path, *arguments, **options)
                ),
            )

    def test_unreliable_identity_fails_instead_of_skipping(self, tmp_path: Path) -> None:
        """A host without a usable inode cannot authorize cached success."""
        reading = os.stat_result((0, 0, 0, 1, 0, 0, 10, 0, 0, 0))
        with pytest.raises(OSError, match="reliable corpus file identity"):
            PdfPathAllocator._stat_identity(reading)
        assert reading.st_ino == 0

    def test_outside_category_fails_before_creating_it(self, corpus: SmallCorpusHarness, tmp_path: Path) -> None:
        """A download cannot create an output directory outside its corpus."""
        url = "https://example.test/escape.pdf"
        outside = tmp_path / "outside"
        result = corpus.downloader.download_document(url, outside)
        assert result == (
            "failed",
            None,
            None,
            "permanent: local corpus operation failed: A corpus payload path is outside the corpus root.",
        )
        assert not outside.exists()
        assert corpus.client.requests == []
        assert corpus.payload_writes.call_count == 0


class MemoryMeasure:
    """Measure additional Python allocations during the actual operation."""

    def __init__(self) -> None:
        """Retain an existing tracing state instead of changing other tests."""
        self.tracing = tracemalloc.is_tracing()
        self.baseline = tracemalloc.get_traced_memory()[0] if self.tracing else 0
        self.peak = 0

    def __enter__(self) -> MemoryMeasure:
        """Start measurement without retaining payload samples."""
        if not self.tracing:
            tracemalloc.start()
        tracemalloc.reset_peak()
        return self

    def __exit__(self, *_error: object) -> None:
        """Record peak allocation and restore the previous tracing capability."""
        self.peak = tracemalloc.get_traced_memory()[1] - self.baseline
        if not self.tracing:
            tracemalloc.stop()


class NativeChangeQuery:
    """Emulate the native ABI while the real allocator uses original local files."""

    def __init__(self, ticks: int, success: int = 1) -> None:
        """Store the synthetic native change clock and result."""
        self.ticks = ticks
        self.success = success
        self.calls: list[tuple[int, int, int]] = []

    def __call__(self, handle: int, information_class: int, buffer: object, size: int) -> int:
        """Populate the real ctypes structure through its native pointer."""
        self.calls.append((handle, information_class, size))
        information = ctypes.cast(buffer, ctypes.POINTER(PdfPathAllocator.WindowsFileTimes))
        information.contents.change_time = self.ticks
        return self.success


class TestWindowsChangeClock:
    """Do not substitute Windows creation time for a content-change identity."""

    @staticmethod
    def _install(monkeypatch: pytest.MonkeyPatch, query: NativeChangeQuery) -> None:
        """Provide only the native interfaces that the production code requires."""
        monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(get_osfhandle=lambda descriptor: descriptor))
        library = SimpleNamespace(GetFileInformationByHandleEx=query)
        loader = MagicMock(return_value=library)
        monkeypatch.setattr(ctypes, "WinDLL", loader, raising=False)

    def test_native_change_time_uses_the_correct_structure_and_epoch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The actual native-query code reads a 40-byte FILE_BASIC_INFO structure."""
        query = NativeChangeQuery(116444736000000123)
        self._install(monkeypatch, query)
        assert PdfPathAllocator._windows_change_time(42) == 12300
        assert query.calls == [(42, 0, 40)]
        assert ctypes.sizeof(PdfPathAllocator.WindowsFileTimes) == 40
        assert query.argtypes == [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        assert query.restype is ctypes.c_int

    @pytest.mark.parametrize(("ticks", "success"), [(0, 1), (116444736000000123, 0)])
    def test_missing_native_change_time_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, ticks: int, success: int
    ) -> None:
        """An unsupported filesystem cannot authorize a creation-time cache skip."""
        query = NativeChangeQuery(ticks, success)
        self._install(monkeypatch, query)
        with pytest.raises(OSError, match="cannot provide a Windows FILE_BASIC_INFO change time"):
            PdfPathAllocator._windows_change_time(42)
        assert query.calls == [(42, 0, 40)]

    def test_actual_flow_detects_a_changed_native_clock_with_restored_mtime(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The allocator checks the native clock even when creation time cannot help."""
        query = NativeChangeQuery(116444736000001000)
        with monkeypatch.context() as native:
            self._install(native, query)
            native.setattr(sys, "platform", "win32")
            _roots, urls, payload, canonical = TestCanonicalIndex.seed_pair(corpus)
            before = canonical.stat()
            altered = b"%PDF" + b"v" * (len(payload) - 4)
            canonical.write_bytes(altered)
            os.utime(canonical, ns=(before.st_atime_ns, before.st_mtime_ns))
            query.ticks += 1000
            result = corpus.downloader.download_document(urls[0], canonical.parent)
        expected = canonical.with_name(f"alpha-{PdfPathAllocator._short_hash(urls[0])}.pdf")
        assert result == ("downloaded", str(expected), len(payload), None)
        assert canonical.read_bytes() == altered
        assert expected.read_bytes() == payload
        assert [row["local_path"] for row in corpus.store.document_rows()] == [str(expected)] * 2
        assert corpus.payload_writes.call_count == 2


class TestIndexGuardDecisions:
    """Prove missing capability and invalid input decisions without a network."""

    def test_repeat_index_is_a_noop_and_failed_index_cannot_leave_a_partial_binding(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A second bind makes no walk, and an unreadable first bind remains incomplete."""
        allocator = corpus.downloader._allocator
        walks = MagicMock(side_effect=AssertionError("A repeated bind must not walk the corpus."))
        with monkeypatch.context() as faults:
            faults.setattr(Path, "rglob", walks)
            allocator.index_corpus(corpus.root)
        assert walks.call_count == 0
        path = corpus.root / "unreadable.pdf"
        path.write_bytes(b"%PDF-1.4\nOriginal indexing input.\n")
        retry = PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
        with monkeypatch.context() as faults:
            faults.setattr(
                PdfPathAllocator, "_digest_file", MagicMock(side_effect=PermissionError("Synthetic input failure."))
            )
            with pytest.raises(PermissionError, match="Synthetic input failure"):
                retry.index_corpus(corpus.root)
        assert retry._cache.root is None
        assert retry._cache.files == {}
        assert path.read_bytes() == b"%PDF-1.4\nOriginal indexing input.\n"

    def test_temporary_and_linked_paths_cannot_authorize_reuse(
        self, corpus: SmallCorpusHarness, tmp_path: Path
    ) -> None:
        """Neither a partial path nor a file link can become canonical."""
        allocator = corpus.downloader._allocator
        assert allocator.valid_document(str(corpus.root / "partial.pdf.part"), "a" * 64) is False
        assert allocator.valid_document(str(corpus.root / "unknown.pdf"), None) is False
        with pytest.raises(OSError, match="temporary corpus path"):
            allocator._key(corpus.root / "partial.pdf.part")
        original = tmp_path / "original.pdf"
        original.write_bytes(b"%PDF original local link target")
        link = corpus.root / "linked.pdf"
        link.symlink_to(original)
        with pytest.raises(OSError, match="symbolic link"):
            allocator._key(link)
        assert original.read_bytes() == b"%PDF original local link target"
        assert link.is_symlink()

    def test_unbound_allocator_rejects_durable_metadata_operations(self) -> None:
        """A missing corpus root never becomes a default path."""
        allocator = PdfPathAllocator(lambda _path: None)
        with pytest.raises(RuntimeError, match="has not been indexed"):
            allocator._root()
        assert allocator._cache.root is None

    def test_stored_hash_rejects_a_file_that_changes_during_its_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The real descriptor check rejects an unstable content digest."""
        path = tmp_path / "changing.pdf"
        payload = b"%PDF-1.4\nOriginal changing input.\n"
        path.write_bytes(payload)
        original = os.fstat
        calls: list[int] = []

        def changing(descriptor: int) -> os.stat_result:
            calls.append(descriptor)
            if len(calls) == 2:
                path.write_bytes(payload + b"x")
            return original(descriptor)

        with monkeypatch.context() as faults:
            faults.setattr(os, "fstat", changing)
            with pytest.raises(OSError, match="changed during hashing"):
                PdfPathAllocator._digest_file(path)
        assert len(calls) == 2
        assert path.read_bytes() == payload + b"x"

    def test_extensionless_published_payload_remains_indexed_after_restart(self, corpus: SmallCorpusHarness) -> None:
        """A recorded original name without a suffix does not lose its cache identity."""
        first_url, second_url = "https://example.test/original/download", "https://example.test/other/renamed.pdf#page"
        payload = b"%PDF-1.4\nOriginal extensionless payload.\n"
        corpus.seed(first_url, first_url, "design")
        corpus.client.payloads[first_url] = payload
        first = corpus.downloader.download_document(first_url, corpus.root / "design")
        corpus.persist_success(first_url, first)
        corpus.store.close()
        corpus.store = HarvestStateStore(corpus.root / "harvest_state.db")
        corpus.downloader = CorpusDownloader(
            corpus.client, corpus.root, PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
        )
        corpus.seed(second_url, second_url, "hardware-guides")
        corpus.client.payloads[second_url] = payload
        second = corpus.downloader.download_document(second_url, corpus.root / "hardware-guides")
        assert second == ("skipped", str(corpus.root / "design" / "download"), len(payload), None)
        by_url = {row["root_url"]: row for row in corpus.store.document_rows()}
        assert by_url[second_url]["original_pdf_name"] == "renamed.pdf"
        assert corpus.payload_writes.call_count == 1
        assert not (corpus.root / "hardware-guides" / "renamed.pdf").exists()


class TestExpectedContentDecisions:
    """Reject changes between path planning, validation, and association."""

    def test_expected_download_digest_cannot_change_before_association(self, corpus: SmallCorpusHarness) -> None:
        """Both new publication and cached reuse must keep their expected full digest."""
        allocator = corpus.downloader._allocator
        url = "https://example.test/expected.pdf"
        path = corpus.root / "expected.pdf"
        record = ("a" * 64, (1, 1, 1, 1, 1))
        allocator._cache.pending = (url, path, "b" * 64, 1)
        with pytest.raises(OSError, match="differs from the planned response"):
            allocator._validate_download(url, path, record)
        allocator._cache.pending = None
        allocator._cache.urls[url] = (path, "b" * 64)
        with pytest.raises(OSError, match="changed before association"):
            allocator._validate_download(url, path, record)
        assert corpus.store.document_rows() == []
        assert corpus.client.requests == []
        assert corpus.payload_writes.call_count == 0


class TestColdCacheWork:
    """Measure separate existing, published, and changed stored hash bytes."""

    def test_cold_existing_corpus_obeys_the_exact_stored_hash_bound(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A cold walk hashes existing bytes once and only touched changed bytes again."""
        folder = corpus.root / "original"
        folder.mkdir()
        payloads = [b"%PDF-1.4\n" + str(index).encode().ljust(2 * 1024 * 1024 + 8, b".") for index in range(3)]
        paths = [folder / f"original-{index}.pdf" for index in range(3)]
        for path, payload in zip(paths, payloads, strict=True):
            path.write_bytes(payload)
        existing_bytes = sum(path.stat().st_size for path in paths)
        observations = TestHashWork._observe(monkeypatch, corpus)
        assert observations.stored.call_count == 3
        modified = paths[0].stat()
        os.utime(paths[0], ns=(modified.st_atime_ns, modified.st_mtime_ns + 1000000))
        alias, unique = "https://example.test/new-name/alias.pdf", "https://example.test/new-name/unique.pdf"
        new_body = b"%PDF-1.4\n" + b"u" * 8183
        for url, payload in ((alias, payloads[0]), (unique, new_body)):
            corpus.seed(url, url, "design")
            corpus.client.payloads[url] = payload
        reused = corpus.downloader.download_document(alias, corpus.root / "design")
        published = corpus.downloader.download_document(unique, corpus.root / "design")
        assert reused == ("skipped", str(paths[0]), len(payloads[0]), None)
        assert published == ("downloaded", str(corpus.root / "design" / "unique.pdf"), len(new_body), None)
        hashed_bytes = sum(call.args[0].stat().st_size for call in observations.stored.call_args_list)
        changed_bytes = paths[0].stat().st_size
        assert hashed_bytes == existing_bytes + len(new_body) + changed_bytes
        assert observations.stored.call_count == 5
        assert observations.fetched.call_count == 2
        assert observations.walks.call_count == 1
        assert corpus.payload_writes.call_count == 1
        assert corpus.client.requests == [alias, unique]
        actual = list(corpus.root.rglob("*.pdf"))
        assert len(actual) == 4
        assert sum(path.stat().st_size for path in actual) == existing_bytes + len(new_body)
