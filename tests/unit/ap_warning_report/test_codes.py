"""Verify code matching without inventing definitions or observation times."""

from copy import deepcopy
from typing import Any

import pytest

from src.operations.exporting.ap_warning_report.codes import CodeDefinitions, RecoveryClassifier, TroubleCode


@pytest.mark.parametrize("value", [None, "", "  ", 0, "0", "00", "000"])
def test_absent_and_zero_codes_are_not_trouble(value: object) -> None:
    """Zero and absent values must not produce report rows."""
    assert TroubleCode.normalize(value) == ""


@pytest.fixture
def recovery_case() -> tuple[dict[str, Any], dict[str, Any]]:
    """Use the screenshot's exact UTC order without depending on AP uptime."""
    trouble = 1794003421.0  # 2026-11-06T22:17:01Z precedes the successful connection.
    candidate = {
        "mac": "000000000001",
        "site_id": "site-one",
        "code": "07",
        "code_key": "NO_DNS_RESPONSE",
        "trouble_timestamp": TroubleCode.timestamp(trouble),
    }
    evidence = {
        "evidence_status": "complete",
        "catalogue_verified": True,
        "history_start": trouble - 3301,
        "history_end": trouble + 299,
        "events": [
            {"mac": candidate["mac"], "timestamp": trouble - 335, "type": "AP_DISCONNECTED"},
            {"ap": candidate["mac"], "timestamp": trouble + 2, "type": "AP_CONNECTED"},
        ],
        "statistics": {
            "mac": candidate["mac"],
            "site_id": "site-one",
            "status": "connected",
            "last_seen": trouble + 295,
            "last_trouble": {"code": "07", "timestamp": trouble},
        },
    }
    return candidate, evidence


def test_screenshot_order_proves_recovery_without_ten_minute_wait(recovery_case: tuple[dict, dict]) -> None:
    """A two-second strict ordering can prove recovery when every other condition holds."""
    candidate, evidence = recovery_case
    result = RecoveryClassifier.classify(candidate, evidence)
    assert result["recovery_status"] == "recovered"
    assert result["recovery_connection_at"] == "2026-11-06T22:17:03+00:00"
    assert result["interruptions_60m"] == 1


def test_fractional_epochs_at_exact_history_boundaries_remain_valid(recovery_case: tuple[dict, dict]) -> None:
    """ISO display rounding must not move valid evidence outside its numeric window."""
    candidate, evidence = recovery_case
    end = 1794003720.1234567
    evidence.update(history_start=end - 3600, history_end=end)
    evidence["events"] = [
        {"mac": candidate["mac"], "timestamp": end - 3600, "type": "AP_DISCONNECTED"},
        {"mac": candidate["mac"], "timestamp": end, "type": "AP_CONNECTED"},
    ]
    evidence["statistics"]["last_seen"] = end
    result = RecoveryClassifier.classify(candidate, evidence)
    assert result["recovery_status"] == "recovered"
    assert result["interruptions_60m"] == 1


@pytest.mark.parametrize("offset", [-1, 0])
def test_equal_or_earlier_reconnect_never_clears_trouble(recovery_case: tuple[dict, dict], offset: int) -> None:
    """Equal timestamps cannot establish the requested event order."""
    candidate, evidence = recovery_case
    evidence["events"][-1]["timestamp"] = 1794003421 + offset
    assert RecoveryClassifier.classify(candidate, evidence)["recovery_reason"] == "connection_not_after_trouble"


@pytest.mark.parametrize("event_type", ["AP_DISCONNECTED", "AP_CONFIG_FAILED", "AP_RESTARTED", "AP_UNASSIGNED"])
def test_newer_blocker_prevents_recovery(recovery_case: tuple[dict, dict], event_type: str) -> None:
    """A later loss or restart cannot be hidden by an earlier reconnect."""
    candidate, evidence = recovery_case
    evidence["events"].append({"mac": candidate["mac"], "timestamp": 1794003424, "type": event_type})
    assert RecoveryClassifier.classify(candidate, evidence)["recovery_reason"] == "later_connection_blocker"


