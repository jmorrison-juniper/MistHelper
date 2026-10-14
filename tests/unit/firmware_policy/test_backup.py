"""Prove complete settings backups verify and private data cannot reach portal outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.operations.execution.firmware_policy.recovery.backup import BACKUP_DIRECTORY, PolicyBackup
from src.operations.execution.firmware_policy.sdk import PolicyError
from web_portal.services.data_browser import DataBrowserService
from web_portal.services.output_scan import OutputFileScanner


def test_full_backup_verifies_content_count_checksum_and_permissions(tmp_path: Path) -> None:
    """Retain complete organization and site settings with private POSIX permissions."""
    records = [
        {"scope": "org", "id": "one", "settings": {"ssr": {"conductor_token": "private-fixture"}}},
        {"scope": "site", "id": "two", "settings": {"auto_upgrade": {"enabled": False}, "timezone": "UTC"}},
    ]
    backup = PolicyBackup(tmp_path)
    path = backup.save(records)
    document = json.loads(path.read_text())
    assert document["records"] == records
    assert document["record_count"] == 2
    assert document["sha256"] == backup.digest(records)
    assert "+00:00" in document["created_at"]
    if os.name != "nt":
        assert path.stat().st_mode & 0o077 == 0
        assert path.parent.stat().st_mode & 0o077 == 0
    backup.verify(path, records)


@pytest.mark.parametrize("field", ["records", "record_count", "sha256"])
def test_corrupted_backup_fails_verification(tmp_path: Path, field: str) -> None:
    """Reject changed settings, incomplete counts, and invalid checksums."""
    backup = PolicyBackup(tmp_path)
    records = [{"scope": "org", "id": "one", "settings": {"timezone": "UTC"}}]
    path = backup.save(records)
    document = json.loads(path.read_text())
    document[field] = None
    path.write_text(json.dumps(document))
    with pytest.raises(PolicyError, match="does not match"):
        backup.verify(path, records)


def test_missing_and_unreadable_backups_fail(tmp_path: Path) -> None:
    """A missing or invalid JSON file cannot satisfy the backup gate."""
    backup = PolicyBackup(tmp_path)
    records = [{"scope": "org", "id": "one", "settings": {}}]
    path = backup.save(records)
    path.write_text("{incomplete")
    with pytest.raises(PolicyError, match="could not be verified"):
        backup.verify(path, records)
    path.unlink()
    with pytest.raises(PolicyError, match="could not be verified"):
        backup.verify(path, records)


@pytest.mark.parametrize("content", [b"", b"bad json"])
def test_empty_body_and_malformed_json_backup_fail(tmp_path: Path, content: bytes) -> None:
    """Reject empty files and malformed JSON rather than treating them as good backups."""
    backup = PolicyBackup(tmp_path)
    records = [{"scope": "site", "id": "one", "settings": {"timezone": "UTC"}}]
    path = backup.save(records)
    path.write_bytes(content)
    with pytest.raises(PolicyError, match="could not be verified"):
        backup.verify(path, records)


def test_backup_write_failure_is_explicit(tmp_path: Path) -> None:
    """Refuse an invalid local storage target instead of continuing without a backup."""
    blocked = tmp_path / BACKUP_DIRECTORY
    blocked.write_text("not a directory")
    with pytest.raises(PolicyError, match="could not be written"):
        PolicyBackup(tmp_path).save([{"settings": {}}])


def test_non_json_settings_cannot_be_backed_up(tmp_path: Path) -> None:
    """Reject unreadable complete settings before creating a misleading backup."""
    with pytest.raises(PolicyError, match="cannot be serialized"):
        PolicyBackup(tmp_path).save([{"settings": {"invalid": float("nan")}}])
    assert not (tmp_path / BACKUP_DIRECTORY).exists()


def test_private_backup_is_not_listed_previewed_downloaded_or_scanned(tmp_path: Path) -> None:
    """Deny full settings bundles, including access through another symbolic link."""
    scanner = OutputFileScanner(str(tmp_path))
    scanner.snapshot()
    path = PolicyBackup(tmp_path).save([{"settings": {"conductor_token": "private-fixture"}}])
    browser = DataBrowserService(str(tmp_path))
    assert browser.list_files() == []
    assert browser.resolve_safe_path(str(path.relative_to(tmp_path))) is None
    assert browser.preview_file(str(path.relative_to(tmp_path)), 1, 50, "") == {"error": "File not found"}
    assert scanner.changed_files() == []
    if os.name != "nt":
        alias = tmp_path / "visible.json"
        alias.symlink_to(path)
        assert browser.resolve_safe_path(alias.name) is None
