"""Check the module-move gate table against the live quality workflow."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path


class MoveModuleGuideGuard:
    """Read the module-move table and compare supported rows with live jobs."""

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
        logging.info("Reading the module-move guide and live workflow")
        guide = self._read(".github/copilot-instructions.md")
        workflow = self._read(".github/workflows/ci.yml")
        if guide is None or workflow is None:
            return False
        rows = self._table_rows(guide)
        if rows != self.expected:
            self.errors.append("The Move a module table does not match the required rows")
            return False
        checked: list[str] = []
        unchecked: list[str] = []
        for gate, _, _command in rows:
            patterns = self._live_patterns(gate)
            if patterns and all(re.search(pattern, workflow) for pattern in patterns):
                checked.append(gate)
            else:
                unchecked.append(gate)
                logging.warning("Move a module gate unchecked: %s", gate)
            if gate == "Import smoke" and "tests/unit/scripts/test_script_imports.py" not in workflow:
                self.errors.append("The Import smoke live job is missing")
        self.result = self.Result(tuple(checked), tuple(unchecked))
        logging.debug("Checked %s module-move gates and left %s unchecked", len(checked), len(unchecked))
        return not self.errors

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

    @staticmethod
    def _live_patterns(gate: str) -> tuple[str, ...]:
        """Return workflow evidence for a gate, or no evidence when no job exists."""
        return {
            "Guardrails": (r"\btests/guardrails\b",),
            "Import smoke": (r"python -m pytest tests/unit/scripts/test_script_imports\.py -q",),
            "Menu reference": (
                r"python scripts/generate_menu_wiki\.py",
                r"python -m scripts\.menu_api_map --check",
            ),
        }.get(gate, ())


class TestMoveModuleGuide:
    """Prove table validation, live drift detection, and unchecked reporting."""

    def test_current_guide_matches_live_jobs(self) -> None:
        """Require the committed table to remain synchronized with available jobs."""
        root = Path(__file__).resolve().parents[2]
        guard = MoveModuleGuideGuard(root)
        assert guard.run(), guard.errors
        assert guard.result.checked == ("Guardrails", "Import smoke", "Menu reference")
        assert guard.result.unchecked == ("Resolver", "Old paths", "Symbols")

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
            workflow.read_text(encoding="utf-8").replace("tests/unit/scripts/test_script_imports.py", "other.py"),
            encoding="utf-8",
        )
        guard = MoveModuleGuideGuard(tmp_path)
        assert guard.run() is False
        assert "Import smoke" in guard.result.unchecked
        assert guard.errors == ["The Import smoke live job is missing"]

    @staticmethod
    def _copy_inputs(root: Path) -> None:
        """Copy only the two guard inputs into a temporary repository."""
        source = Path(__file__).resolve().parents[2]
        for relative_path in (".github/copilot-instructions.md", ".github/workflows/ci.yml"):
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text((source / relative_path).read_text(encoding="utf-8"), encoding="utf-8")
