"""Unit tests for ``src.cache.cache_utils.CacheUtils``.

Why:
    Un-omitted for #878 tranche 10. ``CacheUtils`` is a static utility class
    that mediates every CSV cache read/write in MistHelper — freshness gate,
    (re)generation, support-package dump, Menu 175 cache clear, address-parse
    failure export, and the fast-path freshness check.

Strategy:
    - Redirect ``importlib.import_module("MistHelper")`` to a lightweight fake
      so ``mh.FilePathUtils.get_csv_path`` resolves to ``tmp_path / <name>``
      and ``mh.CSV_FRESHNESS_MINUTES`` is a small integer.
    - Exercise real filesystem paths via ``tmp_path`` so os.path.getmtime /
      os.listdir / os.remove behavior is tested end-to-end.
    - Cover both the success and failure branches (OSError, generator raise,
      malformed rows, empty inputs) to reach 100% statement coverage.
"""

from __future__ import annotations

import csv
import importlib
import logging  # WHY (#886 Phase 2): assert against caplog after print()->logging migration.
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.cache.cache_utils import CacheUtils


class _FakeFilePathUtils:
    """Stand-in for ``MistHelper.FilePathUtils`` that anchors CSVs in tmp_path.

    Why:
        The real ``FilePathUtils.get_csv_path`` prefixes filenames with the
        repo's ``data/`` directory. Tests must not touch that shared directory,
        so we route every path through a pytest-managed temp directory.
    """

    def __init__(self, root: Path) -> None:
        """Store the root directory that will host resolved CSV paths."""
        self.root = root

    def get_csv_path(self, filename: str) -> str:
        """Return ``<root>/<filename>`` as a string, mirroring the production API."""
        return str(self.root / filename)


class _FakeMH:
    """Fake ``MistHelper`` module exposing only the attributes CacheUtils reads."""

    def __init__(self, root: Path, freshness_minutes: int = 60) -> None:
        """Wire up ``FilePathUtils`` and ``CSV_FRESHNESS_MINUTES`` attributes."""
        self.FilePathUtils = _FakeFilePathUtils(root)
        self.CSV_FRESHNESS_MINUTES = freshness_minutes


@pytest.fixture
def fake_mh(monkeypatch, tmp_path):
    """Redirect ``importlib.import_module('MistHelper')`` to a fake and return it.

    Why:
        Every CacheUtils method fetches ``FilePathUtils`` via ``importlib``.
        A per-test fake lets us anchor cache files inside ``tmp_path`` and
        control the configured freshness window without touching real modules.
    """
    fake = _FakeMH(tmp_path)
    real_import = importlib.import_module

    def _stub(name, *args, **kwargs):
        if name == "MistHelper":
            return fake
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("src.cache.cache_utils.importlib.import_module", _stub)
    return fake


# ---------------------------------------------------------------------------
# _is_csv_fresh
# ---------------------------------------------------------------------------


class TestIsCsvFresh:
    """Cover every branch of the freshness gate (missing / fresh / stale / OSError)."""

    def test_returns_false_when_missing(self, tmp_path):
        """Missing file must always be treated as stale."""
        assert CacheUtils._is_csv_fresh(str(tmp_path / "missing.csv"), "missing.csv", 60) is False

    def test_returns_true_when_fresh(self, tmp_path):
        """A file modified within the freshness window is considered fresh."""
        path = tmp_path / "fresh.csv"
        path.write_text("a,b\n1,2\n", encoding="utf-8")
        assert CacheUtils._is_csv_fresh(str(path), "fresh.csv", freshness_minutes=60) is True

    def test_returns_false_when_stale(self, tmp_path):
        """An old file (mtime beyond the window) is stale."""
        path = tmp_path / "stale.csv"
        path.write_text("a,b\n1,2\n", encoding="utf-8")
        old = (datetime.now() - timedelta(hours=2)).timestamp()
        os.utime(str(path), (old, old))
        assert CacheUtils._is_csv_fresh(str(path), "stale.csv", freshness_minutes=60) is False

    def test_returns_false_when_oserror(self, tmp_path, monkeypatch):
        """OSError while reading mtime is treated as stale (regeneration path)."""
        path = tmp_path / "err.csv"
        path.write_text("data", encoding="utf-8")

        def _raise(_):
            raise OSError("boom")

        monkeypatch.setattr("src.cache.cache_utils.os.path.getmtime", _raise)
        assert CacheUtils._is_csv_fresh(str(path), "err.csv", freshness_minutes=60) is False