@pytest.mark.parametrize("timestamp", [1794003423, 1794003424])
def test_new_or_equal_fresh_trouble_prevents_recovery(recovery_case: tuple[dict, dict], timestamp: int) -> None:
    """Fresh trouble at or after reconnect defeats recovery."""
    candidate, evidence = recovery_case
    evidence["statistics"]["last_trouble"]["timestamp"] = timestamp
    assert RecoveryClassifier.classify(candidate, evidence)["recovery_reason"] == "newer_or_changed_trouble"


@pytest.mark.parametrize("last_seen", [1794003419, 1794003721, None])
def test_stale_future_or_missing_stats_remain_visible(recovery_case: tuple[dict, dict], last_seen: int | None) -> None:
    """Connection status alone cannot prove recovery."""
    candidate, evidence = recovery_case
    evidence["statistics"]["last_seen"] = last_seen
    assert RecoveryClassifier.classify(candidate, evidence)["recovery_status"] == "retained"


def test_three_distinct_interruptions_remain_visible_even_connected(recovery_case: tuple[dict, dict]) -> None:
    """Alternating state transitions count while duplicated events do not."""
    candidate, evidence = recovery_case
    evidence["events"] = [
        {"mac": candidate["mac"], "timestamp": 1794003000 + step, "type": event_type}
        for step, event_type in enumerate(
            ["AP_DISCONNECTED", "AP_CONNECTED", "AP_DISCONNECTED", "AP_CONNECTED", "AP_DISCONNECTED", "AP_CONNECTED"]
        )
    ] + [evidence["events"][-1]]
    evidence["events"] += deepcopy(evidence["events"])
    result = RecoveryClassifier.classify(candidate, evidence)
    assert result["interruptions_60m"] == 3
    assert result["recovery_status"] == "repeated"


def test_duplicate_disconnect_notifications_are_one_transition(recovery_case: tuple[dict, dict]) -> None:
    """Consecutive disconnections without reconnect do not create extra interruptions."""
    candidate, evidence = recovery_case
    evidence["events"] += [
        {"mac": candidate["mac"], "timestamp": 1794003090 + offset, "type": "AP_DISCONNECTED"} for offset in range(5)
    ]
    evidence["events"] += deepcopy(evidence["events"])
    result = RecoveryClassifier.classify(candidate, evidence)
    assert result["interruptions_60m"] == 1
    assert result["recovery_status"] == "recovered"


@pytest.mark.parametrize("code,key", [("99", ""), ("51", "FIRMWARE_CORRUPT"), ("07", "UNVERIFIED_KEY")])
def test_unknown_and_nonconnectivity_codes_remain_visible(
    recovery_case: tuple[dict, dict], code: str, key: str
) -> None:
    """A cloud connection cannot clear an unrelated or unverified definition."""
    candidate, evidence = recovery_case
    candidate.update(code=code, code_key=key)
    assert RecoveryClassifier.classify(candidate, evidence)["recovery_reason"] == "code_not_verified_connectivity"


@pytest.mark.parametrize("status", ["history_unavailable", "history_truncated", "history_http_403", "history_http_503"])
def test_incomplete_history_never_clears_a_warning(recovery_case: tuple[dict, dict], status: str) -> None:
    """Failure status survives classification rather than resembling successful recovery."""
    candidate, evidence = recovery_case
    evidence["evidence_status"] = status
    result = RecoveryClassifier.classify(candidate, evidence)
    assert result["recovery_status"] == "retained"
    assert result["evidence_status"] == status


@pytest.mark.parametrize("missing", ["events", "statistics", "catalogue", "trouble_timestamp"])
def test_missing_recovery_evidence_remains_visible(recovery_case: tuple[dict, dict], missing: str) -> None:
    """Each absent required signal is conservative."""
    candidate, evidence = recovery_case
    if missing == "trouble_timestamp":
        candidate[missing] = ""
    elif missing == "catalogue":
        evidence["catalogue_verified"] = False
    else:
        evidence[missing] = [] if missing == "events" else {}
    assert RecoveryClassifier.classify(candidate, evidence)["recovery_status"] == "retained"


