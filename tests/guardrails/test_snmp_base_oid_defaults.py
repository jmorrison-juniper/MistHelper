"""Guard current SNMP base OID defaults and approved historical evidence."""

from __future__ import annotations  # Keep annotations stable during pytest collection.

import ast  # Read the canonical value without importing product code.
import logging  # Record each external scan action and measured result.
import re  # Find exact OID tokens and current default declarations.
import subprocess  # Ask Git for the tracked file set.
from collections import Counter  # Prove each historical reference exists exactly once.
from dataclasses import dataclass  # Store scan inputs and results with explicit types.
from pathlib import Path, PurePosixPath  # Build portable file paths and tracked names.

import pytest  # Prove the guard fails for bad and empty inputs.

logger = logging.getLogger(__name__)  # Share one logger for the guard diagnostics.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Locate the checkout from this test file.
CANONICAL_SOURCE = PurePosixPath("src/interfaces/monitoring/metrics_gateway/snmp.py")  # Own the fact.
LEGACY_BASE_OID = ".1.3.6.1.4.1.11." + "2147483646"  # Avoid counting the detector as historical evidence.
APPROVED_REFERENCES = frozenset(  # Hold exact historical evidence locations so movement fails.
    {
        ("CHANGELOG.md", 2059),
        ("specs/2159-openapi-mib-generator/data-model.md", 114),
        ("specs/2159-openapi-mib-generator/quickstart.md", 95),
        ("specs/2159-openapi-mib-generator/spec.md", 32),
        ("specs/2159-openapi-mib-generator/spec.md", 216),
        ("specs/3411-docs-audit/audit/slice-a.md", 6),
    }
)
CURRENT_DEFAULT_PATTERNS = {  # Name the current declarations that must equal the canonical value.
    "container/scripts/start.sh": re.compile(
        r"^SNMP_BASE_OID=.*?(?P<oid>\.1(?:\.\d+)+)",
        re.MULTILINE,
    ),
    "specs/2159-openapi-mib-generator/spec.md": re.compile(
        r"^- \*\*FR-017\*\*: The MIB root MUST be `(?P<oid>\.1(?:\.\d+)+)`",
        re.MULTILINE,
    ),
}
LEGACY_PATTERN = re.compile(  # Match the exact old root but not a child OID below it.
    rf"(?<![0-9.]){re.escape(LEGACY_BASE_OID)}(?![0-9.])"
)


@dataclass(frozen=True)
class ScanInput:
    """Name one file and its readable location."""

    relative_path: str  # Keep a stable repository-style path for each report.
    path: Path  # Read the file from this concrete location.


@dataclass(frozen=True)
class OidReference:
    """Name one exact legacy OID occurrence."""

    relative_path: str  # Report the tracked path that holds the occurrence.
    line_number: int  # Report the exact line so approved evidence cannot move.

    @property
    def location(self) -> tuple[str, int]:
        """Return the pair used by the exact historical allowlist."""
        return self.relative_path, self.line_number  # Compare the path and line as one identity.


@dataclass(frozen=True)
class ScanReport:
    """Hold the measured scope, classifications, and blocking findings."""

    scanned_files: int  # Count each supplied file so zero input cannot pass.
    found_references: int  # Count each exact legacy or divergent current reference.
    approved_references: int  # Count historical references at their approved locations.
    unapproved_references: int  # Count references that have no current approval.
    findings: tuple[str, ...]  # Name each missing, moved, or divergent reference.

    def proof_line(self) -> str:
        """Return the stable ASCII measurement line for CI and review evidence."""
        status = "fail" if self.scanned_files == 0 or self.findings else "pass"  # State the decision.
        return (  # Keep the result on one stable line for direct comparison.
            f"snmp_base_oid_guard: scanned_files={self.scanned_files} "
            f"references={self.found_references} approved={self.approved_references} "
            f"unapproved={self.unapproved_references} status={status}"
        )

    def check(self) -> None:
        """Raise with exact evidence when the scan cannot report green."""
        if self.scanned_files == 0:  # A guard that reads no files proves nothing.
            raise ValueError("snmp base OID guard scanned 0 files")  # Name the empty measurement.
        if self.findings:  # Each missing or divergent reference blocks the guard.
            raise ValueError("\n".join(self.findings))  # Report every path in one repair list.


