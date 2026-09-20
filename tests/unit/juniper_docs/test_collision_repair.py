"""Regression tests for the silent file overwrite defect (issue #2738).

Two remote PDF files that share a file name once landed on one local path, and
the second write destroyed the first. The manifest still recorded both, so the
loss was invisible. These tests prove the repair through the real downloader and
the real runner, and against the recorded evidence in ``juniper_corpus_smoke``.
No test reads the network. No test re-runs the live crawl.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path, PurePath

import pytest

from src.juniper_docs.acquire.downloader import CorpusDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.juniper_docs.classify.slug_classifier import UNCATEGORIZED
from src.juniper_docs.harvest.runner import HarvestConfig, HarvestRunner, TuningConfig, _sanitize
from src.juniper_docs.harvest.state_store import HarvestStateStore
from src.juniper_docs.models import DocumentType, InventoryRecord, PdfCandidate
from tests.unit.juniper_docs.conftest import FakeCatalogClient

# The recorded manifest from the run that lost 50 documents (measured evidence).
_SMOKE_MANIFEST = Path(__file__).resolve().parents[3] / "data" / "juniper_corpus_smoke" / "manifest.json"

_APSTRA_A = "https://www.juniper.net/documentation/us/en/software/apstra4.2/apstra-user-guide/"
_APSTRA_B = "https://www.juniper.net/documentation/us/en/software/apstra6.2/apstra-user-guide/"

# Three uncategorized roots that each resolve to one shared companion PDF file
# name. An uncategorized slug reaches the runner _place step, where the stale-row
# defect built a constant "None" hash for every later same-name document.
_UNCAT_ROOTS = (
    "https://www.juniper.net/documentation/us/en/software/topology-alpha/",
    "https://www.juniper.net/documentation/us/en/software/topology-beta/",
    "https://www.juniper.net/documentation/us/en/software/topology-gamma/",
)
_SHARED_HREF = "topology-summary.pdf"  # Every uncategorized index page names this companion PDF.


def _downloader(tmp_path: Path, owners: dict[str, str], payloads: dict[str, bytes]) -> CorpusDownloader:
    """Return a downloader whose allocator reads the shared owner map."""
    client = FakeCatalogClient(payloads=payloads)  # A client that serves the scripted PDFs.
    return CorpusDownloader(client, tmp_path, PdfPathAllocator(owners.get))  # Owner-aware downloader.


def _download(downloader: CorpusDownloader, owners: dict[str, str], url: str, folder: Path) -> tuple[str, str]:
    """Download one URL, record the stored owner, and return the outcome and path."""
    outcome, path, _size, _reason = downloader.download_document(url, folder)  # Download the PDF.
    if path is not None:  # A downloaded or reused file has a real path.
        owners[path] = url  # Record the owner, as the runner does after mark_downloaded.
    assert path is not None  # Every scripted URL produces a stored path.
    return outcome, path  # The caller asserts on the outcome and the path.


def test_two_urls_same_name_produce_two_files(tmp_path: Path) -> None:
    """Two different URLs with one base name each write a distinct file (path one)."""
    url_a = "https://x/apstra4.2/apstra-user-guide.pdf"  # The first version URL.
    url_b = "https://x/apstra6.2/apstra-user-guide.pdf"  # The second version URL.
    payloads = {url_a: b"%PDF-A first version body", url_b: b"%PDF-B second version longer body"}
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    downloader = _downloader(tmp_path, owners, payloads)  # An owner-aware downloader.
    folder = tmp_path / "guides"  # Both versions target the same category folder.
    outcome_a, path_a = _download(downloader, owners, url_a, folder)  # Download the first.
    outcome_b, path_b = _download(downloader, owners, url_b, folder)  # Download the second.
    assert outcome_a == "downloaded" and outcome_b == "downloaded"  # Both are fresh writes.
    assert path_a != path_b  # Each distinct document kept its own path.
    assert Path(path_a).read_bytes() == payloads[url_a]  # The first file holds its own bytes.
    assert Path(path_b).read_bytes() == payloads[url_b]  # The second file holds its own bytes.


def test_same_url_twice_downloads_once(tmp_path: Path) -> None:
    """The same URL downloaded twice keeps one file and skips the second fetch (resume)."""
    url = "https://x/apstra4.2/apstra-user-guide.pdf"  # One resolved PDF URL.
    payloads = {url: b"%PDF-A single body"}  # One scripted payload for the URL.
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    downloader = _downloader(tmp_path, owners, payloads)  # An owner-aware downloader.
    folder = tmp_path / "guides"  # The category folder for the document.
    outcome_first, path_first = _download(downloader, owners, url, folder)  # First download.
    outcome_second, path_second = _download(downloader, owners, url, folder)  # Second call.
    assert outcome_first == "downloaded" and outcome_second == "skipped"  # One write, one skip.
    assert path_first == path_second  # The same URL maps to the one stored file.
    assert downloader.client.requests == [url]  # The second call made no network read.


def test_two_urls_identical_bytes_produce_one_file(tmp_path: Path) -> None:
    """Two different URLs with identical bytes keep one file (the ctpview case)."""
    url_a = "https://x/ctp9.1/ctpview-server.pdf"  # The first ctpview URL.
    url_b = "https://x/ctp/ctpview-server.pdf"  # The second ctpview URL.
    body = b"%PDF ctpview identical bytes for both urls"  # One byte payload for both URLs.
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    downloader = _downloader(tmp_path, owners, {url_a: body, url_b: body})  # Owner-aware.
    folder = tmp_path / "uncategorized" / "configuration"  # The shared destination folder.
    outcome_a, path_a = _download(downloader, owners, url_a, folder)  # Download the first.
    outcome_b, path_b = _download(downloader, owners, url_b, folder)  # Download the second.
    assert outcome_a == "downloaded" and outcome_b == "skipped"  # The identical second is deduped.
    assert path_a == path_b  # One stored file holds the identical document.
    assert sum(1 for _ in folder.glob("*.pdf")) == 1  # Exactly one file sits on disk.


def _register(store: HarvestStateStore, root: str, pdf_url: str, path: Path, payload: bytes) -> None:
    """Write a file and record its owner in the store, as a prior run would."""
    path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the destination folder.
    path.write_bytes(payload)  # Persist the earlier document on disk.
    store.add_document(InventoryRecord(root, "slug", DocumentType.HTML_ROOT))  # Record the document.
    store.set_resolved(root, pdf_url, [PdfCandidate(pdf_url, True, "chosen")])  # Record the URL.
    store.mark_downloaded(root, str(path), len(payload))  # Record the stored local path.


def _place_config(tmp_path: Path) -> HarvestConfig:
    """Return a runner config that writes under the test directory."""
    tuning = TuningConfig(delay_seconds=0.0, timeout_seconds=5, max_sample_pages=8, confidence_threshold=2.0)
    return HarvestConfig(tmp_path, str(tmp_path / "unused.xml"), "insecure", False, tuning)  # Client injected.


def test_place_does_not_destroy_an_existing_different_file(tmp_path: Path) -> None:
    """The _place move never overwrites an existing file from a different URL (path one)."""
    runner = HarvestRunner(_place_config(tmp_path), client=FakeCatalogClient())  # Build the runner.
    label_dir = tmp_path / UNCATEGORIZED / _sanitize("guides")  # The label folder path.
    existing = label_dir / "guide.pdf"  # A stored file from an earlier different document.
    _register(runner.store, "https://a/root/", "https://a/guide.pdf", existing, b"%PDF-A earlier body")
    source = tmp_path / UNCATEGORIZED / "guide.pdf"  # The staged new download in the staging folder.
    source.parent.mkdir(parents=True, exist_ok=True)  # Ensure the staging folder exists.
    source.write_bytes(b"%PDF-B different larger body")  # A different document to place.
    final = runner._place(str(source), "guides", "https://b/guide.pdf")  # Place the new document.
    runner.store.close()  # Release the database file.
    assert existing.read_bytes() == b"%PDF-A earlier body"  # The earlier file is intact.
    assert Path(final) != existing and Path(final).exists()  # The new document has its own file.
    assert Path(final).read_bytes() == b"%PDF-B different larger body"  # It holds its own bytes.


def _apstra_sitemap(tmp_path: Path) -> str:
    """Write a two-version apstra sitemap and return its local path."""
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{_APSTRA_A}</loc></url>\n"
        f"  <url><loc>{_APSTRA_B}</loc></url>\n"
        "</urlset>\n"
    )  # A minimal sitemap that names both apstra versions.
    path = tmp_path / "apstra_sitemap.xml"  # The local sitemap path under the test directory.
    path.write_text(body, encoding="utf-8")  # Persist the sitemap for the reader.
    return str(path)  # The runner reads this local path with no network call.


def _fake_for_apstra() -> tuple[FakeCatalogClient, str, str]:
    """Return a client that serves both apstra index pages and two distinct PDFs."""
    href = "apstra-user-guide.pdf"  # Both index pages name this companion PDF.
    pdf_a = _APSTRA_A + href  # The first version resolves to its own PDF URL.
    pdf_b = _APSTRA_B + href  # The second version resolves to its own PDF URL.
    texts = {_APSTRA_A: f'<a href="{href}">PDF</a>', _APSTRA_B: f'<a href="{href}">PDF</a>'}
    payloads = {pdf_a: b"%PDF-1.4 apstra 4.2 body", pdf_b: b"%PDF-1.4 apstra 6.2 longer body"}
    return FakeCatalogClient(texts=texts, payloads=payloads), pdf_a, pdf_b


def test_manifest_records_a_distinct_path_for_each_document(tmp_path: Path) -> None:
    """A full run gives each of two same-name documents its own manifest path (issue #2738)."""
    client, _pdf_a, _pdf_b = _fake_for_apstra()  # A client scripted for both versions.
    tuning = TuningConfig(delay_seconds=0.0, timeout_seconds=5, max_sample_pages=8, confidence_threshold=2.0)
    config = HarvestConfig(tmp_path, _apstra_sitemap(tmp_path), "insecure", False, tuning)  # The run config.
    assert HarvestRunner(config, client=client).run() == 0  # The full run reaches a final stage.
    data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))  # Read the manifest.
    classified = [entry for entry in data if entry["status"] == "classified"]  # The stored documents.
    assert len(classified) == 2  # The manifest covers both apstra versions.
    paths = {entry["local_path"] for entry in classified}  # The recorded final paths.
    assert len(paths) == 2  # Each document has a distinct final path, so none was lost.
    assert len({str(Path(p).parent) for p in paths}) == 1  # Both share one folder, so this was a real collision.
    for entry in classified:  # Prove every recorded path resolves to a real file.
        assert Path(entry["local_path"]).exists()  # The manifest path is not a phantom.
    contents = {Path(entry["local_path"]).read_bytes() for entry in classified}  # The stored bytes.
    assert len(contents) == 2  # The two files hold their own distinct bytes.


