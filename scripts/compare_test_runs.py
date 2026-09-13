"""Compare two MistHelper NDJSON test event files and report regressions."""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ComparisonItem:
    """A single entry in a TestComparison list."""

    menu_option: str
    run_a_status: str
    run_b_status: str
    operation_name: str = ""
    run_a_duration: float = 0.0
    run_b_duration: float = 0.0
    ratio: float = 0.0
    error_message: str = ""


@dataclass
class TestComparison:
    """Derived analysis comparing two sets of TestEvents."""

    run_a_file: str
    run_b_file: str
    run_a_timestamp: str = ""
    run_b_timestamp: str = ""
    new_failures: list = field(default_factory=list)
    resolved_failures: list = field(default_factory=list)
    timing_regressions: list = field(default_factory=list)
    status_changes: list = field(default_factory=list)


class TestComparator:
    """Reads two JSONL files and reports regressions between test runs."""

    TIMING_THRESHOLD = 2.0

    def load_events(self, file_path):
        """Read JSONL and index TestEvents by menu_option.

        Returns a dict keyed by menu_option with the final
        test_pass/test_fail/test_skip event for each operation,
        plus a 'summary' key if a test_summary event exists.
        """
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        events = {}
        summary = None
        with open(path, encoding="utf-8") as handle:
            for line_num, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    event = json.loads(stripped)
                except json.JSONDecodeError:
                    print(
                        f"Warning: Skipping invalid JSON at " f"{file_path}:{line_num}",
                        file=sys.stderr,
                    )
                    continue

                event_type = event.get("event_type", "")
                if event_type == "test_summary":
                    summary = event
                    continue
                if event_type in ("test_pass", "test_fail", "test_skip"):
                    option = event.get("menu_option", "")
                    if option:
                        events[option] = event

        result = {"events": events, "summary": summary}
        return result

    def compare(self, run_a_path, run_b_path):
        """Produce a TestComparison from two JSONL files.

        Detects new failures, resolved failures, timing regressions
        (>2x slower), and other status changes.
        """
        data_a = self.load_events(run_a_path)
        data_b = self.load_events(run_b_path)

        events_a = data_a["events"]
        events_b = data_b["events"]

        comparison = TestComparison(
            run_a_file=str(run_a_path),
            run_b_file=str(run_b_path),
        )

        comparison.run_a_timestamp = self._extract_timestamp(data_a["summary"], events_a)
        comparison.run_b_timestamp = self._extract_timestamp(data_b["summary"], events_b)

        all_options = sorted(
            set(events_a.keys()) | set(events_b.keys()),
            key=lambda x: int(x) if x.isdigit() else 0,
        )

        for option in all_options:
            event_a = events_a.get(option)
            event_b = events_b.get(option)
            self._classify_change(option, event_a, event_b, comparison)

        return comparison

    def format_report(self, comparison):
        """Produce a human-readable summary of the comparison."""
        lines = []
        lines.append("=" * 60)
        lines.append("MistHelper Test Run Comparison Report")
        lines.append("=" * 60)
        lines.append(f"Run A: {comparison.run_a_file}")
        lines.append(f"  Timestamp: {comparison.run_a_timestamp}")
        lines.append(f"Run B: {comparison.run_b_file}")
        lines.append(f"  Timestamp: {comparison.run_b_timestamp}")
        lines.append("")

        lines.extend(
            self._format_section(
                "NEW FAILURES (passed in A, failed in B)",
                comparison.new_failures,
            )
        )
        lines.extend(
            self._format_section(
                "RESOLVED FAILURES (failed in A, passed in B)",
                comparison.resolved_failures,
            )
        )
        lines.extend(self._format_timing_section(comparison.timing_regressions))
        lines.extend(
            self._format_section(
                "OTHER STATUS CHANGES",
                comparison.status_changes,
            )
        )

        total_issues = len(comparison.new_failures) + len(comparison.timing_regressions)
        lines.append("-" * 60)
        if total_issues == 0:
            lines.append("Result: No regressions detected.")
        else:
            lines.append(f"Result: {total_issues} regression(s) detected.")
        lines.append("")

        return "\n".join(lines)

    def _extract_timestamp(self, summary, events):
        """Get the best available timestamp from summary or events."""
        if summary and summary.get("timestamp"):
            return summary["timestamp"]
        if events:
            timestamps = [ev.get("timestamp", "") for ev in events.values() if ev.get("timestamp")]
            if timestamps:
                return max(timestamps)
        return "unknown"

    def _classify_change(self, option, event_a, event_b, comparison):
        """Classify a single menu option's change between runs."""
        status_a = event_a.get("status", "absent") if event_a else "absent"
        status_b = event_b.get("status", "absent") if event_b else "absent"

        if status_a == status_b:
            self._check_timing(option, event_a, event_b, comparison)
            return

        name = self._get_name(event_a, event_b)
        item = ComparisonItem(
            menu_option=option,
            run_a_status=status_a,
            run_b_status=status_b,
            operation_name=name,
            run_a_duration=self._get_duration(event_a),
            run_b_duration=self._get_duration(event_b),
        )

        if status_b == "fail" and status_a in ("pass", "absent"):
            item.error_message = event_b.get("error_message", "") if event_b else ""
            comparison.new_failures.append(item)
        elif status_a == "fail" and status_b in ("pass", "absent"):
            comparison.resolved_failures.append(item)
        else:
            comparison.status_changes.append(item)

    def _check_timing(self, option, event_a, event_b, comparison):
        """Detect timing regressions for operations with same status."""
        if not event_a or not event_b:
            return
        dur_a = self._get_duration(event_a)
        dur_b = self._get_duration(event_b)
        if dur_a <= 0:
            return
        ratio = dur_b / dur_a
        if ratio > self.TIMING_THRESHOLD:
            item = ComparisonItem(
                menu_option=option,
                run_a_status=event_a.get("status", ""),
                run_b_status=event_b.get("status", ""),
                operation_name=self._get_name(event_a, event_b),
                run_a_duration=dur_a,
                run_b_duration=dur_b,
                ratio=round(ratio, 2),
            )
            comparison.timing_regressions.append(item)

    def _get_name(self, event_a, event_b):
        """Get operation name from whichever event has it."""
        if event_a and event_a.get("operation_name"):
            return event_a["operation_name"]
        if event_b and event_b.get("operation_name"):
            return event_b["operation_name"]
        return ""

    def _get_duration(self, event):
        """Safely extract duration_seconds from an event."""
        if not event:
            return 0.0
        return event.get("duration_seconds", 0.0)

    def _format_section(self, title, items):
        """Format a section of ComparisonItems for display."""
        lines = [f"--- {title} ---"]
        if not items:
            lines.append("  (none)")
        else:
            for item in items:
                label = f"Menu {item.menu_option}"
                if item.operation_name:
                    label += f" ({item.operation_name})"
                label += f": {item.run_a_status} -> {item.run_b_status}"
                if item.error_message:
                    label += f"\n    Error: {item.error_message}"
                lines.append(f"  {label}")
        lines.append("")
        return lines

    def _format_timing_section(self, items):
        """Format timing regressions with ratio details."""
        lines = ["--- TIMING REGRESSIONS (>2x slower) ---"]
        if not items:
            lines.append("  (none)")
        else:
            for item in items:
                label = f"Menu {item.menu_option}"
                if item.operation_name:
                    label += f" ({item.operation_name})"
                label += f": {item.run_a_duration:.2f}s -> " f"{item.run_b_duration:.2f}s " f"({item.ratio}x slower)"
                lines.append(f"  {label}")
        lines.append("")
        return lines


def main():
    """CLI entry point for comparing two test run JSONL files."""
    parser = argparse.ArgumentParser(
        description="Compare two MistHelper test run JSONL files " "and report regressions."
    )
    parser.add_argument(
        "run_a",
        help="Path to the baseline JSONL test events file",
    )
    parser.add_argument(
        "run_b",
        help="Path to the newer JSONL test events file to compare",
    )
    args = parser.parse_args()

    comparator = TestComparator()
    comparison = comparator.compare(args.run_a, args.run_b)
    report = comparator.format_report(comparison)
    print(report)

    has_regressions = len(comparison.new_failures) > 0 or len(comparison.timing_regressions) > 0
    sys.exit(1 if has_regressions else 0)


if __name__ == "__main__":
    main()
