"""Save complete settings and verify private backups before any Mist settings change."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import stat

# The fixed Windows security query never includes caller-controlled command text.
import subprocess  # nosec B404
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..sdk import PolicyError

logger = logging.getLogger(__name__)


@dataclass
class BackupProof:
    """Bind a durable recovery file to one unchanged, single-use plan."""

    path: Path
    records: list[dict[str, Any]] = field(repr=False)
    binding: str = ""
    consumed: bool = False
    lock: Any = field(default_factory=threading.Lock, repr=False, compare=False)
    fingerprint: tuple[int, ...] = field(default=(), repr=False)

    def verify(self, backup: PolicyBackup, records: list[dict[str, Any]], binding: str) -> None:
        """Reject another plan, a consumed proof, or a changed durable backup."""
        with self.lock:  # Prevent concurrent callers from consuming one prepared operation twice.
            if self.consumed or self.records != records or self.binding != binding:
                raise PolicyError("The recovery proof is consumed or belongs to another plan.")
            try:
                before = self.identity(self.path.lstat())
                backup.verify(self.path, records)  # Recheck private durable recovery before consumption.
                self.fingerprint = self.identity(self.path.lstat())
            except OSError:
                raise PolicyError("The recovery backup could not be verified.") from None
            if before != self.fingerprint:
                raise PolicyError("The recovery backup changed during verification.")
            self.consumed = True  # Never reuse a proof after the apply boundary.

    @staticmethod
    def identity(status: os.stat_result) -> tuple[int, ...]:
        """Retain file identity and change time for constant-time recovery freshness."""
        return (status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns)

    def ensure(self, backup: PolicyBackup) -> None:
        """Require the verified complete recovery file to remain private before each write."""
        try:
            BackupAccess.verify(backup.root, directory=True)
            status = self.path.lstat()
            BackupAccess.verify(self.path, status=status)
            if not self.consumed or self.identity(status) != self.fingerprint:
                raise PolicyError("The verified recovery backup changed. Changes can remain.")
        except OSError:
            raise PolicyError("The verified recovery backup is unavailable. Changes can remain.") from None


BACKUP_DIRECTORY = ".firmware-policy-backups"
WINDOWS_ACL_QUERY = """
$ErrorActionPreference = 'Stop'
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$acl = Get-Acl -LiteralPath $env:MISTHELPER_BACKUP_ACL_PATH
$raw = [System.Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(), 0)
$rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]) |
    ForEach-Object { @{sid=$_.IdentityReference.Value;
        allowed=($_.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Allow);
        rights=[int64]$_.FileSystemRights} })
@{owner=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value;
  current=$identity; null_dacl=($null -eq $raw.DiscretionaryAcl); rules=$rules} |
    ConvertTo-Json -Depth 4 -Compress