def _load_smoke_manifest() -> list[dict]:
    """Return the recorded smoke manifest, or skip when the evidence is absent."""
    if not _SMOKE_MANIFEST.is_file():  # The evidence file must be present to prove the repair.
        pytest.skip(f"smoke manifest evidence not present at {_SMOKE_MANIFEST}")  # Name the missing input.
    return json.loads(_SMOKE_MANIFEST.read_text(encoding="utf-8"))  # The recorded 400-entry manifest.


def _distinct_urls_for(manifest: list[dict], filename: str) -> list[str]:
    """Return the distinct resolved PDF URLs that the recorded run mapped to one file name."""
    urls: list[str] = []  # The distinct resolved URLs, in first-seen order.
    for entry in manifest:  # Scan every recorded manifest entry once.
        path = entry.get("local_path")  # The recorded final path of this entry.
        if path and PurePath(path).name == filename and entry["resolved_pdf_url"] not in urls:
            urls.append(entry["resolved_pdf_url"])  # Keep each resolved URL one time.
    return urls  # The competing URLs the buggy run collapsed onto one path.


def test_real_apstra_collision_keeps_every_version(tmp_path: Path) -> None:
    """The recorded apstra collision keeps one file for each distinct version (evidence)."""
    urls = _distinct_urls_for(_load_smoke_manifest(), "apstra-user-guide.pdf")  # Real competing URLs.
    assert len(urls) >= 2  # The recorded run mapped several versions onto one path.
    payloads = {url: b"%PDF-1.4 apstra unique " + bytes([index]) * (index + 5) for index, url in enumerate(urls)}
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    downloader = _downloader(tmp_path, owners, payloads)  # An owner-aware downloader.
    folder = tmp_path / "uncategorized" / "apstra__configuration__routing"  # The recorded label folder.
    paths = [_download(downloader, owners, url, folder)[1] for url in urls]  # Download each version.
    assert len(set(paths)) == len(urls)  # Every distinct version kept its own path.
    assert sum(1 for _ in folder.glob("*.pdf")) == len(urls)  # One file per version sits on disk.
    for url, path in zip(urls, paths, strict=True):  # Prove each stored file holds its own bytes.
        assert Path(path).read_bytes() == payloads[url]  # No version overwrote another version.


