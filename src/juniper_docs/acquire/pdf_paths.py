"""Select one canonical payload across corpus names, categories, and URLs."""

from __future__ import annotations

import ctypes
import hashlib
import logging
import os
import stat
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.juniper_docs.harvest.state_store import HarvestStateStore

_LOGGER = logging.getLogger(__name__)

type OwnerLookup = Callable[[str], str | None]
type FileIdentity = tuple[int, int, int, int, int]
type ContentRecord = tuple[str, FileIdentity]

_HASH_WIDTH = 10
_MAX_VARIANTS = 1000
_READ_BLOCK = 1024 * 1024


class PdfPathAllocator:
    """Own canonical content lookup and collision-safe path allocation."""

    @dataclass
    class Cache:
        """Hold metadata only for one allocator lifetime."""

        root: Path | None = None
        files: dict[Path, ContentRecord] = field(default_factory=dict)
        digests: dict[str, set[Path]] = field(default_factory=dict)
        urls: dict[str, tuple[Path, str]] = field(default_factory=dict)
        pending: tuple[str, Path, str, int] | None = None

    class WindowsFileTimes(ctypes.Structure):
        """Read native change time instead of Windows creation time."""

        change_time: int
        _fields_ = [
            ("creation_time", ctypes.c_int64),
            ("access_time", ctypes.c_int64),
            ("write_time", ctypes.c_int64),
            ("change_time", ctypes.c_int64),
            ("attributes", ctypes.c_uint32),
        ]

    def __init__(self, owner_lookup: OwnerLookup, store: HarvestStateStore | None = None) -> None:
        """Store the existing ownership lookup and optional durable state."""
        self._owner_of = owner_lookup
        self._store = store
        self._cache = self.Cache()

    def index_corpus(self, root: Path) -> None:
        """Discover complete paths once and validate persisted hash metadata."""
        resolved = root.resolve()
        if self._cache.root is not None:
            if resolved != self._cache.root:
                raise ValueError("An allocator cannot serve two corpus roots.")
            return
        _LOGGER.info("Indexing corpus files under %s", resolved)
        self._cache.root = resolved
        try:
            self._index_files()
            self._load_aliases()
        except (OSError, RuntimeError, ValueError):
            _LOGGER.exception("Corpus indexing failed after checking %d file identities", len(self._cache.files))
            self._cache = self.Cache()
            raise
        _LOGGER.debug("Indexed %d complete files and %d URL aliases", len(self._cache.files), len(self._cache.urls))

    def _index_files(self) -> None:
        """Perform the single walk and discard only stale path metadata."""
        self._load_cache()
        seen: set[Path] = set()
        for path in self._root().rglob("*"):
            if path.suffix.lower() == ".pdf" and not path.is_dir() and self._occupied(path):
                key = self._key(path)
                self._record_for(key)
                seen.add(key)
        for missing in self._cache.files.keys() - seen:
            try:
                self._record_for(missing)  # Recorded PDF payloads can have a name without a PDF extension.
            except FileNotFoundError:
                self._forget(missing)

    def existing_for_url(self, target: Path, url: str) -> Path | None:
        """Return a verified URL association without another response fetch."""
        if self._store is not None:
            self._refresh_url(url)
        association = self._cache.urls.get(url)
        if association is not None:
            path, expected = association
            if self._matches(path, expected):
                return self._display(path, target)
            recovered = self._canonical(expected)
            if recovered is not None:
                _LOGGER.debug("Recovered 1 URL association from verified stored content")
                return self._display(recovered, target)
            _LOGGER.warning("The stored file for a URL needs recovery: %s", path)
            return None
        if self._store is not None:
            return None
        for candidate in self._variants(target, url):
            if not self._occupied(candidate):
                return None
            if self._owner_of(str(candidate)) == url:
                digest, _identity = self._record_for(self._key(candidate))
                self._cache.urls[url] = (self._key(candidate), digest)
                return candidate
        return None

    def _refresh_url(self, url: str) -> None:
        """Use current durable pointers without another corpus discovery walk."""
        if self._store is None:
            return
        rows = self._store.associations_for_url(url)
        digests = {str(row["content_sha256"]) for row in rows if row["content_sha256"] is not None}
        if len(digests) > 1:
            raise RuntimeError("Several source rows disagree about one resolved URL's expected content.")
        if digests:
            expected = next(iter(digests))
            paths = sorted(self._key(Path(str(row["local_path"]))) for row in rows if row["content_sha256"] == expected)
            self._cache.urls[url] = (paths[0], expected)
        else:
            self._cache.urls.pop(url, None)

    def plan_bytes(self, target: Path, url: str, payload: bytes) -> tuple[Path, bool]:
        """Hash a fetched body once, then select content before a local name."""
        digest = self._digest_bytes(payload)
        canonical = self._canonical(digest)
        final, write = (
            (self._display(canonical, target), False)
            if canonical is not None
            else self._place_path(target, url, len(payload), digest)
        )
        self._cache.pending = (url, self._key(final), digest, len(payload))
        return final, write

    def plan_file(self, target: Path, url: str, source: Path) -> tuple[Path, bool]:
        """Plan a placement without selecting the source as its own duplicate."""
        digest, identity = self._record_for(self._key(source))
        canonical = self._canonical(digest, exclude=self._key(source))
        if canonical is not None:
            return self._display(canonical, target), False
        return self._place_path(target, url, identity[0], digest)

    def record_download(self, path: Path, url: str) -> None:
        """Verify publication and required durable aliases before success."""
        key = self._key(path)
        record = self._record_for(key)
        self._validate_download(url, key, record)
        if self._store is not None:
            rows = self._store.associate_content(str(self._root()), str(path), url, record)
            for row in rows:
                self._cache.urls[str(row["resolved_pdf_url"])] = (key, record[0])
        self._cache.urls[url] = (key, record[0])
        self._cache.pending = None
        _LOGGER.debug("Verified 1 canonical payload for %s", path)

    def _validate_download(self, url: str, key: Path, record: ContentRecord) -> None:
        """Compare a publication or reuse against its recorded expected content."""
        pending = self._cache.pending
        planned = pending is not None and pending[:2] == (url, key)
        if planned and pending is not None:
            if record[0] != pending[2] or record[1][0] != pending[3]:
                raise OSError("The published payload differs from the planned response.")
        expected = self._cache.urls.get(url)
        if not planned and expected is not None and record[0] != expected[1]:
            raise OSError("The stored URL payload changed before association.")

    def record_move(self, source: Path, final: Path) -> None:
        """Refresh path metadata and every alias after a real placement."""
        source_key, final_key = self._key(source), self._key(final)
        if source_key == final_key:
            return
        record = self._record_for(final_key)
        if self._store is not None:
            self._store.relocate_content(str(self._root()), str(source), str(final), record)
        if not source.exists():
            self._forget(source_key)
        for url, (path, digest) in tuple(self._cache.urls.items()):
            if path == source_key:
                self._cache.urls[url] = (final_key, digest)
        _LOGGER.debug("Updated canonical placement to %s", final)

    def valid_document(self, local_path: str, expected: str | None) -> bool:
        """Validate a recorded file before a final document can resume."""
        if expected is None or Path(local_path).suffix.lower() == ".part":
            return False
        return self._matches(self._key(Path(local_path)), expected)

    def _load_cache(self) -> None:
        """Load metadata for this real corpus root without reading payloads."""
        if self._store is None:
            return
        for row in self._store.content_rows(str(self._root())):
            path = self._key(Path(str(row["local_path"])))
            self._remember(path, self._store._content_from_row(row))

    def _load_aliases(self) -> None:
        """Load natural URL associations and explicitly adopt legacy digests."""
        if self._store is None:
            return
        _LOGGER.info("Loading corpus URL associations")
        for row in self._store.document_rows():
            if row["local_path"] is None or row["resolved_pdf_url"] is None:
                continue
            path = self._key(Path(str(row["local_path"])))
            digest = row["content_sha256"]
            if digest is None and path.suffix.lower() != ".part" and self._occupied(path):
                with path.open("rb") as handle:
                    valid_prefix = handle.read(4) == b"%PDF"
                if valid_prefix:
                    digest = self._record_for(path)[0]
                    self._store.adopt_content(str(row["root_url"]), digest)
                else:
                    self._store.mark_failed(str(row["root_url"]), "The legacy local payload is not a PDF.")
            if digest is not None:
                self._remember_alias(str(row["resolved_pdf_url"]), path, str(digest))
        _LOGGER.debug("Loaded %d resolved URL associations", len(self._cache.urls))

    def _remember_alias(self, url: str, path: Path, digest: str) -> None:
        """Reject conflicting persisted identities for one resolved URL."""
        existing = self._cache.urls.get(url)
        if existing is not None and existing[1] != digest:
            raise RuntimeError("Several source rows disagree about one resolved URL's expected content.")
        self._cache.urls.setdefault(url, (path, digest))

    def _canonical(self, digest: str, exclude: Path | None = None) -> Path | None:
        """Return a stable verified path across the entire indexed corpus."""
        candidates = sorted(self._cache.digests.get(digest, ()))
        established = {path for path, expected in self._cache.urls.values() if expected == digest}
        for path in sorted(candidates, key=lambda candidate: (candidate not in established, str(candidate))):
            if path != exclude and self._matches(path, digest):
                return path
        return self._canonical_from_store(digest, exclude, candidates)

    def _canonical_from_store(self, digest: str, exclude: Path | None, checked: list[Path]) -> Path | None:
        """Find a moved path through the existing digest index, not another walk."""
        if self._store is None:
            return None
        for saved in self._store.paths_for_digest(str(self._root()), digest):
            path = self._key(Path(saved))
            if path != exclude and path not in checked and self._matches(path, digest):
                return path
        return None

    def _matches(self, path: Path, expected: str) -> bool:
        """Reject a missing or changed expected payload without changing its identity."""
        try:
            digest, _identity = self._record_for(path)
        except FileNotFoundError:
            self._forget(path)
            _LOGGER.warning("A canonical payload is missing: %s", path)
            return False
        if digest != expected:
            _LOGGER.warning("A canonical payload has different content: %s", path)
            return False
        return True

    def _record_for(self, path: Path) -> ContentRecord:
        """Use a full stat identity or stream only the changed file."""
        identity = self._identity(path)
        stored = self._cache.files.get(path)
        if stored is None and self._store is not None:
            stored = self._store.content_record(str(self._root()), str(path))
        with path.open("rb") as handle:
            if self._stat_identity(os.fstat(handle.fileno()), handle.fileno()) != identity:
                raise OSError("The corpus file changed before validation.")
            if stored is not None and stored[1] == identity:
                if self._identity(path) != identity:
                    raise OSError("The corpus file changed before reuse.")
                self._remember(path, stored)
                return stored
        digest = self._digest_file(path)
        if self._identity(path) != identity:
            raise OSError("The corpus file changed during validation.")
        record = (digest, identity)
        if self._store is not None:
            self._store.cache_content(str(self._root()), str(path), record)
        self._remember(path, record)
        return record

    def _remember(self, path: Path, record: ContentRecord) -> None:
        """Update both derived maps without another filesystem walk."""
        previous = self._cache.files.get(path)
        if previous is not None:
            self._cache.digests[previous[0]].discard(path)
        self._cache.files[path] = record
        self._cache.digests.setdefault(record[0], set()).add(path)

    def _forget(self, path: Path) -> None:
        """Remove stale metadata only, never a corpus payload."""
        previous = self._cache.files.pop(path, None)
        if previous is not None:
            self._cache.digests[previous[0]].discard(path)
        if self._store is not None:
            self._store.forget_content(str(self._root()), str(path))

    def _place_path(self, target: Path, url: str, size: int, digest: str) -> tuple[Path, bool]:
        """Keep different bytes separate even when the resolved URL repeats."""
        self._key(target)
        for candidate in self._variants(target, url):
            if not self._occupied(candidate):
                return candidate, True
            if self._same_content(candidate, size, digest):
                return candidate, False
        raise RuntimeError(f"No free variant name exists for {target}.")

    def _same_content(self, path: Path, size: int, digest: str) -> bool:
        """Confirm equality from verified content, never URL ownership."""
        if path.stat().st_size != size:
            return False
        return self._record_for(self._key(path))[0] == digest

    def _key(self, path: Path) -> Path:
        """Reject links and paths outside the selected corpus."""
        if path.suffix.lower() == ".part":
            raise OSError("A temporary corpus path cannot be a canonical payload.")
        if path.is_symlink():
            raise OSError("A corpus payload path cannot be a symbolic link.")
        resolved = path.resolve()
        if self._cache.root is not None and not resolved.is_relative_to(self._cache.root):
            raise OSError("A corpus payload path is outside the corpus root.")
        return resolved

    def _root(self) -> Path:
        """Require corpus binding before any durable cache operation."""
        if self._cache.root is None:
            raise RuntimeError("The corpus root has not been indexed.")
        return self._cache.root

    @staticmethod
    def _display(path: Path, target: Path) -> Path:
        """Preserve relative output paths for callers that use a relative root."""
        return path if target.is_absolute() else Path(os.path.relpath(path))

    def _variants(self, target: Path, url: str) -> Iterator[Path]:
        """Yield the clean name, URL-hash name, and bounded indexed names."""
        yield target
        digest = self._short_hash(url)
        yield self._suffixed(target, digest)
        for index in range(2, _MAX_VARIANTS):
            yield self._suffixed(target, f"{digest}-{index}")

    @classmethod
    def _identity(cls, path: Path) -> FileIdentity:
        """Require a nonempty regular file and reliable host identity."""
        reading = path.lstat()
        if not stat.S_ISREG(reading.st_mode) or reading.st_size <= 0:
            raise OSError("A canonical payload must be a nonempty regular file.")
        if sys.platform == "win32":
            with path.open("rb") as handle:
                return cls._stat_identity(reading, handle.fileno())
        return cls._stat_identity(reading)

    @classmethod
    def _stat_identity(cls, reading: os.stat_result, descriptor: int | None = None) -> FileIdentity:
        """Include change time to detect restored-mtime replacements."""
        if reading.st_ino <= 0 or reading.st_dev < 0:
            raise OSError("This host cannot provide a reliable corpus file identity.")
        changed = reading.st_ctime_ns
        if sys.platform == "win32":
            if descriptor is None:
                raise OSError("Windows change time requires an open file descriptor.")
            changed = cls._windows_change_time(descriptor)
        identity = (reading.st_size, reading.st_dev, reading.st_ino, reading.st_mtime_ns, changed)
        if any(value < -(2**63) or value >= 2**63 for value in identity):
            raise OSError("The host file identity cannot fit the SQLite signed integer fields.")
        return identity

    @classmethod
    def _windows_change_time(cls, descriptor: int) -> int:
        """Require the native FILE_BASIC_INFO change clock for cached trust."""
        information = cls.WindowsFileTimes()
        _LOGGER.info("The tool reads 1 native Windows file change time.")
        success = cls._query_windows_clock(descriptor, information)
        if not success or information.change_time <= 0:
            raise OSError("The filesystem cannot provide a Windows FILE_BASIC_INFO change time.")
        _LOGGER.debug("The tool read 1 native Windows file change time.")
        return (information.change_time - 116444736000000000) * 100  # Convert Windows ticks to Unix nanoseconds.

    @staticmethod
    def _query_windows_clock(descriptor: int, information: WindowsFileTimes) -> bool:
        """Load the native handle capability and query its exact ABI."""
        import msvcrt

        loader = getattr(ctypes, "WinDLL", None)
        convert_handle = getattr(msvcrt, "get_osfhandle", None)
        if loader is None or convert_handle is None:
            raise OSError("The Windows FILE_BASIC_INFO change-time capability is unavailable.")
        library = loader("kernel32", use_last_error=True)
        query = library.GetFileInformationByHandleEx
        query.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        query.restype = ctypes.c_int
        return bool(query(convert_handle(descriptor), 0, ctypes.byref(information), ctypes.sizeof(information)))

    @staticmethod
    def _occupied(path: Path) -> bool:
        """Treat links and existing nonempty paths as occupied."""
        return path.is_symlink() or (path.exists() and path.stat().st_size > 0)

    @staticmethod
    def _suffixed(target: Path, discriminator: str) -> Path:
        """Insert a stable discriminator before the original suffix."""
        return target.with_name(f"{target.stem}-{discriminator}{target.suffix}")

    @staticmethod
    def _short_hash(url: str) -> str:
        """Return the existing short URL discriminator, not a content identity."""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:_HASH_WIDTH]

    @staticmethod
    def _digest_bytes(payload: bytes) -> str:
        """Calculate one full digest of a fetched response."""
        _LOGGER.info("Hashing 1 fetched payload with %d bytes", len(payload))
        digest = hashlib.sha256(payload).hexdigest()
        _LOGGER.debug("Hashed 1 fetched payload with %d bytes", len(payload))
        return digest

    @classmethod
    def _digest_file(cls, path: Path) -> str:
        """Hash original stored bytes in bounded blocks with stable identity."""
        _LOGGER.info("Hashing 1 stored payload at %s", path)
        before = cls._identity(path)
        digest = hashlib.sha256()
        try:
            with path.open("rb") as handle:
                if cls._stat_identity(os.fstat(handle.fileno()), handle.fileno()) != before:
                    raise OSError("The corpus file changed before hashing.")
                for block in iter(lambda: handle.read(_READ_BLOCK), b""):
                    digest.update(block)
                after = cls._stat_identity(os.fstat(handle.fileno()), handle.fileno())
            if after != before or cls._identity(path) != before:
                raise OSError("The corpus file changed during hashing.")
        except OSError:
            _LOGGER.exception("Cannot hash the stored corpus payload")
            raise
        _LOGGER.debug("Hashed 1 stored payload with %d bytes", before[0])
        return digest.hexdigest()
