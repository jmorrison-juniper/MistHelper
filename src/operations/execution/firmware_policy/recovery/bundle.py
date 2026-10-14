"""Validate bounded private legacy bundles without treating checksums as signatures."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ..sdk import PolicyApi, PolicyError, PolicyResponse
from .backup import BackupAccess, PolicyBackup

logger = logging.getLogger(__name__)


class BundleValidation:
    """Reject ambiguous JSON and malformed complete settings records."""

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
        if not isinstance(records, list) or not 1 <= len(records) <= 1000:
            raise PolicyError("The backup must contain between 1 and 1000 records.")
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
            with path.open("rb") as stream:
                BackupAccess.verify(path, status=os.fstat(stream.fileno()))
                if (before.st_dev, before.st_ino) != (
                    os.fstat(stream.fileno()).st_dev,
                    os.fstat(stream.fileno()).st_ino,
                ):
                    raise PolicyError("The backup file changed while it was opened.")
                content = stream.read(8 * 1024 * 1024 + 1)
            return self._decode(token, content)
        except (OSError, ValueError, TypeError, RecursionError):
            logger.error("Private restoration backup could not be read or parsed")
            raise PolicyError("The private backup could not be read or parsed.") from None

    @staticmethod
    def _decode(token: str, content: bytes) -> RestoreBundle:
        """Reject oversized or invalid JSON before accepting any saved record."""
        if len(content) > 8 * 1024 * 1024:
            raise PolicyError("The backup exceeds the 8 MiB size limit.")
        logger.info("Validate private restoration backup")
        document = json.loads(content, object_pairs_hook=BundleValidation.pairs)
        records = BundleValidation.records(document)
        logger.debug("Validated %s private restoration records", len(records))
        return RestoreBundle(token, document["sha256"], records, document["created_at"])

    def list(self) -> list[dict[str, Any]]:
        """List bounded verified bundles without exposing private contents."""
        if not self.backup.root.exists():
            return []
        BackupAccess.verify(self.backup.root, directory=True)
        paths = list(self.backup.root.iterdir())
        if len(paths) > 1000:
            raise PolicyError("The private backup list exceeds 1000 entries.")
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
        organizations = {item["id"] for item in bundle.records if item["scope"] == "org"}
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
    def membership(api: PolicyApi, organizations: set[str]) -> dict[str, list[str]]:
        """Read complete current memberships and reject duplicates or wrong owners."""
        result: dict[str, list[str]] = {}
        for organization in sorted(organizations):
            identifiers = []
            for site in api.sites(organization):
                identifier = PolicyResponse.identifier(site.get("id", ""))
                if site.get("org_id", organization) != organization or identifier in identifiers:
                    raise PolicyError("The current site membership is inconsistent.")
                identifiers.append(identifier)
            result[organization] = sorted(identifiers)
        return result