class SnmpBaseOidScanner:
    """Compare current SNMP defaults with the canonical source declaration."""

    @classmethod
    def tracked_inputs(cls, root: Path) -> tuple[ScanInput, ...]:
        """Return every tracked file from Git in deterministic order."""
        logger.info("Listing tracked files under %s", root)  # Log before the external Git request.
        listing = subprocess.run(  # Use Git so untracked output cannot enter the guard.
            ["git", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        paths = tuple(sorted(entry for entry in listing.stdout.split("\0") if entry))  # Remove the final empty entry.
        inputs = tuple(ScanInput(path, root / PurePosixPath(path)) for path in paths)  # Resolve each tracked path.
        logger.debug("The SNMP base OID guard selected %d tracked file(s)", len(inputs))  # Record the scope.
        return inputs  # Return the exact measured file set.

    @classmethod
    def canonical_value(cls, root: Path) -> str:
        """Read the one canonical default from its Python assignment."""
        source_path = root / CANONICAL_SOURCE  # Resolve the source without a platform-specific string.
        logger.info("Reading the canonical SNMP base OID from %s", source_path)  # Log before the read.
        source = source_path.read_text(encoding="utf-8")  # Read the canonical source as project text.
        tree = ast.parse(source, filename=str(source_path))  # Parse the assignment without import side effects.
        values = cls._canonical_assignments(tree)  # Collect exact DEFAULT_BASE_OID string assignments.
        if len(values) != 1:  # A missing or duplicate declaration makes the authority ambiguous.
            raise ValueError(f"expected 1 DEFAULT_BASE_OID assignment, found {len(values)}")
        logger.debug("Read one canonical SNMP base OID assignment")  # Record the successful measurement.
        return values[0]  # Return the source-owned value without a second canonical copy.

    @staticmethod
    def _canonical_assignments(tree: ast.AST) -> tuple[str, ...]:
        """Return string values assigned directly to DEFAULT_BASE_OID."""
        values: list[str] = []  # Collect assignments so duplicates fail visibly.
        for node in ast.walk(tree):  # Find the declaration even if its location moves.
            if not isinstance(node, ast.Assign):  # Only direct assignments can define the constant.
                continue  # Ignore annotations, calls, and references.
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]  # Read simple targets.
            if "DEFAULT_BASE_OID" in names and isinstance(node.value, ast.Constant):  # Match the authority.
                if isinstance(node.value.value, str):  # Require a literal string value.
                    values.append(node.value.value)  # Preserve each declaration for ambiguity checks.
        return tuple(values)  # Return an immutable result for stable decisions.

    @classmethod
    def scan(
        cls,
        inputs: tuple[ScanInput, ...],
        canonical: str,
        enforce_repository_contract: bool,
    ) -> ScanReport:
        """Scan supplied files and optionally enforce the repository allowlist."""
        logger.info("Scanning %d file(s) for SNMP base OID drift", len(inputs))  # Log before file reads.
        texts, read_findings = cls._read_inputs(inputs)  # Read each input once for both scan rules.
        references = cls._legacy_references(texts)  # Find exact old-root occurrences and line numbers.
        approved, unapproved, findings = cls._classify_references(references)  # Classify each old root.
        findings.extend(read_findings)  # A read failure must never shrink the measured scope silently.
        divergent = 0  # Count current defaults that differ without using the known legacy root.
        if enforce_repository_contract:  # Direct proof inputs do not contain the whole repository.
            findings.extend(cls._missing_approvals(references))  # Require each historical entry once.
            current_findings, divergent = cls._current_default_findings(texts, canonical, unapproved)  # Compare.
            findings.extend(current_findings)  # Add missing and divergent current declarations.
        report = ScanReport(  # Store all counts used by the stable proof line.
            len(inputs),
            len(references) + divergent,
            approved,
            len(unapproved) + divergent,
            tuple(sorted(set(findings))),
        )
        logger.debug("The SNMP base OID scan found %d blocking issue(s)", len(report.findings))  # Record result.
        return report  # Return the complete measurement and decision evidence.

    @staticmethod
    def _read_inputs(inputs: tuple[ScanInput, ...]) -> tuple[dict[str, str], list[str]]:
        """Read each scan input and report any unreadable file."""
        texts: dict[str, str] = {}  # Keep one decoded text body for each readable input.
        findings: list[str] = []  # Keep read failures visible to the final decision.
        for scan_input in inputs:  # Read each measured path exactly once.
            try:  # Convert binary and text files to searchable text without encoding assumptions.
                texts[scan_input.relative_path] = scan_input.path.read_bytes().decode("utf-8", errors="ignore")
            except OSError as error:  # A missing tracked file can hide a stale reference.
                findings.append(f"{scan_input.relative_path}: read failure: {error}")  # Name the hidden input.
        return texts, findings  # Return the readable content and each explicit failure.

    @staticmethod
    def _legacy_references(texts: dict[str, str]) -> tuple[OidReference, ...]:
        """Return each exact legacy root occurrence in deterministic order."""
        references: list[OidReference] = []  # Collect all occurrences so duplicates stay visible.
        for relative_path, text in sorted(texts.items()):  # Keep paths stable across platforms.
            for line_number, line in enumerate(text.splitlines(), start=1):  # Preserve exact source lines.
                references.extend(  # Add one record for each occurrence on this line.
                    OidReference(relative_path, line_number) for _match in LEGACY_PATTERN.finditer(line)
                )
        return tuple(references)  # Return an immutable ordered measurement.

    @staticmethod
    def _classify_references(
        references: tuple[OidReference, ...],
    ) -> tuple[int, tuple[OidReference, ...], list[str]]:
        """Separate approved historical references from unapproved references."""
        approved = sum(reference.location in APPROVED_REFERENCES for reference in references)  # Count approvals.
        unapproved = tuple(reference for reference in references if reference.location not in APPROVED_REFERENCES)
        findings = [  # Name each unapproved location and its exact stale value.
            f"{reference.relative_path}:{reference.line_number}: unapproved legacy base OID {LEGACY_BASE_OID}"
            for reference in unapproved
        ]
        return approved, unapproved, findings  # Return counts, records, and blocking messages.

    @staticmethod
    def _missing_approvals(references: tuple[OidReference, ...]) -> list[str]:
        """Report an approved historical reference that moved or disappeared."""
        counts = Counter(reference.location for reference in references)  # Count exact path and line pairs.
        findings: list[str] = []  # Collect missing and duplicate approved evidence.
        for relative_path, line_number in sorted(APPROVED_REFERENCES):  # Keep failure order deterministic.
            count = counts[(relative_path, line_number)]  # Read the measured count for this exact location.
            if count != 1:  # One occurrence must remain until a recorded decision changes the allowlist.
                findings.append(f"{relative_path}:{line_number}: approved legacy reference count is {count}")
        return findings  # Return each allowlist integrity failure.

    @classmethod
    def _current_default_findings(
        cls,
        texts: dict[str, str],
        canonical: str,
        legacy_unapproved: tuple[OidReference, ...],
    ) -> tuple[list[str], int]:
        """Report missing or divergent current default declarations."""
        legacy_locations = {reference.location for reference in legacy_unapproved}  # Avoid double counting old roots.
        findings: list[str] = []  # Collect current declaration failures.
        divergent = 0  # Count only divergent values not already counted as legacy references.
        for relative_path, pattern in CURRENT_DEFAULT_PATTERNS.items():  # Check each owned current declaration.
            path_findings, path_divergent = cls._check_current_default(
                relative_path,
                texts.get(relative_path),
                pattern,
                canonical,
                legacy_locations,
            )
            findings.extend(path_findings)  # Add each failure for this current declaration.
            divergent += path_divergent  # Add a third-value divergence to the proof counts.
        return findings, divergent  # Return all current failures and additional unapproved references.

    @staticmethod
    def _check_current_default(
        relative_path: str,
        text: str | None,
        pattern: re.Pattern[str],
        canonical: str,
        legacy_locations: set[tuple[str, int]],
    ) -> tuple[list[str], int]:
        """Check one current default declaration against the canonical value."""
        if text is None:  # A missing tracked current file invalidates the repository contract.
            return [f"{relative_path}: current default file is missing"], 0  # Name the missing authority.
        matches = tuple(pattern.finditer(text))  # Require one exact normative declaration.
        if len(matches) != 1:  # A missing or duplicate declaration is ambiguous.
            return [f"{relative_path}: expected 1 current default, found {len(matches)}"], 0
        match = matches[0]  # Read the one current declaration after the count check.
        actual = match.group("oid")  # Extract only the OID value from the declaration.
        line_number = text.count("\n", 0, match.start()) + 1  # Convert the match offset to a source line.
        if actual == canonical:  # A canonical current declaration needs no finding.
            return [], 0  # Report no divergence.
        location = (relative_path, line_number)  # Identify the current declaration for duplicate suppression.
        if location in legacy_locations:  # The legacy scan already counted and reported this exact value.
            return [], 0  # Avoid a duplicate message and duplicate proof count.
        finding = f"{relative_path}:{line_number}: current default {actual} differs from canonical {canonical}"
        return [finding], 1  # Count and report a nonlegacy divergent current value.


class TestSnmpBaseOidDefaults:
    """Verify current defaults and historical evidence stay explicit."""

    def test_tracked_snmp_base_oid_defaults_match_the_canonical_value(self) -> None:
        """Tracked current defaults must match the source-owned canonical value."""
        inputs = SnmpBaseOidScanner.tracked_inputs(REPOSITORY_ROOT)  # Measure tracked files only.
        canonical = SnmpBaseOidScanner.canonical_value(REPOSITORY_ROOT)  # Read the source-owned fact.
        report = SnmpBaseOidScanner.scan(inputs, canonical, enforce_repository_contract=True)  # Check all rules.
        print(report.proof_line())  # Emit stable counts for CI, RED proof, and GREEN proof evidence.
        assert report.scanned_files > 0, "snmp base OID guard scanned 0 files"  # Reject an empty measurement.
        assert not report.findings, "\n".join(report.findings)  # Report each exact blocking location.

    def test_an_unapproved_stale_reference_fails_with_its_exact_path(self, tmp_path: Path) -> None:
        """An unapproved old root must fail and name the supplied temporary file."""
        source_path = tmp_path / "unapproved.md"  # Keep the deliberate defect outside the repository.
        source_path.write_text(f"Current default: {LEGACY_BASE_OID}\n", encoding="utf-8")  # Plant one stale root.
        display_path = "temporary/unapproved.md"  # Give the proof a stable path independent of the host.
        scan_input = ScanInput(display_path, source_path)  # Point the scanner at the temporary file.
        report = SnmpBaseOidScanner.scan((scan_input,), ".1.3.6.1.4.1.8072.0", False)  # Scan direct proof input.
        with pytest.raises(ValueError) as failure:  # The same decision path must reject the defect.
            report.check()  # Raise with the exact unapproved location.
        assert report.unapproved_references == 1, "the RED proof did not count one unapproved reference"
        assert f"{display_path}:1" in str(failure.value), "the RED proof did not name the exact path"

    def test_a_zero_file_scan_fails_instead_of_reporting_green(self) -> None:
        """A guard with no input must fail and state the empty measurement."""
        report = SnmpBaseOidScanner.scan((), ".1.3.6.1.4.1.8072.0", False)  # Exercise the zero-input path.
        with pytest.raises(ValueError) as failure:  # The guard must reject a scan that proves nothing.
            report.check()  # Run the same decision used by the repository assertion.
        assert report.scanned_files == 0, "the zero-input proof did not report zero scanned files"
        assert "scanned 0 files" in str(failure.value), "the zero-input failure did not name the empty scope"