def test_real_ctpview_identical_stays_one_file(tmp_path: Path) -> None:
    """The recorded ctpview case keeps one file because every URL holds identical bytes (evidence)."""
    urls = _distinct_urls_for(_load_smoke_manifest(), "ctpview-server.pdf")  # Real competing URLs.
    assert len(urls) >= 2  # The recorded run reached ctpview from more than one URL.
    body = b"%PDF-1.4 ctpview identical bytes for every url"  # One byte payload for every URL.
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    downloader = _downloader(tmp_path, owners, {url: body for url in urls})  # Owner-aware downloader.
    folder = tmp_path / "uncategorized" / "configuration"  # The recorded ctpview label folder.
    outcomes = [_download(downloader, owners, url, folder) for url in urls]  # Download each URL.
    assert len({path for _outcome, path in outcomes}) == 1  # Identical bytes stay one stored file.
    assert sum(1 for _ in folder.glob("*.pdf")) == 1  # Exactly one file sits on disk for ctpview.
    assert outcomes[0][0] == "downloaded"  # The first URL writes the single file.
    assert all(outcome == "skipped" for outcome, _path in outcomes[1:])  # Every later URL is deduped.


def _collisions_by_path(manifest: list[dict]) -> dict[str, list[str]]:
    """Return each recorded final path that more than one distinct resolved URL claimed."""
    by_path: dict[str, list[str]] = defaultdict(list)  # The distinct URLs recorded for each path.
    for entry in manifest:  # Scan every recorded manifest entry once.
        path = entry.get("local_path")  # The recorded final path of this entry.
        if path and entry["status"] == "classified" and entry["resolved_pdf_url"] not in by_path[path]:
            by_path[path].append(entry["resolved_pdf_url"])  # Keep each resolved URL one time.
    return {path: urls for path, urls in by_path.items() if len(urls) > 1}  # Only real collisions.


