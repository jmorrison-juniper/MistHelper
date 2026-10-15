"""Reject hostile legacy bundles and preserve original private files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.firmware_policy.recovery.fakes import RestoreSession


def test_valid_bundle_is_private_unchanged_and_sanitized(tmp_path: Path) -> None:
    """Expose scope metadata while keeping private values in the original file."""
    session = RestoreSession(tmp_path)
    original = session.path.read_bytes()
    bundle = BundleFiles(session.backup).read(session.path.stem)
    assert bundle.records == session.saved
    assert "private-fixture" not in json.dumps(bundle.summary())
    assert session.path.read_bytes() == original
    if os.name != "nt":
        assert session.path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("content", [b"", b"{}", b"[]", b"bad json", b'{"records":[],"records":[]}'])
def test_invalid_json_and_envelopes_fail(tmp_path: Path, content: bytes) -> None:
    """Unreadable or ambiguous input cannot enter a restoration plan."""
    session = RestoreSession(tmp_path)
    session.path.write_bytes(content)
    with pytest.raises(PolicyError):
        BundleFiles(session.backup).read(session.path.stem)
    assert session.writes == []


@pytest.mark.parametrize("change", ["checksum", "count", "empty", "duplicate", "scope", "identifier", "time", "nan"])
def test_tampered_envelopes_fail(tmp_path: Path, change: str) -> None:
    """Reject bad identity and shape even when an attacker recalculates the checksum."""
    session = RestoreSession(tmp_path)
    document = json.loads(session.path.read_text())
    if change == "checksum":
        document["sha256"] = "0" * 64
    elif change == "count":
        document["record_count"] = True
    elif change == "time":
        document["created_at"] = "2026-10-14T10:00:00"
    else:
        mutations: dict[str, Any] = {
            "empty": [],
            "duplicate": [document["records"][0]] * 2,
            "scope": [{"scope": "device", "id": session.saved[0]["id"], "settings": {}}],
            "identifier": [{"scope": "org", "id": "../../token", "settings": {}}],
            "nan": [{"scope": "org", "id": session.saved[0]["id"], "settings": {"allow_mist": float("nan")}}],
        }
        document["records"] = mutations[change]
        document["record_count"] = len(document["records"])
        document["sha256"] = "invalid" if change == "nan" else PolicyBackup.digest(document["records"])
    session.path.write_text(json.dumps(document))
    with pytest.raises(PolicyError):
        BundleFiles(session.backup).read(session.path.stem)
    assert session.writes == []


def test_symlink_hardlink_traversal_and_public_files_fail(tmp_path: Path) -> None:
    """The loader must reject unsafe file identity before reading settings."""
    session = RestoreSession(tmp_path)
    files = BundleFiles(session.backup)
    with pytest.raises(PolicyError):
        files.read("../outside")
    linked = session.path.with_name("11111111-1111-4111-8111-111111111111.json")
    linked.symlink_to(session.path)
    with pytest.raises(PolicyError):
        files.read(linked.stem)
    linked.unlink()
    os.link(session.path, linked)
    with pytest.raises(PolicyError):
        files.read(session.path.stem)
    linked.unlink()
    if os.name != "nt":
        session.path.chmod(0o640)
        with pytest.raises(PolicyError):
            files.read(session.path.stem)


def test_oversized_record_fails(tmp_path: Path) -> None:
    """A per-record bound must not become an aggregate bundle size threshold."""
    session = RestoreSession(tmp_path)
    session.path.write_bytes(b'{"records":[{"settings":{"large":"' + b"x" * (8 * 1024 * 1024 + 1) + b'"}}]}')
    with pytest.raises(PolicyError, match="record resource limit"):
        BundleFiles(session.backup).read(session.path.stem)


def test_duplicate_setting_keys_are_rejected_before_checksum_validation(tmp_path: Path) -> None:
    """Ambiguous record values cannot disappear during the streamed object decode."""
    session = RestoreSession(tmp_path)
    text = session.path.read_text()
    text = text.replace('"allow_mist": true', '"allow_mist": true, "allow_mist": false', 1)
    session.path.write_text(text)
    with pytest.raises(PolicyError, match="duplicate JSON keys"):
        BundleFiles(session.backup).read(session.path.stem)
    assert session.writes == []


def test_truncated_late_record_cannot_become_a_partial_bundle(tmp_path: Path) -> None:
    """A valid first record cannot bypass a missing late record delimiter."""
    session = RestoreSession(tmp_path)
    text = session.path.read_text()
    session.path.write_text(text[: text.index('"site_id"') + 15])
    with pytest.raises(PolicyError):
        BundleFiles(session.backup).read(session.path.stem)
    assert session.writes == []


def test_job_status_directory_is_not_a_backup_selection(tmp_path: Path) -> None:
    """Private portal status can share the private root without entering restoration."""
    session = RestoreSession(tmp_path)
    (session.backup.root / ".portal-jobs").mkdir(mode=0o700)
    assert [row["token"] for row in BundleFiles(session.backup).list()] == [session.path.stem]
