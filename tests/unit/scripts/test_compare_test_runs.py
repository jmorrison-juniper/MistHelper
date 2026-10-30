"""Tests for required fields in test-run comparison events."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.compare_test_runs import TestComparator


def test_missing_menu_option_fails_visibly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Reject result events without a menu selector instead of skipping them."""
    event_file = tmp_path / "events.jsonl"
    event_file.write_text(
        json.dumps({"event_type": "test_fail", "status": "fail"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exit_info:
        TestComparator().load_events(event_file)

    assert exit_info.value.code == 1
    assert capsys.readouterr().err == (f"Error: Missing menu_option in test_fail event at {event_file}:1\n")


def test_loads_result_event_with_menu_option(tmp_path: Path) -> None:
    """Keep valid result events available to the comparison."""
    event_file = tmp_path / "events.jsonl"
    event = {"event_type": "test_pass", "menu_option": "17", "status": "pass"}
    event_file.write_text(json.dumps(event) + "\n", encoding="utf-8")

    loaded_events = TestComparator().load_events(event_file)

    assert loaded_events["events"] == {"17": event}


def test_empty_event_file_has_no_results(tmp_path: Path) -> None:
    """Keep a valid empty input distinct from a missing result selector."""
    event_file = tmp_path / "events.jsonl"
    event_file.write_bytes(b"")

    loaded_events = TestComparator().load_events(event_file)

    assert loaded_events["events"] == {}
    assert loaded_events["summary"] is None


def test_malformed_json_is_reported_and_skipped(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report malformed records without treating them as result events."""
    event_file = tmp_path / "events.jsonl"
    event_file.write_text("{invalid json}\n", encoding="utf-8")
    parse_error = json.JSONDecodeError("invalid", "", 0)
    monkeypatch.setattr(json, "loads", Mock(side_effect=parse_error))

    loaded_events = TestComparator().load_events(event_file)

    assert loaded_events["events"] == {}
    assert capsys.readouterr().err == f"Warning: Skipping invalid JSON at {event_file}:1\n"
