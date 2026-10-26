"""Validate transient input and bind proposal review to the browser session."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import NotRequired, TypedDict

from flask import session


class GatewayTemplate(TypedDict):
    """Describe only verified request fields without hardware assumptions."""

    name: str
    type: str
    dns_servers: NotRequired[list[str]]


class UnsupportedItem(TypedDict):
    """Identify source lines without retaining potentially sensitive values."""

    line: int
    command: str
    reason: str


class ConversionProposal(TypedDict):
    """Describe the complete object bound to review and export."""

    gateway_template: GatewayTemplate
    unsupported_items: list[UnsupportedItem]
    known_gaps: list[str]


@dataclass(frozen=True)
class SourceConfiguration:
    """Keep validated source text in memory for one conversion."""

    content: str
    name: str
    kind: str

    @classmethod
    def read(cls, filename: str, content: bytes, name: str, kind: str) -> "SourceConfiguration":
        """Reject unsafe input before constructing a source value."""
        cls._filename(filename)
        if not name.strip() or len(name) > 120 or any(ord(character) < 32 for character in name):
            raise ValueError("Use a template name with 1 to 120 visible characters.")
        if kind not in {"standalone", "spoke"}:
            raise ValueError("Select standalone or spoke.")
        return cls(cls._text(content), name, kind)

    @staticmethod
    def _filename(filename: str) -> None:
        """Reject both platform path forms before checking the text suffix."""
        if not filename or PurePosixPath(filename).name != filename or PureWindowsPath(filename).name != filename:
            raise ValueError("Use a file name without a directory.")
        if ":" in filename or PurePosixPath(filename).suffix.lower() not in {
            ".txt",
            ".conf",
            ".cfg",
            ".ios",
            ".config",
            ".log",
        }:
            raise ValueError("Select a supported text file.")

    @staticmethod
    def _text(content: bytes) -> str:
        """Decode bounded UTF-8 input without a replacement character."""
        if len(content) > 16 * 1024 * 1024:
            raise ValueError("The file exceeds 16 MiB.")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Use a UTF-8 text file.") from error
        if not text.strip() or "\x00" in text:
            raise ValueError("Use nonempty text without null characters.")
        return text


class ReviewState:
    """Store only canonical proposal digests in the signed session."""

    @staticmethod
    def digest(proposal: Mapping[str, object]) -> str:
        """Bind all proposal fields through deterministic JSON encoding."""
        encoded = json.dumps(proposal, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @classmethod
    def publish(cls, proposal: Mapping[str, object]) -> None:
        """Invalidate an earlier review when a preview succeeds."""
        session["cisco_proposal"] = cls.digest(proposal)
        session.pop("cisco_reviewed", None)

    @classmethod
    def verify(cls, proposal: Mapping[str, object], reviewed: bool = False) -> None:
        """Reject a changed, missing, or unreviewed proposal."""
        digest = cls.digest(proposal)
        if session.get("cisco_proposal") != digest:
            raise LookupError("Create a new preview before review or export.")
        if reviewed and session.get("cisco_reviewed") != digest:
            raise LookupError("Review this proposal before export.")

    @classmethod
    def approve(cls, proposal: Mapping[str, object]) -> None:
        """Record approval only for the current proposal."""
        cls.verify(proposal)
        session["cisco_reviewed"] = cls.digest(proposal)
