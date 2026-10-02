"""Test canonical storage through the actual downloader and durable URL records."""

from __future__ import annotations

import hashlib
import urllib.error
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call

import pytest

from src.juniper_docs.acquire.downloader import CorpusDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator

if TYPE_CHECKING:
    from tests.unit.juniper_docs.canonical.conftest import RenderedManifests, SmallCorpusHarness
    from tests.unit.juniper_docs.conftest import FakeCatalogClient


class TestCanonicalDownloadFlow:
    """Verify physical payload writes without combining independent URL records."""

    def test_equal_bytes_across_names_and_categories(self, corpus: SmallCorpusHarness) -> None:
        """Two fetched URLs must share one payload across different names and categories."""
        roots = ("https://example.test/docs/alpha/", "https://example.test/docs/beta/")
        urls = ("https://example.test/a/alpha.pdf", "https://example.test/b/beta.pdf")
        categories = ("configuration-guides", "hardware-guides")
        payload = b"%PDF-1.4\nOriginal shared payload.\n"
        corpus.client.payloads.update(dict.fromkeys(urls, payload))
        for root, url, category in zip(roots, urls, categories, strict=True):
            corpus.seed(root, url, category)
        canonical = corpus.root / categories[0] / "alpha.pdf"
        first = corpus.downloader.download_document(urls[0], corpus.root / categories[0])
        corpus.persist_success(roots[0], first)
        second = corpus.downloader.download_document(urls[1], corpus.root / categories[1])
        corpus.persist_success(roots[1], second)
        manifests = corpus.render_manifests()
        pdf_paths = sorted(corpus.root.rglob("*.pdf"))
        physical_bytes = sum(path.stat().st_size for path in pdf_paths)
        assert (first, second) == (
            ("downloaded", str(canonical), len(payload), None),
            ("skipped", str(canonical), len(payload), None),
        ), (
            f"The flow wrote {len(pdf_paths)} PDF files with {physical_bytes} physical bytes "
            f"and {corpus.payload_writes.call_count} payload writes. The fetches were {corpus.client.requests!r}."
        )
        for rows in manifests:
            assert [row["local_path"] for row in rows] == [str(canonical), str(canonical)]
        self._assert_alias_metadata(manifests, roots, urls, categories)
        json_rows, csv_rows = manifests
        assert [row["file_size"] for row in json_rows] == [len(payload), len(payload)]
        assert [row["file_size"] for row in csv_rows] == [str(len(payload)), str(len(payload))]
        alternates = [url.removesuffix(".pdf") + "-alternate.pdf" for url in urls]
        assert [row["rejected_candidates"] for row in json_rows] == [[url] for url in alternates]
        assert [row["rejected_candidates"] for row in csv_rows] == alternates
        assert len(pdf_paths) == 1
        assert pdf_paths == [canonical]
        assert physical_bytes == len(payload)
        assert canonical.read_bytes() == payload
        assert not (corpus.root / categories[1] / "beta.pdf").exists()
        assert list(corpus.root.rglob("*.part")) == []
        assert corpus.client.requests == list(urls)
        assert corpus.payload_writes.call_count == 1
        assert corpus.payload_writes.call_args_list == [call(canonical, payload)]

    @pytest.mark.parametrize(
        ("first_payload", "second_payload"),
        [
            (b"%PDF-1.4\nalpha\n", b"%PDF-1.4\nbravo\n"),
            (b"%PDF-1.4\nalpha\n", b"%PDF-1.4\nbravo-longer\n"),
        ],
        ids=["equal-size", "different-size"],
    )
    def test_distinct_bytes_with_shared_basename(
        self, corpus: SmallCorpusHarness, first_payload: bytes, second_payload: bytes
    ) -> None:
        """Different payloads with one basename must retain both exact byte sequences."""
        roots = ("https://example.test/docs/alpha/", "https://example.test/docs/beta/")
        urls = ("https://example.test/a/shared.pdf", "https://example.test/b/shared.pdf")
        categories = ("configuration-guides", "configuration-guides")
        corpus.client.payloads.update({urls[0]: first_payload, urls[1]: second_payload})
        for root, url, category in zip(roots, urls, categories, strict=True):
            corpus.seed(root, url, category)
        folder = corpus.root / categories[0]
        first_path = folder / "shared.pdf"
        discriminator = hashlib.sha256(urls[1].encode("utf-8")).hexdigest()[:10]
        second_path = folder / f"shared-{discriminator}.pdf"
        first = corpus.downloader.download_document(urls[0], folder)
        corpus.persist_success(roots[0], first)
        second = corpus.downloader.download_document(urls[1], folder)
        corpus.persist_success(roots[1], second)
        assert first == ("downloaded", str(first_path), len(first_payload), None)
        assert second == ("downloaded", str(second_path), len(second_payload), None)
        assert first_path.read_bytes() == first_payload
        assert second_path.read_bytes() == second_payload
        assert set(corpus.root.rglob("*.pdf")) == {first_path, second_path}
        assert first_path.stat().st_size + second_path.stat().st_size == len(first_payload) + len(second_payload)
        assert list(corpus.root.rglob("*.part")) == []
        assert corpus.client.requests == list(urls)
        assert corpus.payload_writes.call_count == 2
        assert corpus.payload_writes.call_args_list == [
            call(first_path, first_payload),
            call(second_path, second_payload),
        ]
        manifests = corpus.render_manifests()
        self._assert_alias_metadata(manifests, roots, urls, categories)
        for rows in manifests:
            assert [row["local_path"] for row in rows] == [str(first_path), str(second_path)]

    def test_same_url_repeat_skips_without_fetch(self, corpus: SmallCorpusHarness) -> None:
        """A known URL must skip without another fetch or physical payload write."""
        root = "https://example.test/docs/alpha/"
        url = "https://example.test/a/alpha.pdf"
        payload = b"%PDF-1.4\nOriginal repeat payload.\n"
        corpus.seed(root, url, "configuration-guides")
        corpus.client.payloads[url] = payload
        folder = corpus.root / "configuration-guides"
        canonical = folder / "alpha.pdf"
        first = corpus.downloader.download_document(url, folder)
        corpus.persist_success(root, first)
        corpus.client.payloads.clear()  # An unexpected fetch must fail instead of receiving another response.
        second = corpus.downloader.download_document(url, folder)
        corpus.persist_success(root, second)
        assert first == ("downloaded", str(canonical), len(payload), None)
        assert second == ("skipped", str(canonical), len(payload), None)
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 1
        assert corpus.payload_writes.call_args_list == [call(canonical, payload)]
        assert list(corpus.root.rglob("*.pdf")) == [canonical]
        assert canonical.read_bytes() == payload
        for rows in corpus.render_manifests():
            assert [row["source_url"] for row in rows] == [root]
            assert [row["local_path"] for row in rows] == [str(canonical)]
            assert [row["status"] for row in rows] == ["classified"]

    def test_known_alias_repeat_across_categories_skips_without_fetch(self, corpus: SmallCorpusHarness) -> None:
        """A known resolved URL must keep both category records without another fetch."""
        roots = ("https://example.test/docs/alpha/", "https://example.test/docs/beta/")
        url = "https://example.test/a/alpha.pdf"
        categories = ("configuration-guides", "hardware-guides")
        payload = b"%PDF-1.4\nOriginal alias payload.\n"
        corpus.client.payloads[url] = payload
        for root, category in zip(roots, categories, strict=True):
            corpus.seed(root, url, category)
        canonical = corpus.root / categories[0] / "alpha.pdf"
        first = corpus.downloader.download_document(url, corpus.root / categories[0])
        corpus.persist_success(roots[0], first)
        second = corpus.downloader.download_document(url, corpus.root / categories[1])
        corpus.persist_success(roots[1], second)
        assert first == ("downloaded", str(canonical), len(payload), None)
        assert second == ("skipped", str(canonical), len(payload), None)
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 1
        assert corpus.payload_writes.call_args_list == [call(canonical, payload)]
        assert list(corpus.root.rglob("*.pdf")) == [canonical]
        assert canonical.read_bytes() == payload
        assert not (corpus.root / categories[1] / "alpha.pdf").exists()
        manifests = corpus.render_manifests()
        self._assert_alias_metadata(manifests, roots, (url, url), categories)
        for rows in manifests:
            assert [row["local_path"] for row in rows] == [str(canonical), str(canonical)]

    @staticmethod
    def _assert_alias_metadata(
        manifests: RenderedManifests, roots: tuple[str, str], urls: tuple[str, str], categories: tuple[str, str]
    ) -> None:
        """Check independent source metadata in both actual manifest formats."""
        for rows in manifests:
            assert [row["source_url"] for row in rows] == list(roots)
            assert [row["resolved_pdf_url"] for row in rows] == list(urls)
            assert [row["category"] for row in rows] == list(categories)
            assert [row["chosen_pdf"] for row in rows] == list(urls)
            assert [row["status"] for row in rows] == ["classified", "classified"]