def _distinct_payloads(urls: list[str]) -> dict[str, bytes]:
    """Return a distinct valid PDF payload for each URL, so each is a distinct document."""
    return {
        url: b"%PDF-1.4 distinct " + str(index).encode() + b" " + bytes([index % 240 + 1]) * (index + 4)
        for index, url in enumerate(urls)
    }  # A unique body and a unique length per URL model distinct documents.


def test_real_every_recorded_collision_keeps_every_distinct_url(tmp_path: Path) -> None:
    """The repair keeps one file for each distinct URL across every recorded collision (evidence)."""
    collisions = _collisions_by_path(_load_smoke_manifest())  # The recorded different-URL collisions.
    assert len(collisions) >= 20  # The recorded run collapsed many distinct URLs onto one path.
    lost: list[str] = []  # The cases where a distinct document would still be lost.
    for index, urls in enumerate(collisions.values()):  # Replay each recorded collision once.
        folder = tmp_path / f"case{index}"  # A fresh folder isolates each recorded collision.
        owners: dict[str, str] = {}  # The path-to-URL owner map for this case.
        downloader = _downloader(folder, owners, _distinct_payloads(urls))  # Owner-aware downloader.
        stored = {_download(downloader, owners, url, folder)[1] for url in urls}  # Download each URL.
        if len(stored) != len(urls):  # Fewer files than distinct URLs means a lost document.
            lost.append(folder.name)  # Record the case that still loses a document.
    assert lost == []  # Every distinct document in every recorded collision kept its own file.


