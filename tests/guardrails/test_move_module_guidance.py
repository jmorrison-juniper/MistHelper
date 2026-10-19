"""Check the module-move gate table against the live quality workflow."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml


class MoveModuleGuideGuard:
    """Read the module-move table and compare supported rows with live jobs."""

    nested_package_guidance = (
        "The guard counts direct Python modules except `__init__.py` and immediate child "
        "directories with tracked Python descendants. It uses the baseline ratchet and "
        "requires total excess to decrease or remain fixed."
    )

    expected = (
        (
            "Guardrails",
            "A path-keyed guard still names the old path.",
            "python -m pytest tests/guardrails",
        ),
        (
            "Import smoke",
            "The new path does not import, or the old path still imports.",
            'python -c "import <new module>" and a failing import of the old module',
        ),
        (
            "Resolver",
            "A wrong module string exists in `source_dependency_resolver.py`.",
            "A direct, unmocked resolution of each changed entry",
        ),
        (
            "Old paths",
            "A tracked text file names the old dotted or slash path.",
            'git grep -n "<old dotted path>|<old slash path>"',
        ),
        (
            "Menu reference",
            "A generated page is stale.",
            "python scripts/generate_menu_wiki.py and python -m scripts.menu_api_map",
        ),
        (
            "Symbols",
            "A module-level name is lost.",
            "symbol-diff --base origin/main <file> for each changed file",
        ),
    )

    @dataclass(frozen=True)
    class Result:
        """Keep checked and unchecked gate names available to the guard test."""

        checked: tuple[str, ...]
        unchecked: tuple[str, ...]

    def __init__(self, root: Path) -> None:
        self.root = root
        self.result = self.Result((), ())
        self.errors: list[str] = []

    def run(self) -> bool:
        """Read the guide and workflow, then report unsupported live coverage."""
        self.result = self.Result((), ())
        self.errors.clear()
        logging.info("Reading the module-move guide and live workflow")
        guide = self._read(".github/copilot-instructions.md")
        workflow = self._read(".github/workflows/ci.yml")
        if guide is None or workflow is None:
            return False
        if self.nested_package_guidance not in guide:
            self.errors.append("The nested source package ratchet guidance is missing")
        rows = self._table_rows(guide)
        if rows != self.expected:
            self.errors.append("The Move a module table does not match the required rows")
            return False
        return self._check_jobs(rows, workflow)

    def _check_jobs(self, rows: tuple[tuple[str, str, str], ...], workflow: str) -> bool:
        """Compare documented commands with active jobs, not comments or unrelated jobs."""
        try:
            document = yaml.safe_load(workflow)
        except yaml.YAMLError as error:
            self.errors.append(f"The workflow YAML is invalid: {error}")
            return False
        if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
            self.errors.append("The workflow must hold a jobs mapping")
            return False
        checked: list[str] = []
        unchecked: list[str] = []
        for gate, _, command in rows:
            job_name = {"Guardrails": "pytest_coverage_shards", "Menu reference": "menu_reference_drift"}.get(gate)
            job = document["jobs"].get(job_name)
            if job_name and job is not None and self._matches_job(gate, command, job):
                checked.append(gate)
            else:
                unchecked.append(gate)
                logging.warning("Move a module gate unchecked: %s", gate)
        self.result = self.Result(tuple(checked), tuple(unchecked))
        print(f"Move a module: checked {len(checked)} rows, unchecked {len(unchecked)} rows")
        for gate in unchecked:
            print(f"Move a module gate unchecked: {gate}")
        logging.debug("Checked %s module-move gates and left %s unchecked", len(checked), len(unchecked))
        return not self.errors

    def _matches_job(self, gate: str, command: str, job: object) -> bool:
        """Fail when a known job no longer runs the documented command."""
        if not isinstance(job, dict) or not isinstance(job.get("steps"), list):
            self.errors.append(f"The {gate} live job must hold steps")
            return False
        runs = [step["run"] for step in job["steps"] if isinstance(step, dict) and isinstance(step.get("run"), str)]
        if gate == "Guardrails":
            matches = self._guardrail_selection(command, job, runs)
        else:
            commands = command.split(" and ")
            matches = commands[0] in runs and f"{commands[1]} --check" in runs
        if not matches:
            self.errors.append(f"The {gate} documented command differs from the live job")
        return matches

    @staticmethod
    def _guardrail_selection(command: str, job: dict[str, object], runs: list[str]) -> bool:
        """Require the documented test directory in a matrix consumed by pytest."""
        strategy = job.get("strategy", {})
        if not isinstance(strategy, dict) or not isinstance(strategy.get("matrix"), dict):
            return False
        includes = strategy["matrix"].get("include", [])
        if not isinstance(includes, list):
            return False
        path = command.removeprefix("python -m pytest ")
        selected = any(
            isinstance(row, dict) and isinstance(row.get("test_paths"), str) and path in row["test_paths"].split()
            for row in includes
        )
        return selected and any(run.startswith("pytest ${{ matrix.test_paths }} ") for run in runs)

    def _read(self, relative_path: str) -> str | None:
        """Read one UTF-8 input and retain a named failure."""
        try:
            return (self.root / relative_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            self.errors.append(f"{relative_path}: {type(error).__name__}")
            return None

    @classmethod
    def _table_rows(cls, guide: str) -> tuple[tuple[str, str, str], ...]:
        """Parse the one table under the exact module-move heading."""
        match = re.search(r"^### Move a module\s*$([\s\S]*?)(?=^### |\Z)", guide, re.MULTILINE)
        if match is None:
            return ()
        rows: list[tuple[str, str, str]] = []
        for line in match.group(1).splitlines():
            cells = [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if len(cells) == 3 and cells[0] not in {"Gate", "-"}:
                cells[2] = cells[2].replace("`", "")
                rows.append(tuple(cells))
        return tuple(rows)


class TestMoveModuleGuide:
    """Prove table validation, live drift detection, and unchecked reporting."""

    def test_current_guide_matches_live_jobs(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Require the committed table to remain synchronized with available jobs."""
        root = Path(__file__).resolve().parents[2]
        guard = MoveModuleGuideGuard(root)
        assert guard.run(), guard.errors
        assert guard.result.checked == ("Guardrails", "Menu reference")
        assert guard.result.unchecked == ("Import smoke", "Resolver", "Old paths", "Symbols")
        output = capsys.readouterr().out
        assert "checked 2 rows, unchecked 4 rows" in output
        assert all(f"gate unchecked: {gate}" in output for gate in guard.result.unchecked)

    def test_table_drift_fails(self, tmp_path: Path) -> None:
        """Reject a changed command before it can hide a missing gate."""
        self._copy_inputs(tmp_path)
        guide = tmp_path / ".github/copilot-instructions.md"
        guide.write_text(
            guide.read_text(encoding="utf-8").replace("tests/guardrails`", "tests/unit`"),
            encoding="utf-8",
        )
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is False
        assert guard.errors == ["The Move a module table does not match the required rows"]

    def test_missing_live_job_is_reported_unchecked(self, tmp_path: Path) -> None:
        """Keep a missing live job visible without claiming that the row passed."""
        self._copy_inputs(tmp_path)
        workflow = tmp_path / ".github/workflows/ci.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace("menu_reference_drift:", "other_job:"),
            encoding="utf-8",
        )
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is True
        assert guard.result.checked == ("Guardrails",)
        assert "Menu reference" in guard.result.unchecked
        assert guard.errors == []

    @pytest.mark.parametrize(
        ("old", "new", "gate"),
        (
            ("tests/guardrails tests/integration", "tests/other tests/integration", "Guardrails"),
            ("run: pytest ${{ matrix.test_paths }}", "run: echo ${{ matrix.test_paths }}", "Guardrails"),
            ("run: python scripts/generate_menu_wiki.py", "run: echo skipped", "Menu reference"),
            ("run: python -m scripts.menu_api_map --check", "run: python -m scripts.menu_api_map", "Menu reference"),
        ),
    )
    def test_live_command_drift_fails(self, tmp_path: Path, old: str, new: str, gate: str) -> None:
        """Reject changed active commands even when a comment preserves the old text."""
        self._copy_inputs(tmp_path)
        workflow = tmp_path / ".github/workflows/ci.yml"
        original = workflow.read_text(encoding="utf-8")
        assert old in original
        workflow.write_text(original.replace(old, new) + f"\n# {old}\n", encoding="utf-8")
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is False
        assert gate in guard.result.unchecked
        assert guard.errors == [f"The {gate} documented command differs from the live job"]

    @pytest.mark.parametrize("content", ("jobs: [", "", "jobs: []"))
    def test_invalid_workflow_fails(self, tmp_path: Path, content: str) -> None:
        """Reject unreadable workflow contracts instead of reporting success."""
        self._copy_inputs(tmp_path)
        (tmp_path / ".github/workflows/ci.yml").write_text(content, encoding="utf-8")
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is False
        assert len(guard.errors) == 1
        assert "workflow" in guard.errors[0]

    @pytest.mark.parametrize("path", (".github/copilot-instructions.md", ".github/workflows/ci.yml"))
    @pytest.mark.parametrize("content", (None, b"\xff"))
    def test_unreadable_input_fails(self, tmp_path: Path, path: str, content: bytes | None) -> None:
        """Name missing and invalid UTF-8 inputs without claiming checked rows."""
        self._copy_inputs(tmp_path)
        destination = tmp_path / path
        if content is None:
            destination.unlink()
        else:
            destination.write_bytes(content)
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is False
        assert len(guard.errors) == 1
        assert path in guard.errors[0]
        assert guard.result.checked == ()

    def test_nested_package_guidance_drift_fails(self, tmp_path: Path) -> None:
        """Reject missing nested-package ratchet wording before it can drift."""
        self._copy_inputs(tmp_path)
        guide = tmp_path / ".github/copilot-instructions.md"
        guide.write_text(
            guide.read_text(encoding="utf-8").replace(
                MoveModuleGuideGuard.nested_package_guidance,
                "The nested package guidance changed.",
            ),
            encoding="utf-8",
        )
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is False
        assert "The nested source package ratchet guidance is missing" in guard.errors

    @staticmethod
    def _copy_inputs(root: Path) -> None:
        """Copy only the two guard inputs into a temporary repository."""
        source = Path(__file__).resolve().parents[2]
        for relative_path in (".github/copilot-instructions.md", ".github/workflows/ci.yml"):
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text((source / relative_path).read_text(encoding="utf-8"), encoding="utf-8")
