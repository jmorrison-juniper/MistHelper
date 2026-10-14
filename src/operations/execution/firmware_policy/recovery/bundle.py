"""Validate bounded private legacy bundles without treating checksums as signatures."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TextIO
from uuid import UUID

from ..sdk import PolicyApi, PolicyError, PolicyResponse
from .backup import BackupAccess, PolicyBackup

logger = logging.getLogger(__name__)


class LegacyStream:
    """Parse the legacy envelope with bounded tokens, records, and nesting."""

    def __init__(self, stream: TextIO) -> None:
        """Keep only a small input chunk while scanning a single record."""
        self.stream = stream  # Retain the verified descriptor rather than reopening its path.
        self.chunk = ""  # Read only a bounded input chunk at a time.
        self.position = 0  # Track the current chunk without copying its remaining content.

    def character(self) -> str:
        """Read one character from a bounded buffered descriptor."""
        if self.position == len(self.chunk):  # Replace only an exhausted chunk.
            self.chunk = self.stream.read(65536)  # Never read the aggregate source into a text value.
            self.position = 0
        if not self.chunk:
            return ""
        value = self.chunk[self.position]  # Inspect one character without growing the input buffer.
        self.position += 1
        return value

    def token(self, first: str) -> tuple[Any, str]:
        """Decode one bounded JSON value and return its envelope delimiter."""
        self.chunk = first + self.chunk[self.position :]  # Retain only the current value and bounded read-ahead.
        self.position = 0
        decoder = json.JSONDecoder(object_pairs_hook=BundleValidation.pairs)
        while True:
            try:
                value, end = decoder.raw_decode(self.chunk)
                if end > 8 * 1024 * 1024:
                    raise PolicyError("A backup record exceeds the 8 MiB record resource limit.")
                if end == len(self.chunk):
                    continuation = self.stream.read(65536)  # A number can continue across an input chunk boundary.
                    if continuation:
                        self.chunk += continuation
                        continue
                self.position = end
                BundleValidation.structure(value)  # Bound nested record structure before workflow processing.
                return value, self.significant()
            except json.JSONDecodeError:
                if len(self.chunk) > 8 * 1024 * 1024:
                    raise PolicyError("A backup record exceeds the 8 MiB record resource limit.") from None
                chunk = self.stream.read(65536)  # Accumulate no more than one bounded value.
                if not chunk:
                    raise
                self.chunk += chunk

    def significant(self) -> str:
        """Ignore JSON whitespace without consuming the next structural character."""
        character = self.character()
        while character and character in " \t\r\n":
            character = self.character()
        return character

    def document(self) -> dict[str, Any]:
        """Accept each envelope member once and decode records independently."""
        if self.significant() != "{":
            raise ValueError("The backup format is not supported.")
        document: dict[str, Any] = {}
        delimiter = ","
        while delimiter == ",":
            key, delimiter = self.key()
            if key in document:
                raise PolicyError("The backup contains duplicate JSON keys.")
            if key == "records":
                document[key], delimiter = self.records()
            else:
                document[key], delimiter = self.token(self.significant())
            if key not in {"created_at", "record_count", "sha256", "records"}:
                raise PolicyError("The backup format is not supported.")
        if delimiter != "}" or self.significant():
            raise PolicyError("The backup has incomplete or trailing content.")
        return document

    def key(self) -> tuple[str, str]:
        """Read a bounded quoted envelope name and its required colon."""
        characters = [self.significant()]
        if characters[0] != '"':
            raise PolicyError("The backup envelope key is invalid.")
        escaped = False
        while len(characters) < 128:
            character = self.character()
            if not character:
                break
            characters.append(character)
            if character == '"' and not escaped:
                key = json.loads("".join(characters))
                if self.significant() != ":":
                    raise PolicyError("The backup envelope separator is invalid.")
                return key, ":"
            escaped = character == "\\" and not escaped
        raise PolicyError("The backup envelope key is invalid.")

    def records(self) -> tuple[list[dict[str, Any]], str]:
        """Decode records without an aggregate byte or record-count threshold."""
        if self.significant() != "[":
            raise PolicyError("The backup records must be an array.")
        records: list[dict[str, Any]] = []
        first = self.significant()
        while first != "]":
            record, delimiter = self.token(first)
            records.append(record)
            if delimiter == "]":
                break
            if delimiter != ",":
                raise PolicyError("The backup records are incomplete.")
            first = self.significant()
            if first == "]":
                raise PolicyError("The backup records have a trailing comma.")
        return records, self.significant()


class BundleValidation:
    """Reject ambiguous JSON and malformed complete settings records."""

    @staticmethod
    def structure(value: Any) -> None:
        """Reject excessively nested records without recursive validation."""
        pending = [(value, 0)]  # Use bounded iterative traversal after the checked JSON decode.
        while pending:
            item, depth = pending.pop()
            if depth > 64:
                raise PolicyError("A backup record exceeds the nesting resource limit.")
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)

    @staticmethod
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        """Reject duplicate keys before JSON can discard a conflicting value."""
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise PolicyError("The backup contains duplicate JSON keys.")
            result[key] = value
        return result

    @staticmethod
    def records(document: Any) -> list[dict[str, Any]]:
        """Check the exact legacy envelope, UTC timestamp, count, and checksum."""
        if not isinstance(document, dict) or set(document) != {"created_at", "record_count", "sha256", "records"}:
            raise PolicyError("The backup format is not supported.")
        records = document["records"]
        if not isinstance(records, list) or not records:
            raise PolicyError("The backup must contain complete records.")
        if (
            not isinstance(document["record_count"], int)
            or isinstance(document["record_count"], bool)
            or document["record_count"] != len(records)
        ):
            raise PolicyError("The backup record count is invalid.")
        BundleValidation.timestamp(document["created_at"])
        if document["sha256"] != PolicyBackup.digest(records):
            raise PolicyError("The backup checksum does not match its records.")
        BundleValidation.identities(records)
        return records

    @staticmethod
    def timestamp(value: Any) -> None:
        """Require a real UTC creation timestamp instead of trusting arbitrary text."""
        try:
            timestamp = datetime.fromisoformat(value)
            if timestamp.utcoffset() != UTC.utcoffset(timestamp):
                raise ValueError
        except (TypeError, ValueError):
            raise PolicyError("The backup creation time must be a UTC timestamp.") from None

    @staticmethod
    def identities(records: list[dict[str, Any]]) -> None:
        """Reject unknown record shapes, duplicates, and mismatched saved identifiers."""
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict) or set(record) != {"scope", "id", "settings"}:
                raise PolicyError("A backup record has an unsupported format.")
            if record["scope"] not in ("org", "site") or not isinstance(record["settings"], dict):
                raise PolicyError("A backup record has an invalid scope or settings object.")
            identifier = PolicyResponse.identifier(record["id"])
            if identifier != record["id"] or identifier in seen:
                raise PolicyError("Backup scope identifiers must be canonical and unique.")
            seen.add(identifier)
            key = "org_id" if record["scope"] == "org" else "site_id"
            if record["settings"].get(key, identifier) != identifier:
                raise PolicyError("A saved settings identifier does not match its backup scope.")


@dataclass
class RestoreBundle:
    """Hold validated settings privately and expose only scope metadata."""

    token: str
    checksum: str
    records: list[dict[str, Any]] = field(repr=False)
    created_at: str
    fingerprint: tuple[int, ...] = field(default=(), repr=False)
    organizations: set[str] = field(default_factory=set, repr=False, compare=False)

    def summary(self) -> dict[str, Any]:
        """Return no names or settings values from an untrusted bundle."""
        return {
            "token": self.token,
            "created_at": self.created_at,
            "record_count": len(self.records),
            "records": [{"scope": record["scope"], "id": record["id"]} for record in self.records],
        }


@dataclass
class BundleFiles:
    """Read only owned private regular files selected by opaque UUID names."""

    backup: PolicyBackup

    def read(self, token: str) -> RestoreBundle:
        """Use a bounded descriptor read and compare file identity before parsing."""
        logger.info("Read a private restoration backup")
        try:
            if not isinstance(token, str) or str(UUID(token)) != token:
                raise PolicyError("Select a valid backup identifier.")
            BackupAccess.verify(self.backup.root, directory=True)
            path = self.backup.root / f"{token}.json"
            before = path.lstat()
            BackupAccess.verify(path, status=before)
            with path.open("r", encoding="utf-8") as stream:
                BackupAccess.verify(path, status=os.fstat(stream.fileno()))
                if (before.st_dev, before.st_ino) != (
                    os.fstat(stream.fileno()).st_dev,
                    os.fstat(stream.fileno()).st_ino,
                ):
                    raise PolicyError("The backup file changed while it was opened.")
                document = LegacyStream(stream).document()  # Bound parsing to each legacy record.
                after = os.fstat(stream.fileno())  # Detect replacement or modification during the read.
                if self.identity(before) != self.identity(after) or self.identity(after) != self.identity(path.lstat()):
                    raise PolicyError("The backup file changed while it was read.")
            records = BundleValidation.records(document)  # Preserve complete integrity and identity checks.
            logger.debug("Validated %s private restoration records", len(records))
            return RestoreBundle(
                token,
                document["sha256"],
                records,
                document["created_at"],
                self.identity(after),
                {record["id"] for record in records if record["scope"] == "org"},
            )
        except (OSError, ValueError, TypeError, RecursionError):
            logger.error("Private restoration backup could not be read or parsed")
            raise PolicyError("The private backup could not be read or parsed.") from None

    @staticmethod
    def identity(status: os.stat_result) -> tuple[int, ...]:
        """Include change time so timestamp restoration cannot conceal a source edit."""
        return (status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns)

    def unchanged(self, bundle: RestoreBundle) -> None:
        """Check private source identity at every write without parsing all records again."""
        BackupAccess.verify(self.backup.root, directory=True)
        path = self.backup.root / f"{bundle.token}.json"
        try:
            status = path.lstat()
            BackupAccess.verify(path, status=status)
            if self.identity(status) != bundle.fingerprint:
                raise PolicyError("The source backup changed during restoration. Changes can remain.")
        except OSError:
            raise PolicyError("The source backup is unavailable. Changes can remain.") from None

    def list(self) -> list[dict[str, Any]]:
        """List bounded verified bundles without exposing private contents."""
        if not self.backup.root.exists():
            return []
        BackupAccess.verify(self.backup.root, directory=True)
        paths = [path for path in self.backup.root.iterdir() if path.suffix == ".json"]
        return [self.read(path.stem).summary() for path in sorted(paths)]


class RestoreSelection:
    """Bind selected legacy records to explicit current cloud and saved ownership."""

    @staticmethod
    def cloud(api: PolicyApi) -> str:
        """Expose only a validated SDK hostname, never an arbitrary context value."""
        host = api.session.get_cloud()
        if not isinstance(host, str) or not re.fullmatch(
            r"api(?:\.[a-z0-9-]+)*\.(?:mist\.com|mistsys\.com|mist-federal\.com)", host
        ):
            raise PolicyError("The active Mist cloud could not be validated.")
        return str(host)

    @staticmethod
    def records(bundle: RestoreBundle, selected: Any) -> list[dict[str, Any]]:
        """Require explicit unique record choices that belong to the verified bundle."""
        if not isinstance(selected, list) or not selected or len(selected) > len(bundle.records):
            raise PolicyError("Select saved organization and site records.")
        available = {f"{record['scope']}:{record['id']}": record for record in bundle.records}
        if any(not isinstance(key, str) or key not in available for key in selected):
            raise PolicyError("A selected record does not belong to the backup.")
        if len(set(selected)) != len(selected):
            raise PolicyError("Select each backup record only once.")
        return sorted([available[key] for key in selected], key=lambda record: (record["scope"], record["id"]))

    @staticmethod
    def ownership(bundle: RestoreBundle, record: dict[str, Any]) -> str:
        """Use saved ownership or the only unambiguous legacy parent organization."""
        organizations = bundle.organizations or {item["id"] for item in bundle.records if item["scope"] == "org"}
        if record["scope"] == "org":
            return PolicyResponse.identifier(record["id"])
        owner = record["settings"].get("org_id")
        if owner is None and len(organizations) == 1:
            owner = next(iter(organizations))
        owner = PolicyResponse.identifier(owner)
        if owner not in organizations:
            raise PolicyError("The saved site ownership is absent, ambiguous, or outside this backup.")
        return PolicyResponse.identifier(owner)

    @staticmethod
    def membership(
        api: PolicyApi, organizations: set[str], listings: dict[str, list[dict[str, Any]]] | None = None
    ) -> dict[str, list[str]]:
        """Read complete current memberships and reject duplicates or wrong owners."""
        result: dict[str, list[str]] = {}
        for organization in sorted(organizations):
            identifiers = []
            seen: set[str] = set()
            for site in listings[organization] if listings is not None else api.sites(organization):
                identifier = PolicyResponse.identifier(site.get("id", ""))
                if site.get("org_id", organization) != organization or identifier in seen:
                    raise PolicyError("The current site membership is inconsistent.")
                identifiers.append(identifier)
                seen.add(identifier)
            result[organization] = sorted(identifiers)
        return result