class TestDownloadHttpFailures:
    """Verify permanent and transient HTTP failures without a network request."""

    @pytest.mark.parametrize(
        ("status", "expected_reason"),
        [
            (404, "permanent: HTTP Error 404: The scripted download failed."),
            (503, "transient: HTTP Error 503: The scripted download failed."),
        ],
        ids=["http-404", "http-503"],
    )
    def test_http_failure_classification(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch, status: int, expected_reason: str
    ) -> None:
        """An HTTP failure must report its exact class and leave no payload."""
        root = "https://example.test/docs/failure/"
        url = "https://example.test/failure.pdf"
        corpus.seed(root, url, "configuration-guides")
        monkeypatch.setattr(corpus.client, "fetch_bytes", partial(self._raise_http_failure, corpus.client, status))
        result = corpus.downloader.download_document(url, corpus.root / "configuration-guides")
        assert result == ("failed", None, None, expected_reason)
        corpus.store.mark_failed(root, expected_reason)
        row = corpus.store.document_rows()[0]
        assert (row["stage"], row["local_path"], row["file_size"], row["error_reason"]) == (
            "failed",
            None,
            None,
            expected_reason,
        )
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 0
        assert corpus.payload_writes.call_args_list == []
        assert list(corpus.root.rglob("*.pdf")) == []
        assert list(corpus.root.rglob("*.part")) == []

    @staticmethod
    def _raise_http_failure(client: FakeCatalogClient, status: int, url: str) -> bytes:
        """Record a local fake request and raise its scripted HTTP status."""
        client.requests.append(url)  # Preserve request evidence at the injected failure boundary.
        raise urllib.error.HTTPError(url, status, "The scripted download failed.", {}, None)