"""


class BackupAccess:
    """Prove platform-specific ownership and private access without changing permissions."""

    @staticmethod
    def windows_document(path: Path) -> dict[str, Any]:
        """Run a fixed Windows ACL query with a literal path outside command text."""
        root = os.environ.get("SystemRoot")
        if not root or not Path(root).is_absolute():
            raise PolicyError("The Windows system directory is unavailable. Backup access cannot be verified.")
        executable = Path(root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        environment = {**os.environ, "MISTHELPER_BACKUP_ACL_PATH": str(path)}
        try:
            # The fixed command receives the path only as a literal environment value.
            result = subprocess.run(  # nosec B603
                [str(executable), "-NoProfile", "-NonInteractive", "-Command", WINDOWS_ACL_QUERY],
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            if len(result.stdout) > 1024 * 1024:
                raise PolicyError("The Windows backup access report exceeds its size limit.")
            document = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, ValueError):
            raise PolicyError("Windows backup ownership and access could not be verified.") from None
        if not isinstance(document, dict):
            raise PolicyError("The Windows backup access report is invalid.")
        return document

    @staticmethod
    def windows(path: Path) -> None:
        """Permit only the current owner, SYSTEM, and the local Administrators group."""
        logger.info("Verify Windows private backup ownership and access")
        document = BackupAccess.windows_document(path)
        current = BackupAccess.sid(document.get("current"))
        if document.get("owner") != current or document.get("null_dacl") is not False:
            raise PolicyError("The Windows backup has another owner or unrestricted access.")
        rules = document.get("rules")
        if not isinstance(rules, list) or not 1 <= len(rules) <= 4096:
            raise PolicyError("The Windows backup access rules are unavailable or invalid.")
        for rule in rules:
            BackupAccess.windows_rule(rule, {current, "S-1-5-18", "S-1-5-32-544"})
        logger.debug("Verified %s Windows private backup access rules", len(rules))

    @staticmethod
    def windows_rule(rule: Any, permitted: set[str]) -> None:
        """Reject malformed rules and every nonprivileged account access grant."""
        if not isinstance(rule, dict) or set(rule) != {"sid", "allowed", "rights"}:
            raise PolicyError("A Windows backup access rule is invalid.")
        sid = BackupAccess.sid(rule["sid"])
        allowed, rights = rule["allowed"], rule["rights"]
        if not isinstance(allowed, bool) or not isinstance(rights, int) or isinstance(rights, bool):
            raise PolicyError("A Windows backup access rule has invalid rights.")
        if not 0 <= rights <= 0xFFFFFFFF or (allowed and rights and sid not in permitted):
            raise PolicyError("The Windows backup permits access from another account.")

    @staticmethod
    def sid(value: Any) -> str:
        """Require an untranslated security identifier before an access comparison."""
        if not isinstance(value, str) or not re.fullmatch(r"S-\d+(?:-\d+){1,15}", value):
            raise PolicyError("A Windows backup account identifier is invalid.")
        return value

    @staticmethod
    def verify(path: Path, directory: bool = False, status: os.stat_result | None = None) -> None:
        """Require an owned private directory or an owned regular file with one link."""
        status = path.lstat() if status is None else status
        expected = stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode)
        if not expected or (not directory and status.st_nlink != 1):
            raise PolicyError("The backup must be a private regular file with one link.")
        if os.name == "nt":
            attributes = getattr(status, "st_file_attributes", stat.FILE_ATTRIBUTE_REPARSE_POINT)
            if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise PolicyError("Windows backup access requires verified attributes without reparse points.")
            BackupAccess.windows(path)
        elif status.st_uid != os.getuid() or status.st_mode & 0o077:
            raise PolicyError("The backup belongs to a different account or permits access from another account.")


class PolicyBackup:
    """Create a private, unique settings bundle and prove its read-back contents."""

    def __init__(self, data_directory: Path) -> None:
        """Locate the ignored product data root without touching an earlier backup."""
        self.root = data_directory.resolve() / BACKUP_DIRECTORY  # Keep backups inside product data storage.

    @staticmethod
    def digest(records: list[dict[str, Any]]) -> str:
        """Hash canonical complete records so verification detects content changes."""
        try:
            digest = hashlib.sha256(b"[")  # Match the legacy canonical list without aggregate serialization.
            encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
            for index, record in enumerate(records):  # Bound serialization to each record.
                if index:
                    digest.update(b",")
                for chunk in encoder.iterencode(record):
                    digest.update(chunk.encode("utf-8"))
            digest.update(b"]")
        except (TypeError, ValueError) as error:
            logger.error("Firmware policy backup contains invalid JSON values: %s", type(error).__name__)
            raise PolicyError("The complete settings cannot be serialized into a valid backup.") from None
        return digest.hexdigest()  # Record integrity without revealing settings.

    def save(self, records: list[dict[str, Any]]) -> Path:
        """Write every target's settings before the workflow can send its first change."""
        logger.info("Save firmware policy backup for %s settings records", len(records))
        document = {  # Retain complete settings, not only the targeted auto-upgrade policy.
            "created_at": datetime.now(UTC).isoformat(),
            "record_count": len(records),
            "sha256": self.digest(records),
            "records": records,
        }
        path = self._create_file(document)  # Exclusive creation preserves every previous backup.
        self.verify(path, records)  # The write alone does not satisfy the backup gate.
        logger.debug("Verified firmware policy backup for %s settings records", len(records))
        return path  # Only the local operator receives its location.

    def _create_file(self, document: dict[str, Any]) -> Path:
        """Restrict local permissions and flush the unique bundle before verification."""
        try:
            if self.root.is_symlink():
                raise PolicyError("The private backup directory must not be a symbolic link.")
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)  # Do not use public product-output permissions.
            if os.name != "nt":
                self.root.chmod(0o700)  # Restrict this feature-owned private directory.
            BackupAccess.verify(self.root, directory=True)
            path = self.root / f"{uuid4()}.json"  # A new bundle cannot overwrite an earlier backup.
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)  # Refuse an existing path.
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                BackupAccess.verify(path)
                json.dump(document, stream, sort_keys=True, allow_nan=False)  # Serialize full settings privately.
                stream.flush()  # Send the complete JSON to the operating system.
                os.fsync(stream.fileno())  # Flush the file before any cloud write.
            return path  # The caller must verify the content before using it.
        except (OSError, TypeError, ValueError) as error:
            logger.error("Firmware policy backup write failed: %s", type(error).__name__)
            raise PolicyError("The settings backup could not be written. No settings change is permitted.") from None

    def verify(self, path: Path, expected: list[dict[str, Any]]) -> None:
        """Read the complete bundle and compare every original setting and identifier."""
        logger.info("Verify firmware policy backup for %s settings records", len(expected))
        try:
            if path.is_symlink() or path.parent != self.root:
                raise PolicyError("The backup file is outside the private backup directory.")
            BackupAccess.verify(path)
            from .bundle import BundleFiles  # Defer the dependency because bundles use the backup writer.

            try:
                document = BundleFiles(self).read(path.stem)  # Validate each record and the private descriptor.
            except PolicyError:
                raise PolicyError(
                    "The settings backup could not be verified and does not match the original settings."
                ) from None
            valid = (  # Verify all records, their count, and their canonical checksum.
                document.records == expected and document.checksum == self.digest(expected)
            )
            if not valid:
                raise PolicyError("The settings backup does not match the original settings.")
        except (OSError, TypeError, ValueError) as error:
            logger.error("Firmware policy backup read failed: %s", type(error).__name__)
            raise PolicyError("The settings backup could not be verified. No settings change is permitted.") from None
        logger.debug("Verified %s complete settings backup records", len(expected))