# ---------------------------------------------------------------------------
# _run_csv_generator
# ---------------------------------------------------------------------------


class TestRunCsvGenerator:
    """Cover the success and failure legs of the generator wrapper."""

    def test_generator_success_returns_true(self):
        """Generator that completes without raising returns True."""
        called = {"n": 0}

        def _gen():
            called["n"] += 1

        assert CacheUtils._run_csv_generator(_gen, "out.csv") is True
        assert called["n"] == 1

    def test_generator_exception_returns_false(self):
        """Generator that raises must be swallowed and reported as failure."""

        def _gen():
            raise RuntimeError("kaboom")

        _gen.__name__ = "boom_gen"
        assert CacheUtils._run_csv_generator(_gen, "out.csv") is False


# ---------------------------------------------------------------------------
# check_and_generate_csv
# ---------------------------------------------------------------------------


class TestCheckAndGenerateCsv:
    """Verify the freshness dispatcher for fresh, stale, and default-freshness cases."""

    def test_returns_true_when_fresh(self, fake_mh, tmp_path):
        """Fresh file skips generator call and returns True."""
        path = tmp_path / "sites.csv"
        path.write_text("header\n", encoding="utf-8")
        gen = MagicMock()
        gen.__name__ = "gen_sites"
        assert CacheUtils.check_and_generate_csv("sites.csv", gen, freshness_minutes=60) is True
        gen.assert_not_called()

    def test_uses_default_freshness_when_none(self, fake_mh, tmp_path):
        """When freshness_minutes is None, falls back to mh.CSV_FRESHNESS_MINUTES."""
        fake_mh.CSV_FRESHNESS_MINUTES = 120
        path = tmp_path / "sites.csv"
        path.write_text("header\n", encoding="utf-8")
        gen = MagicMock()
        gen.__name__ = "gen_sites"
        assert CacheUtils.check_and_generate_csv("sites.csv", gen) is True

    def test_calls_generator_when_missing(self, fake_mh, tmp_path):
        """Missing file triggers a call to the generator."""
        gen = MagicMock()
        gen.__name__ = "gen_missing"
        assert CacheUtils.check_and_generate_csv("missing.csv", gen, freshness_minutes=60) is True
        gen.assert_called_once()

    def test_returns_false_when_generator_fails(self, fake_mh):
        """Generator that raises causes a False return."""

        def _gen():
            raise ValueError("nope")

        _gen.__name__ = "bad_gen"
        assert CacheUtils.check_and_generate_csv("nope.csv", _gen, freshness_minutes=60) is False


# ---------------------------------------------------------------------------
# load_csv_grouped_by_key
# ---------------------------------------------------------------------------


class TestLoadCsvGroupedByKey:
    """Verify grouping semantics and malformed-row handling."""

    def test_groups_rows_by_key(self, fake_mh, tmp_path):
        """Rows sharing the key value land in the same bucket."""
        path = tmp_path / "grouped.csv"
        path.write_text("site_id,name\nA,one\nA,two\nB,three\n", encoding="utf-8")
        result = CacheUtils.load_csv_grouped_by_key("grouped.csv", "site_id")
        assert set(result.keys()) == {"A", "B"}
        assert len(result["A"]) == 2
        assert result["B"][0]["name"] == "three"

    def test_skips_rows_missing_key(self, fake_mh, tmp_path):
        """A row whose grouping column is absent is skipped (not fatal)."""
        path = tmp_path / "skip.csv"
        path.write_text("name\nfoo\nbar\n", encoding="utf-8")
        result = CacheUtils.load_csv_grouped_by_key("skip.csv", "site_id")
        assert result == {}


# ---------------------------------------------------------------------------
# _collect_csv_fieldnames + _write_data_rows_to_csv + write_support_data_to_csv
# ---------------------------------------------------------------------------


class TestSupportDataCsvHelpers:
    """Cover the internal helpers and the end-to-end support-package writer."""

    def test_collect_csv_fieldnames_union_sorted(self):
        """Returns the deterministic sorted union of keys across all sections."""
        data = {"s1": [{"a": 1, "b": 2}], "s2": [{"b": 3, "c": 4}]}
        assert CacheUtils._collect_csv_fieldnames(data) == ["a", "b", "c"]

    def test_write_data_rows_to_csv_counts(self, tmp_path):
        """The row counter matches the number of rows actually written."""
        path = tmp_path / "rows.csv"
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["a", "b"])
            writer.writeheader()
            n = CacheUtils._write_data_rows_to_csv(writer, {"s": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]})
        assert n == 2

    def test_write_support_data_to_csv_roundtrip(self, fake_mh, tmp_path):
        """End-to-end: writes header + rows to tmp_path via FilePathUtils."""
        data = {"section": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}
        CacheUtils.write_support_data_to_csv(data, "support.csv")
        content = (tmp_path / "support.csv").read_text(encoding="utf-8").splitlines()
        assert content[0] == "a,b"
        assert content[1] in ("1,2", "3,4")