def _uncategorized_sitemap(tmp_path: Path, roots: tuple[str, ...]) -> str:
    """Write a sitemap that names every uncategorized root and return its local path."""
    locs = "".join(f"  <url><loc>{root}</loc></url>\n" for root in roots)  # One loc line per root.
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    path = tmp_path / "uncategorized_sitemap.xml"  # The local sitemap path under the test directory.
    path.write_text(header + locs + "</urlset>\n", encoding="utf-8")  # Persist the sitemap, so no network read.
    return str(path)  # The runner reads this local path with no network call.


def _fake_for_uncategorized(roots: tuple[str, ...]) -> FakeCatalogClient:
    """Return a client that serves an index page and a distinct PDF for each root."""
    texts = {root: f'<a href="{_SHARED_HREF}">PDF</a>' for root in roots}  # One index page per root.
    payloads = {
        root + _SHARED_HREF: b"%PDF-1.4 body " + bytes([index + 1]) * (index + 5) for index, root in enumerate(roots)
    }  # A distinct body and length per root, so each root is a distinct document with one file name.
    return FakeCatalogClient(texts=texts, payloads=payloads)  # A client scripted for every root.


def _run_uncategorized(tmp_path: Path, roots: tuple[str, ...]) -> list[dict]:
    """Run the harvester over the uncategorized roots and return the classified manifest entries."""
    client = _fake_for_uncategorized(roots)  # A client scripted for every root.
    tuning = TuningConfig(delay_seconds=0.0, timeout_seconds=5, max_sample_pages=8, confidence_threshold=2.0)
    config = HarvestConfig(tmp_path, _uncategorized_sitemap(tmp_path, roots), "insecure", False, tuning)  # Run config.
    assert HarvestRunner(config, client=client).run() == 0  # The full run reaches a final stage.
    data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))  # Read the rendered manifest.
    return [entry for entry in data if entry["status"] == "classified"]  # The stored classified documents.


def _assert_name_matches_its_own_url(entry: dict) -> None:
    """Assert one stored file name is the clean base name or the variant of its own URL."""
    name = PurePath(entry["local_path"]).name  # The stored file name for this document.
    suffix = PdfPathAllocator._short_hash(entry["resolved_pdf_url"])  # The hash the allocator derives from the URL.
    variant = f"topology-summary-{suffix}.pdf"  # The URL-specific disambiguated name.
    assert name in {_SHARED_HREF, variant}  # The name is the clean base or its own URL variant.


def test_uncategorized_disambiguator_is_specific_to_each_document(tmp_path: Path) -> None:
    """Two same-name uncategorized documents each keep a URL-specific name (stale-row defect)."""
    classified = _run_uncategorized(tmp_path, _UNCAT_ROOTS[:2])  # Both rows lack a URL at classify time.
    names = {PurePath(entry["local_path"]).name for entry in classified}  # The distinct stored file names.
    assert len(classified) == 2 and len(names) == 2  # Two documents keep two distinct file names.
    parents = {str(PurePath(entry["local_path"]).parent) for entry in classified}  # The stored folders.
    assert len(parents) == 1  # Both share one folder, so this was a real same-folder collision.
    for entry in classified:  # Prove each file name is derived from its own resolved URL.
        _assert_name_matches_its_own_url(entry)  # The name is never the constant hash of the string None.


def test_uncategorized_two_documents_get_distinct_disambiguators(tmp_path: Path) -> None:
    """Three same-name uncategorized documents keep three files with two URL-specific disambiguators."""
    classified = _run_uncategorized(tmp_path, _UNCAT_ROOTS)  # Three rows that lack a URL at classify time.
    names = {PurePath(entry["local_path"]).name for entry in classified}  # The distinct stored file names.
    assert len(classified) == 3 and len(names) == 3  # Every document kept its own file, so none was lost.
    for entry in classified:  # Prove each name is specific to its own resolved URL.
        _assert_name_matches_its_own_url(entry)  # The disambiguator is the URL hash, not a shared constant.
    variants = names - {_SHARED_HREF}  # The disambiguated names, without the clean base name.
    assert len(variants) == 2  # Two documents carry two distinct URL-specific disambiguators.
