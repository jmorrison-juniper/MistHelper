"""Guard the planning record for dynamic JVD labs (issue 4504)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RECORD = REPOSITORY_ROOT / "specs/numbered/0/0/1/2/1/0/0/4/4504-dynamic-jvd-labs-planning"
REQUIRED_FILES = (
    "spec.md",
    "plan.md",
    "tasks.md",
    "analysis.md",
    "design/research.md",
    "design/data-model.md",
    "design/quickstart.md",
    "design/checklists/requirements.md",
    "design/contracts/template-contract.md",
    "design/contracts/engine-contract.md",
    "design/contracts/portal-contract.md",
    "design/contracts/persistence-contract.md",
    "design/contracts/delivery-contract.md",
)
TASK_LINE = re.compile(r"^- \[(?P<mark>[ xX])\] (?P<id>T\d{3})\b(?P<rest>.*)$")


def read_text(record: Path, name: str) -> str:
    """Read one record file and fail loudly when it is unreadable."""
    path = record / name
    assert path.is_file(), f"Missing planning file: {name}"
    return path.read_text(encoding="utf-8")


def checked_tasks_without_evidence(tasks_text: str) -> tuple[int, list[str]]:
    """Return the task count and the checked tasks that lack delivery evidence."""
    total = 0
    bad: list[str] = []
    for line in tasks_text.splitlines():
        match = TASK_LINE.match(line)
        if not match:
            continue
        total += 1
        if match["mark"] != " " and "(delivered:" not in match["rest"]:
            bad.append(match["id"])
    return total, bad


def missing_requirements(spec_text: str, tasks_text: str) -> list[str]:
    """Return each functional requirement that tasks.md does not trace."""
    requirements = sorted(set(re.findall(r"\bFR-\d{3}\b", spec_text)))
    return [item for item in requirements if item not in tasks_text]


def test_required_files_exist() -> None:
    """Require every planning file and report the count examined."""
    missing = [name for name in REQUIRED_FILES if not (RECORD / name).is_file()]
    print(f"examined {len(REQUIRED_FILES)} planning files")
    assert not missing, missing


def test_tasks_stay_unchecked() -> None:
    """Planning only: no task is checked without delivery evidence."""
    total, bad = checked_tasks_without_evidence(read_text(RECORD, "tasks.md"))
    print(f"examined {total} tasks")
    assert total >= 50
    assert not bad, bad


def test_every_requirement_is_traced() -> None:
    """Require each FR identifier in the spec to appear in tasks.md."""
    spec_text = read_text(RECORD, "spec.md")
    assert len(set(re.findall(r"\bFR-\d{3}\b", spec_text))) >= 22
    assert not missing_requirements(spec_text, read_text(RECORD, "tasks.md"))


def test_structural_directories_have_five_children_or_fewer() -> None:
    """Apply the five-child rule to every directory in the record."""
    directories = [RECORD, *(path for path in RECORD.rglob("*") if path.is_dir())]
    print(f"examined {len(directories)} directories")
    too_wide = [str(path) for path in directories if len(list(path.iterdir())) > 5]
    assert not too_wide, too_wide


def test_guard_detects_checked_task() -> None:
    """Prove the guard can fail on a checked task."""
    total, bad = checked_tasks_without_evidence("- [x] T001 Do work\n- [ ] T002 Plan")
    assert (total, bad) == (2, ["T001"])
    delivered = "- [x] T001 Do work (delivered: PR 1)"
    assert checked_tasks_without_evidence(delivered)[1] == []


def test_guard_detects_untraced_requirement() -> None:
    """Prove the guard can fail on a missing trace."""
    assert missing_requirements("FR-001 FR-002", "FR-001") == ["FR-002"]


def test_guard_fails_on_unreadable_input(tmp_path: Path) -> None:
    """Prove a missing file raises a failure and does not pass quietly."""
    with pytest.raises(AssertionError):
        read_text(tmp_path, "tasks.md")