# ---------------------------------------------------------------------------
# _is_generated_file
# ---------------------------------------------------------------------------


class TestIsGeneratedFile:
    """Verify the generated-file allowlist + prefix logic."""

    def test_exact_match(self):
        """A filename in the explicit allowlist is generated."""
        assert CacheUtils._is_generated_file("SiteList.csv") is True

    def test_prefix_match(self):
        """A filename starting with a known prefix and .csv is generated."""
        assert CacheUtils._is_generated_file("AuditLogs_2026.csv") is True

    def test_prefix_but_not_csv(self):
        """A file matching a prefix but without .csv is NOT generated."""
        assert CacheUtils._is_generated_file("Gateway_notes.txt") is False

    def test_no_match(self):
        """A file neither in allowlist nor matching prefix is not generated."""
        assert CacheUtils._is_generated_file("user_notes.csv") is False


# ---------------------------------------------------------------------------
# _scan_cache_candidates + _delete_cache_files + clear_cache
# ---------------------------------------------------------------------------


class TestScanCacheCandidates:
    """Cover both the happy path and the OSError path of the directory scan."""

    def test_returns_generated_files(self, tmp_path, monkeypatch):
        """Files matching allowlist or prefix are returned; unrelated files ignored."""
        (tmp_path / "SiteList.csv").write_text("x", encoding="utf-8")
        (tmp_path / "AuditLogs.csv").write_text("x", encoding="utf-8")
        (tmp_path / "user_notes.txt").write_text("x", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        result = CacheUtils._scan_cache_candidates(str(tmp_path))
        assert set(result) == {"SiteList.csv", "AuditLogs.csv"}

    def test_returns_none_on_oserror(self, monkeypatch):
        """Missing directory (or listdir OSError) returns None to abort clear."""

        def _raise(_):
            raise OSError("no such dir")

        monkeypatch.setattr("src.cache.cache_utils.os.listdir", _raise)
        assert CacheUtils._scan_cache_candidates("/nope") is None


class TestDeleteCacheFiles:
    """Cover the deleted/error counters for the batch-delete helper."""

    def test_deletes_files_and_counts(self, tmp_path):
        """Successful deletions increment the deleted counter."""
        (tmp_path / "a.csv").write_text("x", encoding="utf-8")
        (tmp_path / "b.csv").write_text("x", encoding="utf-8")
        deleted, errors = CacheUtils._delete_cache_files(str(tmp_path), ["a.csv", "b.csv"])
        assert deleted == 2
        assert errors == 0

    def test_error_counter_increments_on_oserror(self, tmp_path, monkeypatch):
        """OSError on remove increments the error counter (partial success continues)."""
        (tmp_path / "a.csv").write_text("x", encoding="utf-8")

        def _raise(_):
            raise OSError("locked")

        monkeypatch.setattr("src.cache.cache_utils.os.remove", _raise)
        deleted, errors = CacheUtils._delete_cache_files(str(tmp_path), ["a.csv"])
        assert deleted == 0
        assert errors == 1


class TestClearCache:
    """End-to-end orchestration for the Menu 175 clear-cache path."""

    def test_clears_generated_files(self, tmp_path, monkeypatch, caplog):
        """Discovers, prints, and deletes matching files, then reports totals."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "SiteList.csv").write_text("x", encoding="utf-8")
        (data_dir / "unrelated.txt").write_text("x", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        # WHY (#886 Phase 2): operator-visible summary is now WARNING-level via logging, not print().
        with caplog.at_level(logging.WARNING):
            CacheUtils.clear_cache()
        assert not (data_dir / "SiteList.csv").exists()
        assert (data_dir / "unrelated.txt").exists()
        assert "Cache cleared" in caplog.text

    def test_no_files_message_when_empty(self, tmp_path, monkeypatch, caplog):
        """Empty data dir prints the empty-state message without errors."""
        (tmp_path / "data").mkdir()
        monkeypatch.chdir(tmp_path)
        # WHY (#886 Phase 2): empty-state notice now WARNING via logging (see cache_utils.clear_cache).
        with caplog.at_level(logging.WARNING):
            CacheUtils.clear_cache()
        assert "No generated cache CSV files found to delete." in caplog.text

    def test_aborts_when_scan_fails(self, monkeypatch, caplog):
        """Scan failure (None) short-circuits clear_cache without printing summary."""
        monkeypatch.setattr(CacheUtils, "_scan_cache_candidates", staticmethod(lambda _: None))
        # WHY (#886 Phase 2): summary line is now WARNING via logging; capture it to assert absence.
        with caplog.at_level(logging.WARNING):
            CacheUtils.clear_cache()
        assert "Cache cleared" not in caplog.text


# ---------------------------------------------------------------------------
# create_address_parse_failures_csv
# ---------------------------------------------------------------------------


class TestCreateAddressParseFailuresCsv:
    """Cover empty-list no-op, happy path, and failure-write path."""

    def test_no_op_when_empty(self, fake_mh, tmp_path):
        """Empty parse_failures returns without touching disk."""
        CacheUtils.create_address_parse_failures_csv([])
        assert not (tmp_path / "AddressParseFailures.csv").exists()

    def test_writes_expected_rows(self, fake_mh, tmp_path, caplog):
        """One row per failure record is written under FilePathUtils path."""
        failures = [
            {
                "site_id": "s1",
                "site_name": "S1",
                "device_id": "d1",
                "device_serial": "sn1",
                "device_name": "dev1",
                "original_address": "123 Main",
                "parsed_tokens": "n/a",
                "failure_reason": "unknown",
                "timestamp": "2026-01-01",
            }
        ]
        # WHY (#886 Phase 2): operator-visible "documented in" notice is now WARNING via logging, not print().
        with caplog.at_level(logging.WARNING):
            CacheUtils.create_address_parse_failures_csv(failures, "custom.csv")
        content = (tmp_path / "custom.csv").read_text(encoding="utf-8").splitlines()
        assert content[0].startswith("site_id,")
        assert "123 Main" in content[1]
        assert "documented in" in caplog.text

    def test_swallows_write_exception(self, fake_mh, monkeypatch, caplog):
        """OSError during write is logged but does not raise."""

        def _bad_open(*_a, **_kw):
            raise OSError("disk full")

        monkeypatch.setattr("src.cache.cache_utils.open", _bad_open, raising=False)
        # WHY (#886 Phase 2): failure notice migrated from print() to logging.error; capture via caplog.
        with caplog.at_level(logging.ERROR):
            CacheUtils.create_address_parse_failures_csv([{"site_id": "x"}])
        assert "Failed to create address parse failures CSV" in caplog.text


# ---------------------------------------------------------------------------
# fast_cache_hit
# ---------------------------------------------------------------------------


class TestFastCacheHit:
    """Cover the freshness fast path (hit, miss, stale, stat error)."""

    def test_returns_false_when_missing(self, fake_mh, tmp_path):
        """Missing file is a cache miss."""
        assert CacheUtils.fast_cache_hit("nope.csv") is False

    def test_returns_true_when_fresh(self, fake_mh, tmp_path, caplog):
        """Fresh file returns True and emits the operator-facing message."""
        (tmp_path / "fresh.csv").write_text("x", encoding="utf-8")
        # WHY (#886 Phase 2): cache-hit notice migrated from print() to logging.warning.
        with caplog.at_level(logging.WARNING):
            assert CacheUtils.fast_cache_hit("fresh.csv", max_age_minutes=60) is True
        assert "Using cached fresh.csv" in caplog.text

    def test_returns_false_when_stale(self, fake_mh, tmp_path):
        """Stale file returns False so caller regenerates."""
        path = tmp_path / "stale.csv"
        path.write_text("x", encoding="utf-8")
        old = time.time() - 60 * 60 * 3  # 3 hours ago
        os.utime(str(path), (old, old))
        assert CacheUtils.fast_cache_hit("stale.csv", max_age_minutes=60) is False

    def test_returns_false_on_oserror(self, fake_mh, tmp_path, monkeypatch):
        """OSError during getmtime returns False (safe default)."""
        path = tmp_path / "err.csv"
        path.write_text("x", encoding="utf-8")

        def _raise(_):
            raise OSError("stat fail")

        monkeypatch.setattr("src.cache.cache_utils.os.path.getmtime", _raise)
        assert CacheUtils.fast_cache_hit("err.csv") is False