@pytest.mark.parametrize(
    "event",
    [
        {"mac": "wrong", "timestamp": 1794003423, "type": "AP_CONNECTED"},
        {"mac": "000000000001", "type": "AP_CONNECTED"},
        {"mac": "000000000001", "timestamp": 1794009999, "type": "AP_CONNECTED"},
        {"mac": "000000000001", "timestamp": 1794003423},
    ],
)
def test_invalid_event_identity_or_time_never_proves_recovery(recovery_case: tuple[dict, dict], event: dict) -> None:
    """Malformed or out-of-scope history must be visible as invalid evidence."""
    candidate, evidence = recovery_case
    evidence["events"] = [event]
    assert RecoveryClassifier.classify(candidate, evidence)["evidence_status"] == "invalid_evidence"


@pytest.mark.parametrize("value", [3, "3", "03", "003", " 03 "])
def test_numeric_codes_match_with_leading_zero(value: object) -> None:
    """String and integer representations identify the same dictionary code."""
    assert TroubleCode.normalize(value) == "03"


@pytest.mark.parametrize("value", [True, False, -1, 3.5, {}, [], "bad", "０３"])
def test_invalid_code_fails_explicitly(value: object) -> None:
    """Malformed evidence must not silently disappear."""
    with pytest.raises(ValueError, match="trouble code"):
        TroubleCode.normalize(value)


def test_known_and_unknown_definitions() -> None:
    """The dictionary resolves known codes and preserves unknown evidence."""
    definitions = CodeDefinitions(
        [{"code": "03", "key": "DHCP_TIMEOUT", "name": "DHCP timeout", "description": "No DHCP response"}]
    )
    assert definitions.describe("03") == {
        "code": "03",
        "definition_status": "known",
        "code_key": "DHCP_TIMEOUT",
        "code_name": "DHCP timeout",
        "code_description": "No DHCP response",
    }
    assert definitions.describe("99") == {
        "code": "99",
        "definition_status": "unknown",
        "code_key": "",
        "code_name": "",
        "code_description": "No definition returned by Mist",
    }


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{"code": "03"}],
        [{"key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}],
        [{"code": "03", "key": None, "name": "Name", "description": "Description"}],
        [{"code": "03", "key": "A", "name": "A", "description": "A"}] * 2,
    ],
)
def test_invalid_or_duplicate_definitions_fail(rows: list[dict[str, object]]) -> None:
    """A broken dictionary must not appear as successful enrichment."""
    with pytest.raises(ValueError, match="definition"):
        CodeDefinitions(rows)


def test_observation_time_uses_utc_without_inventing_missing_time() -> None:
    """Epoch timestamps become UTC ISO 8601 and missing times remain empty."""
    assert TroubleCode.timestamp(0) == "1970-01-01T00:00:00+00:00"
    assert TroubleCode.timestamp(None) == ""


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2026-11-04T23:44:59+00:00", False),
        ("2026-11-04T23:45:00+00:00", True),
        ("2026-11-05T00:00:00+00:00", True),
        ("2026-11-05T00:00:01+00:00", False),
        ("", False),
    ],
)
def test_recent_trouble_window_is_inclusive_and_rejects_future_times(timestamp: str, expected: bool) -> None:
    """The report accepts the exact 15-minute boundary but rejects older and future times."""
    assert TroubleCode.is_recent(timestamp, "2026-11-05T00:00:00+00:00") is expected


@pytest.mark.parametrize("value", [True, -1, "yesterday", float("nan"), float("inf"), 10**30])
def test_invalid_observation_time_fails(value: object) -> None:
    """Invalid observation times cannot become an apparent current observation."""
    with pytest.raises(ValueError, match="timestamp"):
        TroubleCode.timestamp(value)