class TestAtomicPublication:
    """Prove failure at real publication boundaries with no partial receipts."""

    @pytest.mark.parametrize("boundary", ["write", "flush", "replace"])
    def test_interruption_leaves_no_final_payload_or_successful_pointer(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch, boundary: str
    ) -> None:
        """A failed temporary write or replacement cannot reach a complete stage."""
        root, url = "https://example.test/source/", "https://example.test/interrupted.pdf"
        corpus.seed(root, url, "design")
        corpus.client.payloads[url] = b"%PDF-1.4\nOriginal interrupted body.\n"
        with monkeypatch.context() as faults:
            self._interrupt(faults, boundary)
            result = corpus.downloader.download_document(url, corpus.root / "design")
        assert result == (
            "failed",
            None,
            None,
            "permanent: local corpus operation failed: Synthetic publication failure.",
        )
        row = corpus.store.document_rows()[0]
        assert (row["stage"], row["local_path"], row["file_size"], row["content_sha256"]) == (
            "resolved",
            None,
            None,
            None,
        )
        assert list(corpus.root.rglob("*.pdf")) == []
        assert list(corpus.root.rglob("*.part")) == []
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 1
        assert corpus.store.content_rows(str(corpus.root.resolve())) == []

    @staticmethod
    def _interrupt(monkeypatch: pytest.MonkeyPatch, boundary: str) -> None:
        """Inject a failure at the real temporary-file operation."""
        failure = MagicMock(side_effect=OSError("Synthetic publication failure."))
        if boundary == "flush":
            monkeypatch.setattr("src.juniper_docs.acquire.downloader.os.fsync", failure)
        elif boundary == "replace":
            original = Path.replace
            monkeypatch.setattr(
                Path, "replace", lambda path, target: failure() if path.suffix == ".part" else original(path, target)
            )
        else:
            original_open = Path.open
            monkeypatch.setattr(
                Path,
                "open",
                lambda path, *arguments, **options: (
                    failure() if path.suffix == ".part" else original_open(path, *arguments, **options)
                ),
            )

    def test_existing_partial_file_never_authorizes_a_resume(self, corpus: SmallCorpusHarness) -> None:
        """A partial path produces a new verified final write, not a skip."""
        root, url = "https://example.test/source/", "https://example.test/partial.pdf"
        corpus.seed(root, url, "design")
        category = corpus.root / "design"
        category.mkdir()
        (category / "partial.pdf.part").write_bytes(b"%PDF-incomplete")
        payload = b"%PDF-1.4\nOriginal complete body.\n"
        corpus.client.payloads[url] = payload
        result = corpus.downloader.download_document(url, category)
        assert result == ("downloaded", str(category / "partial.pdf"), len(payload), None)
        assert (category / "partial.pdf").read_bytes() == payload
        assert not (category / "partial.pdf.part").exists()
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 1

    def test_racing_complete_destination_is_not_overwritten(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A complete destination that appears before publication retains its own bytes."""
        target = tmp_path / "race.pdf"
        other = b"%PDF-1.4\nOriginal independent destination.\n"
        with monkeypatch.context() as faults:
            faults.setattr(
                "src.juniper_docs.acquire.downloader.os.fsync", lambda _descriptor: target.write_bytes(other)
            )
            with pytest.raises(FileExistsError, match="appeared before publication"):
                CorpusDownloader._atomic_write(target, b"%PDF-1.4\nOriginal attempted response.\n")
        assert target.read_bytes() == other
        assert not target.with_suffix(".pdf.part").exists()


class TestCollisionAndResponseGuards:
    """Keep original bytes and source history through unusual response names."""

    def test_occupied_url_hash_variant_allocates_the_next_safe_name(self, corpus: SmallCorpusHarness) -> None:
        """An occupied deterministic suffix cannot destroy an unrelated payload."""
        first, second = "https://example.test/a/guide.pdf", "https://example.test/b/guide.pdf"
        for url in (first, second):
            corpus.seed(url, url, "design")
        corpus.client.payloads.update({first: b"%PDF-A", second: b"%PDF-B"})
        folder = corpus.root / "design"
        assert corpus.downloader.download_document(first, folder) == ("downloaded", str(folder / "guide.pdf"), 6, None)
        discriminator = PdfPathAllocator._short_hash(second)
        occupied = folder / f"guide-{discriminator}.pdf"
        occupied.write_bytes(b"%PDF-C")
        final = folder / f"guide-{discriminator}-2.pdf"
        assert corpus.downloader.download_document(second, folder) == ("downloaded", str(final), 6, None)
        assert occupied.read_bytes() == b"%PDF-C"
        assert (folder / "guide.pdf").read_bytes() == b"%PDF-A"
        assert final.read_bytes() == b"%PDF-B"
        assert corpus.payload_writes.call_count == 2

    def test_query_and_fragment_names_preserve_original_url_keys(self, corpus: SmallCorpusHarness) -> None:
        """URL suffixes stay in provenance, not in the canonical basename."""
        urls = ("https://example.test/a/alpha.pdf#first", "https://example.test/b/beta.pdf?source=original")
        payload = b"%PDF Original response with no EOF requirement"
        for url in urls:
            corpus.seed(url, url, "design")
            corpus.client.payloads[url] = payload
            result = corpus.downloader.download_document(url, corpus.root / "design")
            corpus.persist_success(url, result)
        rows = corpus.store.document_rows()
        canonical = corpus.root / "design" / "alpha.pdf"
        assert [row["root_url"] for row in rows] == list(urls)
        assert [row["original_pdf_name"] for row in rows] == ["alpha.pdf", "beta.pdf"]
        assert [row["local_path"] for row in rows] == [str(canonical)] * 2
        assert canonical.read_bytes() == payload
        assert corpus.payload_writes.call_count == 1
        assert corpus.client.requests == list(urls)

    @pytest.mark.parametrize("suffix", ["/", "/..", "/partial.pdf.part"])
    def test_unusable_final_name_fails_without_a_fetch(self, corpus: SmallCorpusHarness, suffix: str) -> None:
        """A temporary or absent basename cannot create a complete payload receipt."""
        result = corpus.downloader.download_document("https://example.test" + suffix, corpus.root / "design")
        assert result == (
            "failed",
            None,
            None,
            "permanent: local corpus operation failed: The corpus URL has no usable PDF file name.",
        )
        assert corpus.client.requests == []
        assert corpus.payload_writes.call_count == 0
        assert not (corpus.root / "design").exists()
