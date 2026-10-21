"""Test explicit candidate policy and baseline regression decisions."""

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from src.foundation.support.code_defaults.__main__ import main
from src.foundation.support.code_defaults.inventory import Candidate, Inventory
from src.foundation.support.code_defaults.policy import GuardPolicy

_SCOPE = [
    "src/mist/resources/device/ap_profile_migration_manager.py",
    "src/mist/intelligence/analytics/zone_analyzer.py",
    "src/mist/resources/inventory/csv_comparator.py",
    "src/foundation/support/utils/address_utils.py",
    "src/mist/resources/org/org_config_migration_manager.py",
]


def _inventory(candidates: tuple[Candidate, ...]) -> Inventory:
    """Build a deterministic inventory for policy tests."""
    return Inventory(
        revision="revision",
        discovered_files=5,
        parsed_files=5,
        parse_failures=(),
        candidates=candidates,
        selected_paths=tuple(_SCOPE),
    )


def _candidate(
    identity: str,
    input_key: str = "data",
    path: str = "src/mist/resources/device/ap_profile_migration_manager.py",
    shape: str = "attribute",
) -> Candidate:
    """Build one candidate within the accepted test scope."""
    return Candidate(
        identity=identity,
        path=path,
        line=10,
        column=4,
        symbol="Compare.run",
        shape=shape,
        input_key=input_key,
        default_kind="empty_list",
    )


def _baseline(identities: list[str]) -> dict[str, object]:
    """Build a baseline that accepts the supplied high-severity identities."""
    return {
        "schema_version": 1,
        "criterion_version": "1",
        "reviewed_revision": "revision",
        "scope": _SCOPE,
        "accepted_high": identities,
        "accepted_total": len(identities),
        "dispositions": [
            {
                "identity": identity,
                "classification": "high",
                "evidence": "controlled test baseline",
                "ownership": "issue-2753",
            }
            for identity in identities
        ],
    }


def test_new_candidate_fails_even_when_an_old_candidate_disappears() -> None:
    """Reject a new high identity when the total count stays unchanged."""
    policy = GuardPolicy()
    baseline = _baseline(["old"])

    result = policy.evaluate(_inventory((_candidate("new"),)), baseline)

    assert result.status == "regression"
    assert result.new_high == ("new",)
    assert result.removed_high == ("old",)
    assert result.parsed_files == 5


def test_display_only_candidate_does_not_raise_high_total() -> None:
    """Keep a reviewed display-only default outside the high-severity total."""
    policy = GuardPolicy()
    candidate = _candidate(
        "display",
        "display_name",
        "src/mist/resources/inventory/csv_comparator.py",
        "mapping_get",
    )
    baseline = _baseline([])
    baseline["dispositions"] = [
        {
            "identity": candidate.identity,
            "classification": "display_only",
            "evidence": "controlled test display-only disposition",
            "ownership": "issue-2753",
        }
    ]

    result = policy.evaluate(_inventory((candidate,)), baseline)

    assert result.status == "passed"
    assert result.accepted_total == 0


def test_new_non_high_candidate_requires_a_reviewed_disposition() -> None:
    """Require review evidence for a candidate even if policy marks it non-high."""
    candidate = _candidate(
        "new-display",
        "display_name",
        "src/mist/resources/inventory/csv_comparator.py",
        "mapping_get",
    )

    result = GuardPolicy().evaluate(_inventory((candidate,)), _baseline([]))

    assert result.status == "invalid_input"
    assert "lacks a reviewed disposition" in result.message


def test_cli_guard_rejects_an_unsafe_default_in_a_tracked_repository(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scan all five tracked files and report a new unsafe identity."""
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    for path in _SCOPE:
        source = root / path
        source.parent.mkdir(parents=True, exist_ok=True)
        content = "def choose(response):\n    return getattr(response, 'data', [])\n" if path == _SCOPE[0] else ""
        source.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", *_SCOPE], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "create guard fixture"], check=True, capture_output=True)
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(_baseline(["old"])), encoding="utf-8")

    status = main(["guard", "--root", str(root), "--baseline", str(baseline_path)])
    output = json.loads(capsys.readouterr().out)

    assert status == 1
    assert output["status"] == "regression"
    assert output["parsed_files"] == 5
    assert output["candidate_count"] == 1
    assert output["new_high"] == ["src/mist/resources/device/ap_profile_migration_manager.py|choose|attribute|data|0"]


def test_unknown_scoped_candidate_is_invalid() -> None:
    """Refuse an in-scope candidate without a reviewed classification."""
    result = GuardPolicy().evaluate(
        _inventory((_candidate("unknown", "unreviewed_key"),)),
        _baseline([]),
    )

    assert result.status == "invalid_input"
    assert "unclassified" in result.message


def test_duplicate_identity_and_bad_baseline_total_are_invalid() -> None:
    """Reject duplicate identities and totals that disagree with the baseline."""
    policy = GuardPolicy()
    duplicate = _inventory((_candidate("same"), _candidate("same")))
    invalid_total = _baseline(["known"])
    invalid_total["accepted_total"] = 0

    duplicate_result = policy.evaluate(duplicate, _baseline(["same"]))
    total_result = policy.evaluate(_inventory(()), invalid_total)

    assert duplicate_result.status == "invalid_input"
    assert "duplicate" in duplicate_result.message
    assert total_result.status == "invalid_input"
    assert "total" in total_result.message


def test_incomplete_scans_and_unreadable_baselines_never_pass(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reject parse errors, incomplete selection, zero selection, and missing baseline files."""
    policy = GuardPolicy()
    complete = _inventory(())
    invalid_scans = (
        replace(complete, parse_failures=("source.py: SyntaxError",)),
        replace(complete, selected_paths=tuple(_SCOPE[:-1])),
        replace(complete, selected_paths=()),
    )

    assert all(policy.evaluate(scan, _baseline([])).status == "invalid_input" for scan in invalid_scans)
    root = Path(__file__).resolve().parents[4]
    status = main(["guard", "--root", str(root), "--baseline", str(tmp_path / "missing.json")])
    output = json.loads(capsys.readouterr().out)

    assert status == 2
    assert output["parsed_files"] == 5
