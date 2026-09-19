"""Scan shipped skill Markdown for disallowed control bytes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ALLOWED_CONTROL_BYTES = frozenset({0x09, 0x0A, 0x0D})  # Permit tab, newline, and carriage return only.
DISALLOWED_CONTROL_BYTES = frozenset(range(0x20)) - ALLOWED_CONTROL_BYTES | {0x7F}  # Reject hidden controls.


@dataclass(frozen=True)
class ControlByteFinding:
    """Describe one file that contains at least one disallowed control byte."""

    path: Path  # Store the file path so the report names the bad Markdown file.
    offsets: tuple[tuple[int, int], ...]  # Store byte and offset pairs for exact repair evidence.

    def line(self) -> str:
        joined = ", ".join(f"0x{byte:02x}@{offset}" for offset, byte in self.offsets)  # Build compact evidence.
        return f"{self.path}: {joined}"  # Return one stable report line for this file.


@dataclass(frozen=True)
class ControlByteScanReport:
    """Hold the scan result and the measured file count."""

    checked_count: int  # Store how many Markdown files the guard measured.
    findings: tuple[ControlByteFinding, ...]  # Store every file that contains bad control bytes.

    def summary(self) -> str:
        lines = [f"Checked {self.checked_count} Markdown files for disallowed control bytes."]  # State count.
        if self.findings:  # Add exact evidence only when the guard found a bad byte.
            lines.append(f"Found {len(self.findings)} affected files.")  # State affected file count.
            lines.extend(finding.line() for finding in self.findings)  # Add each file and byte offset.
        else:
            lines.append("Found 0 affected files.")  # State that the scan found no affected files.
        return "\n".join(lines)  # Return a report that pytest can print and use in assertions.


class SkillMarkdownControlByteScanner:
    """Scan Markdown files below the skill roots."""

    def scan_roots(self, roots: tuple[Path, ...]) -> ControlByteScanReport:
        files = tuple(self._markdown_files(roots))  # Materialize the file list so zero scans are detectable.
        findings = tuple(finding for path in files if (finding := self._scan_file(path)) is not None)  # Scan files.
        return ControlByteScanReport(len(files), findings)  # Return counts and exact byte offsets.

    def _markdown_files(self, roots: tuple[Path, ...]) -> tuple[Path, ...]:
        files: list[Path] = []  # Accumulate files from every existing skill root.
        for root in roots:  # Visit each root independently so a missing optional root does not hide another root.
            if root.exists():  # Ignore absent roots because some checkouts omit generated skills.
                files.extend(sorted(path for path in root.rglob("*.md") if path.is_file()))  # Add Markdown files.
        return tuple(files)  # Return an immutable list for deterministic scans.

    def _scan_file(self, path: Path) -> ControlByteFinding | None:
        data = path.read_bytes()  # Read bytes so Python never normalizes control characters.
        offsets = tuple(
            (offset, byte) for offset, byte in enumerate(data) if byte in DISALLOWED_CONTROL_BYTES
        )  # Keep each offending byte and its byte offset.
        if not offsets:  # Return no finding when this file is clean.
            return None  # Keep the report compact for clean files.
        return ControlByteFinding(path, offsets)  # Return exact repair evidence for the bad file.
