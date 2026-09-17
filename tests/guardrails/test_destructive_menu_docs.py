"""Guard the documented destructive menu set against the operation registry.

Why:
    `src/utils/operation_registry.py` decides which menu is destructive. Several
    documents repeat that set as a text range, such as
    `154-187, 189-191, 194, 206-208, 239`. A repeated value drifts.

    Issue #2825 records the drift. Menu 239 starts the upgrade capture portal
    and drives a firmware upgrade, and the registry marks it destructive. The
    agent instruction files stopped at 208, so an agent that trusted them could
    treat a firmware upgrade as safe to automate.

    This guard reads the registry, reads each document, and fails when the two
    disagree. The guard reports the count of documents it checked.
"""

from __future__ import annotations  # Keep annotation evaluation stable during test collection.

import logging  # Record each scan step for local diagnosis.
import re  # Find the documented range expression inside prose and tables.
from pathlib import Path  # Resolve repository paths on Windows and Linux.

import pytest  # Fail with a clear reason when the registry cannot load.

logger = logging.getLogger(__name__)  # Name each record for this module.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from tests/guardrails.

# Each document repeats the destructive set as text. A reader trusts the text,
# so the text must match the registry. Add a file here when it repeats the set.
DOCUMENTS_THAT_REPEAT_THE_SET: tuple[str, ...] = (
    ".github/copilot-instructions.md",  # The instruction file that every agent reads.
    "agents.md",  # The VS Code chat supplement.
    "documentation/diagrams/operations/operations-reference.md",  # The safety diagram page.
    "documentation/menu_reference.md",  # The generated operator reference.
    "documentation/wiki/Menu-Reference.md",  # The generated wiki copy.
)

# The set always starts at the first destructive menu, so anchor on that number
# and read the run of numbers, ranges, commas, and the word "and" that follows.
# The separator must accept `, 194` and `, and 239`, because the prose uses both.
_RANGE_PATTERN = re.compile(r"154-187(?:[,\s]+(?:and\s+)?\d+(?:-\d+)?)*")


class DestructiveMenuIndex:
    """Read the destructive menu set from the registry and from the documents."""

    @staticmethod
    def from_registry() -> set[int]:
        """Return every menu number that the registry marks destructive."""
        registry = pytest.importorskip(  # Skip when the package cannot import at all.
            "src.utils.operation_registry",
            reason="The operation registry is unavailable, so the menu guard cannot run.",
        )
        operation_registry = registry.OperationRegistry  # Read the single source of truth.
        options = operation_registry.registered_options()  # Every registered menu option.
        assert options, "The registry returned no option, so the guard read nothing."
        numbers = {  # Keep the menu number of each destructive option.
            int(option) for option in options if operation_registry.get(option)["category"] == "destructive"
        }
        logger.debug("Registry reports %s destructive menus", len(numbers))  # Log the measured size.
        return numbers

    @staticmethod
    def expand(expression: str) -> set[int]:
        """Return every number named by one documented range expression."""
        numbers: set[int] = set()  # Collect each number the expression names.
        for part in expression.replace(" and ", ",").split(","):  # Read one term at a time.
            term = part.strip()  # Drop the spacing that the prose adds.
            if not term:  # A trailing separator leaves an empty term.
                continue  # Skip it, because it names no menu.
            if "-" in term:  # A term such as `154-187` names an inclusive range.
                first, last = (int(value) for value in term.split("-", 1))  # Read both ends.
                numbers.update(range(first, last + 1))  # Add every number in the range.
            else:  # A term such as `239` names one menu.
                numbers.add(int(term))  # Add the single menu number.
        return numbers  # Return the complete set for comparison.

    @staticmethod
    def occurrences(relative_path: str) -> list[str]:
        """Return each documented range expression found in one file."""
        path = _REPO_ROOT / relative_path  # Build the absolute path for this platform.
        assert path.is_file(), f"The guard cannot read {relative_path}. The document is missing."
        text = path.read_text(encoding="utf-8")  # Read the document with a fixed encoding.
        found = _RANGE_PATTERN.findall(text)  # Collect every range expression in the file.
        logger.debug("Found %s range expressions in %s", len(found), relative_path)  # Log the count.
        return found


def test_documents_match_the_registry() -> None:
    """Fail when a document names a destructive set that the registry denies."""
    expected = DestructiveMenuIndex.from_registry()  # The registry decides.
    mismatches: list[str] = []  # Collect one message for each wrong expression.
    checked = 0  # Count the expressions the guard compared.
    for relative_path in DOCUMENTS_THAT_REPEAT_THE_SET:  # Read each document that repeats the set.
        for expression in DestructiveMenuIndex.occurrences(relative_path):  # Read each expression.
            checked += 1  # Record that the guard compared one more expression.
            documented = DestructiveMenuIndex.expand(expression)  # Expand the text into numbers.
            if documented != expected:  # The text must name the registry set exactly.
                missing = sorted(expected - documented)  # A menu the document forgot.
                extra = sorted(documented - expected)  # A menu the document invented.
                mismatches.append(f"  {relative_path}: missing={missing} extra={extra}")
    assert checked, "The guard found no documented range expression, so it compared nothing."
    report = "\n".join(mismatches)  # One line for each wrong expression.
    assert not mismatches, (  # A wrong safety list must stop the build.
        f"Compared {checked} documented range expressions against " f"{len(expected)} destructive menus.\n{report}"
    )
    logger.info("Compared %s range expressions against the registry", checked)  # State the count.


def test_instruction_table_counts_match_the_registry() -> None:
    """Fail when the category table in the instruction file holds a stale count."""
    registry = pytest.importorskip(  # Skip when the package cannot import at all.
        "src.utils.operation_registry",
        reason="The operation registry is unavailable, so the count guard cannot run.",
    )
    operation_registry = registry.OperationRegistry  # Read the single source of truth.
    options = operation_registry.registered_options()  # Every registered menu option.
    actual: dict[str, int] = {}  # Hold the measured size of each category.
    for option in options:  # Count one option at a time.
        category = operation_registry.get(option)["category"]  # Read the category of this option.
        actual[category] = actual.get(category, 0) + 1  # Add this option to its category.
    path = _REPO_ROOT / ".github/copilot-instructions.md"  # The table lives in the instruction file.
    assert path.is_file(), "The guard cannot read .github/copilot-instructions.md."
    rows = re.findall(r"^\| `(\w+)` \| (\d+) \|", path.read_text(encoding="utf-8"), re.MULTILINE)
    assert rows, "The guard found no category row, so it compared nothing."
    wrong = [  # Keep one message for each row that disagrees with the registry.
        f"  {name}: table says {int(count)}, registry says {actual.get(name)}"
        for name, count in rows
        if actual.get(name) != int(count)
    ]
    assert not wrong, f"Compared {len(rows)} category rows.\n" + "\n".join(wrong)
    logger.info("Compared %s category rows against the registry", len(rows))  # State the count.
