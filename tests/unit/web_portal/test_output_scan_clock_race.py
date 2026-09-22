"""Tests that the output scan never loses a report to a clock disagreement.

Issue #3172 recorded a lost report. The run-start mark came from the wall
clock, and every file carries a time from the filesystem clock. The two
clocks do not agree.

Measured on Windows over 300 writes, a report written right after the
mark carried a time up to 194500 nanoseconds BEFORE it. The strict
comparison then dropped it, and the operator never saw the file the
operation had just written.

My first repair was wrong. I believed a Python float rounded the two
instants together, so I changed both values to integer nanoseconds. That
made the loss rate worse, from 3.10 percent to 4.20 percent, because the
cause was the disagreement between two clocks and not the rounding.

The mark now comes from a probe file, so one clock dates the mark and
every report. Measured over 1500 attempts of each case:

    wall clock, strict >   lost 118   reported in error 0
    wall clock, >=         lost  36   reported in error 0
    probe file, strict >   lost   0   reported in error 0
    probe file, >=         lost   0   reported in error 14

Each test below repeats the race many times, because a single pass never
showed the defect.
"""

import time

import pytest

from web_portal.services.output_scan import OutputFileScanner

# Repetitions for each race test. One pass proves nothing, because the
# original defect appeared on roughly one run in a hundred on Windows.
RACE_ATTEMPTS = 200


def test_a_report_written_right_after_the_mark_always_appears(tmp_path):
    """A file written immediately after snapshot() reaches the list every time."""
    misses = []  # Collect every failed attempt, so one failure reports the rate.
    for attempt in range(RACE_ATTEMPTS):
        root = tmp_path / f"run{attempt}"  # A fresh root keeps each attempt independent.
        root.mkdir()
        scanner = OutputFileScanner(str(root))
        scanner.snapshot()  # Mark the run start.
        (root / "Report.csv").write_text("a,b\n", encoding="utf-8")  # Write with no delay at all.
        if scanner.changed_files() != ["Report.csv"]:
            misses.append(attempt)  # Record the attempt that lost the report.
    assert not misses, f"the scanner lost the report on {len(misses)} of {RACE_ATTEMPTS} attempts"


def test_a_report_in_a_subdirectory_always_appears(tmp_path):
    """The subdirectory case is the one the continuous integration run failed."""
    misses = []  # Collect every failed attempt, so one failure reports the rate.
    for attempt in range(RACE_ATTEMPTS):
        root = tmp_path / f"run{attempt}"  # A fresh root keeps each attempt independent.
        nested = root / "per-host-logs"
        nested.mkdir(parents=True)
        scanner = OutputFileScanner(str(root))
        scanner.snapshot()  # Mark the run start.
        (nested / "switch1.log").write_text("ok", encoding="utf-8")  # Write with no delay at all.
        if scanner.changed_files() != ["per-host-logs/switch1.log"]:
            misses.append(attempt)  # Record the attempt that lost the report.
    assert not misses, f"the scanner lost the report on {len(misses)} of {RACE_ATTEMPTS} attempts"


def test_a_file_written_before_the_mark_never_appears(tmp_path):
    """The repair must not widen the window and report an untouched file."""
    # This is the opposite error. A wider window would show a file the run
    # never wrote, and an operator would open the wrong report.
    false_reports = []  # Collect every attempt that reported an untouched file.
    for attempt in range(RACE_ATTEMPTS):
        root = tmp_path / f"run{attempt}"  # A fresh root keeps each attempt independent.
        root.mkdir()
        (root / "older.csv").write_text("a,b\n", encoding="utf-8")  # Write before the mark.
        scanner = OutputFileScanner(str(root))
        scanner.snapshot()  # Mark the run start after the file already exists.
        if scanner.changed_files() != []:
            false_reports.append(attempt)  # Record the attempt that reported the old file.
    assert not false_reports, f"the scanner reported an untouched file on {len(false_reports)} attempts"


def test_the_mark_is_an_integer_count_of_nanoseconds(tmp_path):
    """The mark holds integer nanoseconds, so no rounding can tie two instants."""
    scanner = OutputFileScanner(str(tmp_path))
    scanner.snapshot()  # Run the code under test.
    # A float mark is the defect itself, so the type is part of the contract.
    assert isinstance(scanner._started_at, int)
    # A nanosecond count of the current era is a 19 digit number. A second
    # count is 10 digits, so this comparison catches a unit mistake.
    assert scanner._started_at > 1_000_000_000_000_000_000


def test_every_recorded_time_is_an_integer_count_of_nanoseconds(tmp_path):
    """Each file time holds integer nanoseconds, matching the mark."""
    (tmp_path / "a.csv").write_text("x", encoding="utf-8")  # Give the walk one file to read.
    (tmp_path / "b.csv").write_text("y", encoding="utf-8")  # A second file proves the walk reads them all.
    scanner = OutputFileScanner(str(tmp_path))
    state = scanner._read_state()  # Run the code under test.
    assert sorted(state) == ["a.csv", "b.csv"]  # The walk must return both files and nothing else.
    for name, stamp in state.items():
        assert isinstance(stamp, int), f"{name} carries a float time, which can round"
        assert stamp > 1_000_000_000_000_000_000  # The value must be nanoseconds, not seconds.


@pytest.mark.parametrize("gap_seconds", [0.0, 0.000001, 0.001])
def test_a_report_appears_whatever_the_delay(tmp_path, gap_seconds):
    """The scanner finds the report with no delay and with a small delay."""
    # A delay used to hide the defect, so the zero case is the important one.
    root = tmp_path / f"gap{gap_seconds}"
    root.mkdir()
    scanner = OutputFileScanner(str(root))
    scanner.snapshot()  # Mark the run start.
    if gap_seconds:
        time.sleep(gap_seconds)  # Wait the requested time before the write.
    (root / "Report.csv").write_text("a,b\n", encoding="utf-8")  # Write the report.
    assert scanner.changed_files() == ["Report.csv"]


def test_the_probe_file_never_reaches_the_result_panel(tmp_path):
    """The probe the mark needs must not appear as an operation report."""
    scanner = OutputFileScanner(str(tmp_path))
    scanner.snapshot()  # Run the code under test, which writes and removes a probe.
    (tmp_path / "Report.csv").write_text("a,b\n", encoding="utf-8")  # Write one real report.
    assert scanner.changed_files() == ["Report.csv"]  # The probe must not join the list.


def test_the_probe_file_is_removed_from_the_data_root(tmp_path):
    """The probe leaves no file behind, so the data directory stays clean."""
    scanner = OutputFileScanner(str(tmp_path))
    scanner.snapshot()  # Run the code under test.
    leftovers = [path.name for path in tmp_path.iterdir()]  # Read what the mark left on disk.
    assert leftovers == []  # A leftover probe would grow the data directory on every run.


def test_a_missing_root_falls_back_without_raising(tmp_path):
    """A root that cannot hold a probe still produces a usable mark."""
    # The portal may start before the data directory exists, and a raise here
    # would end the run before the operation did any work.
    scanner = OutputFileScanner(str(tmp_path / "absent"))
    scanner.snapshot()  # Run the code under test against a missing directory.
    assert isinstance(scanner._started_at, int)  # The fallback must still give a mark.
    assert scanner.changed_files() == []  # A missing directory holds no report.
