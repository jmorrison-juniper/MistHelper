"""Cross-artifact analysis for generated SpecKit skill artifacts."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnalysisFinding:
    """One consistency finding from a SpecKit artifact check."""

    finding_id: str
    category: str
    severity: str
    location: str
    summary: str
    recommendation: str


class SpecKitAnalyzer:
    """Run a speckit.analyze-equivalent consistency check."""

    def analyze(self, feature_dir: Path) -> list[AnalysisFinding]:
        """Return cross-artifact consistency findings."""
        logging.info("Analyzing generated SpecKit artifacts")  # Record validation start.
        spec_text = self._read_required(feature_dir / "spec.md")  # Read the required specification.
        plan_text = self._read_required(feature_dir / "plan.md")  # Read the required plan.
        tasks_text = self._read_required(feature_dir / "tasks.md")  # Read the required tasks.
        findings = self._coverage_findings(spec_text, tasks_text)  # Find requirements that no task covers.
        findings.extend(self._placeholder_findings(spec_text, plan_text, tasks_text))  # Find unresolved placeholders.
        logging.debug("Analysis produced %d findings", len(findings))  # Record the finding count.
        return findings

    def render_report(self, feature_dir: Path) -> str:
        """Return the analysis report Markdown."""
        logging.info("Rendering SpecKit analysis report")  # Record report rendering.
        findings = self.analyze(feature_dir)  # Run the real consistency check before writing a report.
        lines = self._report_header(findings)  # Build the fixed report table head.
        lines.extend(self._finding_lines(findings))  # Add one row per finding.
        lines.extend(self._metrics_lines(feature_dir, findings))  # Add coverage metrics for proof.
        logging.debug("Rendered analysis report with %d findings", len(findings))  # Record report result.
        return "\n".join(lines) + "\n"

    def _read_required(self, path: Path) -> str:
        """Read a required artifact or raise a useful error."""
        logging.info("Reading required SpecKit artifact %s", path)  # Record artifact read.
        if not path.exists():
            logging.error("Missing required SpecKit artifact: %s", path)  # Record the missing file with context.
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")  # Read Markdown with a fixed encoding.
        logging.debug("Read %d characters from %s", len(text), path.name)  # Record safe file size.
        return text

    def _coverage_findings(self, spec_text: str, tasks_text: str) -> list[AnalysisFinding]:
        """Return findings for requirements that no task references."""
        logging.info("Checking requirement coverage in tasks")  # Record coverage analysis start.
        requirements = re.findall(r"\*\*(FR-\d{3})\*\*", spec_text)  # Extract explicit requirement identifiers.
        missing = [requirement for requirement in requirements if requirement not in tasks_text]  # Find uncovered ids.
        findings = [
            self._missing_requirement(index, item) for index, item in enumerate(missing, start=1)
        ]  # Build findings.
        logging.debug("Found %d uncovered requirements", len(findings))  # Record coverage gap count.
        return findings

    def _placeholder_findings(self, *texts: str) -> list[AnalysisFinding]:
        """Return findings for unresolved SpecKit placeholders."""
        logging.info("Checking artifacts for unresolved placeholders")  # Record placeholder analysis start.
        joined = "\n".join(texts)  # Combine generated artifacts for a simple placeholder scan.
        patterns = ("[NEEDS CLARIFICATION", "TODO", "TKTK", "???", "[FEATURE]")  # Match high-signal placeholders.
        found = [pattern for pattern in patterns if pattern in joined]  # Keep only placeholders that remain.
        findings = [self._placeholder(index, item) for index, item in enumerate(found, start=1)]  # Build findings.
        logging.debug("Found %d unresolved placeholder groups", len(findings))  # Record placeholder gap count.
        return findings

    def _missing_requirement(self, index: int, requirement: str) -> AnalysisFinding:
        """Return one missing requirement finding."""
        logging.info("Creating a coverage finding")  # Record finding creation.
        finding = AnalysisFinding(  # Build a stable finding value for tests and reports.
            finding_id=f"C{index}",
            category="Coverage Gap",
            severity="CRITICAL",
            location="tasks.md",
            summary=f"Requirement {requirement} has no matching task.",
            recommendation=f"Add a task that references {requirement}.",
        )
        logging.debug("Created coverage finding %s", finding.finding_id)  # Record the finding id.
        return finding

    def _placeholder(self, index: int, marker: str) -> AnalysisFinding:
        """Return one unresolved placeholder finding."""
        logging.info("Creating a placeholder finding")  # Record finding creation.
        finding = AnalysisFinding(  # Build a stable finding value for tests and reports.
            finding_id=f"P{index}",
            category="Ambiguity",
            severity="HIGH",
            location="generated artifacts",
            summary=f"Placeholder marker {marker} remains in the artifact set.",
            recommendation="Replace the placeholder with a concrete skill requirement.",
        )
        logging.debug("Created placeholder finding %s", finding.finding_id)  # Record the finding id.
        return finding

    def _report_header(self, findings: list[AnalysisFinding]) -> list[str]:
        """Return the fixed analysis report header."""
        logging.info("Building the analysis report header")  # Record header rendering.
        status = "PASS" if not findings else "FAIL"  # Summarize whether implementation can proceed.
        lines = ["# Specification Analysis Report", "", f"Status: {status}", ""]  # Add the report title.
        lines.extend(
            ["| ID | Category | Severity | Location | Summary | Recommendation |", "| - | - | - | - | - | - |"]
        )
        logging.debug("Built analysis report header with status %s", status)  # Record the status.
        return lines

    def _finding_lines(self, findings: list[AnalysisFinding]) -> list[str]:
        """Return Markdown table rows for findings."""
        logging.info("Rendering analysis finding rows")  # Record finding row rendering.
        rows = [self._finding_line(finding) for finding in findings]  # Render all findings consistently.
        logging.debug("Rendered %d analysis finding rows", len(rows))  # Record row count.
        return rows or ["| None | None | None | None | No issues found. | No action required. |"]

    def _finding_line(self, finding: AnalysisFinding) -> str:
        """Return one Markdown finding row."""
        logging.info("Rendering one analysis finding row")  # Record single row rendering.
        row = (  # Keep table rendering deterministic for report tests.
            f"| {finding.finding_id} | {finding.category} | {finding.severity} | "
            f"{finding.location} | {finding.summary} | {finding.recommendation} |"
        )
        logging.debug("Rendered finding row %s", finding.finding_id)  # Record rendered finding id.
        return row

    def _metrics_lines(self, feature_dir: Path, findings: list[AnalysisFinding]) -> list[str]:
        """Return report metric lines."""
        logging.info("Rendering analysis metrics")  # Record metric rendering.
        spec_text = (feature_dir / "spec.md").read_text(encoding="utf-8")  # Read spec for requirement count.
        tasks_text = (feature_dir / "tasks.md").read_text(encoding="utf-8")  # Read tasks for task count.
        requirement_count = len(re.findall(r"\*\*FR-\d{3}\*\*", spec_text))  # Count explicit requirements.
        task_count = len(re.findall(r"^- \[[ xX]\] T\d{3}", tasks_text, re.MULTILINE))  # Count SpecKit tasks.
        logging.debug("Metrics found %d requirements and %d tasks", requirement_count, task_count)  # Record counts.
        return [
            "",
            "## Metrics",
            "",
            f"- Total Requirements: {requirement_count}",
            f"- Total Tasks: {task_count}",
            f"- Critical Issues Count: {self._critical_count(findings)}",
        ]

    def _critical_count(self, findings: list[AnalysisFinding]) -> int:
        """Return the number of critical findings."""
        logging.info("Counting critical analysis findings")  # Record severity count action.
        count = sum(1 for finding in findings if finding.severity == "CRITICAL")  # Count blocking findings.
        logging.debug("Counted %d critical findings", count)  # Record the critical count.
        return count
