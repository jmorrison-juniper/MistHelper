"""Prove SID-based Windows ownership and private access decisions on every test platform."""

from __future__ import annotations

import json
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.operations.execution.firmware_policy.recovery.backup import WINDOWS_ACL_QUERY, BackupAccess
from src.operations.execution.firmware_policy.sdk import PolicyError


@pytest.fixture
def acl_document() -> dict[str, Any]:
    """Model the current owner and only privileged Windows trustees."""
    return {
        "owner": "S-1-5-21-1-2-3-1001",
        "current": "S-1-5-21-1-2-3-1001",
        "null_dacl": False,
        "rules": [
            {"sid": "S-1-5-21-1-2-3-1001", "allowed": True, "rights": 2032127},
            {"sid": "S-1-5-18", "allowed": True, "rights": 2032127},
            {"sid": "S-1-5-32-544", "allowed": True, "rights": 2032127},
        ],
    }


def test_windows_query_uses_fixed_script_literal_path_and_bounded_execution(
    tmp_path: Path, monkeypatch: Any, acl_document: dict[str, Any]
) -> None:
    """A path with shell punctuation must never enter the PowerShell command text."""
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    path = tmp_path / "a'; Write-Output unwanted;'.json"
    calls = []

    def query(command: list[str], **options: Any) -> Any:
        """Inspect the exact subprocess boundary without starting Windows software."""
        calls.append(command)
        assert command == [
            str(tmp_path / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            WINDOWS_ACL_QUERY,
        ]
        assert str(path) not in command[-1]
        assert options["env"]["MISTHELPER_BACKUP_ACL_PATH"] == str(path)
        assert options["timeout"] == 10
        assert options["check"] is True
        assert "shell" not in options
        return SimpleNamespace(stdout=json.dumps(acl_document))

    monkeypatch.setattr(subprocess, "run", query)
    BackupAccess.windows(path)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "case", ["owner", "everyone", "users", "null", "missing", "sid", "rights", "allowed", "unknown"]
)
def test_windows_owner_and_access_rejections(
    tmp_path: Path, monkeypatch: Any, acl_document: dict[str, Any], case: str
) -> None:
    """Reject broad access, wrong ownership, missing ACLs, and unparseable rule evidence."""
    if case == "owner":
        acl_document["owner"] = "S-1-5-21-1-2-3-1002"
    elif case in ("everyone", "users"):
        sid = "S-1-1-0" if case == "everyone" else "S-1-5-32-545"
        acl_document["rules"].append({"sid": sid, "allowed": True, "rights": 1})
    elif case == "null":
        acl_document["null_dacl"] = True
    elif case == "missing":
        acl_document["rules"] = []
    elif case == "sid":
        acl_document["current"] = "owner-name"
    else:
        acl_document["rules"][0][case] = "invalid"
    monkeypatch.setattr(BackupAccess, "windows_document", lambda path: acl_document)
    with pytest.raises(PolicyError):
        BackupAccess.windows(tmp_path)


@pytest.mark.parametrize(
    "failure", ["missing-root", "relative-root", "unavailable", "timeout", "failure", "empty", "malformed", "oversized"]
)
def test_windows_acl_unavailable_or_invalid_report_fails(tmp_path: Path, monkeypatch: Any, failure: str) -> None:
    """No platform failure can become permission success or disclose diagnostic text."""
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    if failure == "missing-root":
        monkeypatch.delenv("SystemRoot")
    elif failure == "relative-root":
        monkeypatch.setenv("SystemRoot", "relative-system-directory")

    def query(*args: Any, **kwargs: Any) -> Any:
        """Simulate failures from the fixed security query without external processes."""
        if failure == "unavailable":
            raise OSError("private-fixture")
        if failure == "timeout":
            raise subprocess.TimeoutExpired("private-fixture", 10)
        if failure == "failure":
            raise subprocess.CalledProcessError(1, "private-fixture", stderr="private-fixture")
        content = {"empty": b"", "malformed": b"bad json", "oversized": b" " * (1024 * 1024 + 1)}
        return SimpleNamespace(stdout=content.get(failure, b"[]").decode())

    monkeypatch.setattr(subprocess, "run", query)
    with pytest.raises(PolicyError) as error:
        BackupAccess.windows(tmp_path)
    assert "private-fixture" not in str(error.value)


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("attributes", [0, stat.FILE_ATTRIBUTE_REPARSE_POINT, None])
def test_windows_private_file_branch_requires_the_acl_query(
    tmp_path: Path, monkeypatch: Any, directory: bool, attributes: int | None
) -> None:
    """Reject junctions, reparse files, and missing Windows evidence before ACL lookup."""
    path = tmp_path / "private.json"
    path.mkdir() if directory else path.write_text("{}")
    original = path.lstat()
    status = SimpleNamespace(st_mode=original.st_mode, st_nlink=original.st_nlink)
    if attributes is not None:
        status.st_file_attributes = attributes
    calls: list[Path] = []
    monkeypatch.setattr(BackupAccess, "windows", lambda value: calls.append(value))
    with monkeypatch.context() as context:
        context.setattr("src.operations.execution.firmware_policy.recovery.backup.sys.platform", "win32")
        context.delattr("src.operations.execution.firmware_policy.recovery.backup.os.getuid", raising=False)
        if attributes == 0:
            BackupAccess.verify(path, directory=directory, status=status)
        else:
            with pytest.raises(PolicyError, match="without reparse points"):
                BackupAccess.verify(path, directory=directory, status=status)
    assert calls == ([path] if attributes == 0 else [])


@pytest.mark.parametrize("platform", ["linux", "darwin"])
@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("access", [(1001, 0o700), (1002, 0o700), (1001, 0o750), (1001, 0o704)])
def test_posix_private_access_requires_current_owner_and_private_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str, directory: bool, access: tuple[int, int]
) -> None:
    """Keep POSIX owner and access checks independent of the Windows ACL query."""
    owner, mode = access
    path = tmp_path / "private.json"
    status = SimpleNamespace(st_mode=(stat.S_IFDIR if directory else stat.S_IFREG) | mode, st_nlink=1, st_uid=owner)
    calls: list[Path] = []
    monkeypatch.setattr(BackupAccess, "windows", lambda value: calls.append(value))
    with monkeypatch.context() as context:
        context.setattr("src.operations.execution.firmware_policy.recovery.backup.sys.platform", platform)
        context.setattr(
            "src.operations.execution.firmware_policy.recovery.backup.os.getuid", lambda: 1001, raising=False
        )
        if owner == 1001 and mode == 0o700:
            BackupAccess.verify(path, directory=directory, status=status)
        else:
            with pytest.raises(PolicyError, match="different account or permits access"):
                BackupAccess.verify(path, directory=directory, status=status)
    assert calls == []
