# Implementation Plan: Automated Sweep Safety Procedure

**Branch**: `chore/1796-sweep-safety` (SpecKit feature directory `1796-comment-sweep-safety`) | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1796-comment-sweep-safety/spec.md`

**GitHub Issue**: [#1796](https://github.com/jmorrison-juniper/MistHelper/issues/1796)

## Summary

An automated sweep deleted a live declaration and stripped a comment marker. The mypy gate caught the first defect by luck, because issue #888 had widened that gate days earlier.

This work removes the luck. It adds a symbol table tool, a written procedure, and a test that covers the `--fast` flag.

The plan runs in three parts. The tool lands first, because the procedure names it. The procedure lands second. The test lands third, because it is independent of the other two.

## Technical Context

**Language/Version**: Python 3.13 (`pyproject.toml` target `py313`)

**Primary Dependencies**: The standard `ast` module and the standard `subprocess` module. This work adds no third-party dependency.

**Storage**: Not applicable. The tool reads a file and prints a report.

**Testing**: `pytest` with `--cov=src/ --cov-fail-under=80`. The suite must keep its pass count and must gain the new tests.

**Target Platform**: The CI runner uses Linux. A developer works on Windows. The tool must read a path on both, so it must use `pathlib` and must not hardcode a separator.

**Project Type**: A new tool plus a documentation change plus a test. The tool adds one class under `tools/`.

**Performance Goals**: The symbol table check must finish in under 5 seconds for a 6000-line file. `MistHelper.py` holds 6054 lines today.

**Constraints**:

- The root ruff line length is 120 characters.
- `mypy` reads `src/`, `MistHelper.py`, and `wsgi.py`. It does not read `tools/`. The new tool therefore faces `ruff`, `black`, `bandit`, and the test suite.
- The Five-Item Rule caps a function at 5 parameters, 5 blocks, and 25 lines. The tool must split its work across small methods.
- The project forbids a wrapper function. The tool must hold its logic in a class.
- `bandit` reports `B404` on an `import subprocess`. The tool needs `subprocess` to read a git revision, so that import needs a `# nosec` comment in the style of `MistHelper.py` line 47.

**Scale/Scope**: One new tool module, one instruction section, and two or three new tests.

### Measurement contract

The reference case is pull request #1791. Its commit statistics read as follows.

```text
1 file changed, 53 insertions(+), 515 deletions(-)
```

Run the command below to replay the sweep and prove the tool.

```powershell
.venv\Scripts\python.exe -m tools.symbol_diff --base 08a75d2~1 MistHelper.py
```

The tool must report the lost name `FAST_MODE_ENABLED` when a reviewer replays the state before the repair. Success criterion SC-006 states this outcome.

### Verified mechanics

A maintainer probed the current tree on 2026-08-06 at commit `08a75d2`. Four results shape the tasks.

1. `MistHelper.py` line 2382 holds the restored declaration `FAST_MODE_ENABLED: bool = False`.
2. `MistHelper.py` line 112 names `FAST_MODE_ENABLED` inside an export list.
3. `MistHelper.py` line 5101 holds the `global FAST_MODE_ENABLED` statement inside `_setup_runtime_flags`.
4. A search of `tests/` finds two references to the name. Both sit in `tests/unit/serial_cc/test_switch_vc_stats.py` and both set an attribute on a test double. No test reads the module global.

### Discovered risk: the declaration uses an annotated assignment

The declaration reads `FAST_MODE_ENABLED: bool = False`. Python parses that statement as `ast.AnnAssign`, not as `ast.Assign`.

A symbol table tool that matches `ast.Assign` alone misses every annotated module global. The tool would then report zero lost names on the exact defect that it exists to catch.

The control is task T007. The tool must handle `ast.Assign`, `ast.AnnAssign`, `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`, `ast.Import`, and `ast.ImportFrom`.

**Warning**: This repository already lost a generator to this exact trap. `scripts/generate_menu_wiki.py` searched for `menu_actions` as an `ast.Assign` node. The declaration gained a type annotation, the node became `ast.AnnAssign`, and the generator produced nothing for months.

### Discovered risk: the tool must read a file that does not compile

Defect 2 left `MistHelper.py` in a state that `py_compile` rejected. A tool that imports the file to read its names cannot run in that state.

The control is the `ast` module. It parses text and does not run it. The tool must catch `SyntaxError` and must print a clear message that names the file and the line. Requirement FR-018 and success criterion SC-007 state this outcome.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS with a constraint | The tool class must hold at most 5 public methods. Each method must stay inside 25 lines and 5 blocks. |
| II. Class-Based Architecture (No Wrappers) | PASS | The tool holds one class named `SymbolTableComparator`. The module entry point calls one method on it. No wrapper function exists. |
| III. Safety-First | PASS | The tool reads a file and prints a report. It writes no file and changes no state. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request workflow. The container needs no rebuild, because the tool does not ship in the runtime path. |
| V. Observability and Logging | PASS | The tool logs each read and each comparison. Every message stays ASCII. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | Every added line carries an inline comment. Requirement FR-023 states this rule. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS | Requirement FR-024 demands a log call before and after each read and each comparison. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS with one suppression | The `import subprocess` line needs a `# nosec B404` comment. The comment names the seam and states that the tool passes a fixed argument list with no shell. |

## Project Structure

### Documentation (this feature)

```text
specs/1796-comment-sweep-safety/
├── spec.md              # The feature specification
├── plan.md              # This file
└── tasks.md             # The task list
```

### Source code (repository root)

The work creates two files and changes two files.

```text
tools/
└── symbol_diff/
    ├── __init__.py                       # New: the module entry point
    └── comparator.py                     # New: the SymbolTableComparator class

.github/copilot-instructions.md           # Changed: add the sweep procedure section
agents.md                                 # Changed: add a one-line pointer to the procedure

tests/
└── unit/
    ├── test_fast_mode_flag.py            # New: the --fast flag tests
    └── tools/
        └── test_symbol_diff.py           # New: the tool tests
```

**Structure Decision**: The tool sits under `tools/`, next to `tools/ste_linter` and `tools/compliance_analyzer`. That location matches requirement FR-020 and matches the existing project layout. The tool takes a package directory, not a single file, because the Five-Item Rule caps one module at 5 top-level constructs.

## Phased approach

The work runs in three parts. Each part ends with a check.

### Part A - The symbol table tool

Build `SymbolTableComparator`. The class reads a file with the `ast` module, collects the module-level names, and compares two sets.

The class holds five public methods at most.

1. `collect_names(source: str) -> set[str]` reads the text and returns the module-level names.
2. `read_revision(revision: str, path: Path) -> str` reads the file text at a git revision.
3. `compare(before: set[str], after: set[str]) -> SymbolDelta` returns the lost names and the added names.
4. `report(delta: SymbolDelta) -> int` prints the report and returns the exit code.
5. `run(revision: str, paths: list[Path]) -> int` runs the whole check.

**Warning**: `collect_names` must handle `ast.AnnAssign` as well as `ast.Assign`. A tool that misses the annotated form reports zero lost names on the exact defect from issue #1796.

**Exit measurement**: The tool reports the lost `FAST_MODE_ENABLED` name when a reviewer replays the pull request #1791 sweep. It reads a file that does not compile without an unhandled error.

### Part B - The written procedure

Add a section to `.github/copilot-instructions.md`. The section states the four checks, each command, and each expected result.

The section must also state three rules.

1. A comment sweep deletes comment lines only. The expected count of other deletions is zero.
2. A sweep pull request body records that count.
3. A rebase repeats every check.

Add a one-line pointer in `agents.md`. That file already points to `.github/copilot-instructions.md` as the canonical source, so it must not repeat the procedure text.

**Exit measurement**: A search of the project instructions for the word "sweep" finds the procedure. The procedure names all four checks.

### Part C - The fast flag test

Add `tests/unit/test_fast_mode_flag.py`. The test proves three facts.

1. The `--fast` flag sets the `MistHelper.FAST_MODE_ENABLED` module global to `True`.
2. The absence of the flag leaves the module global at `False`.
3. The test reads the module global on the `MistHelper` module itself, not on a test double.

**Caution**: The test changes a module global. It must restore the earlier value after each run, or a later test reads a changed flag. Requirement FR-016 states this rule.

**Exit measurement**: The test passes on the current tree. The test fails when a reviewer removes the declaration from `MistHelper.py`.

## Risk register

| Risk | Likelihood | Effect | Control |
| - | - | - | - |
| The tool misses an annotated assignment | High | The tool reports zero lost names on the exact defect it exists to catch | Task T007 handles `ast.AnnAssign`. Task T012 proves the case against pull request #1791. |
| The tool cannot read a file that does not compile | Medium | The tool fails on defect 2 and hides defect 1 | Task T008 catches `SyntaxError` and prints a clear message |
| The fast flag test leaks a changed global | Medium | A later test reads the wrong value and fails without a clear cause | Task T016 restores the earlier value in a fixture teardown |
| A contributor skips the procedure | High | The next sweep repeats the defect | The procedure sits in the file that every agent session reads |
| The `MYPY_PATHS` value narrows again | Low | One of the four checks stops working | The procedure reads the value from `.github/workflows/ci.yml` instead of repeating it |
| The tool trips a bandit rule | Medium | The security gate fails | Task T009 adds a `# nosec B404` comment that names the seam |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The work adds a new tool | The mypy gate catches a lost name only where another module reads it. A private module global has no such reader. | A mypy-only check catches defect 1 by luck. The luck ran out once already, before issue #888 widened the gate. |
| The tool takes a package directory, not one module | The Five-Item Rule caps one module at 5 top-level constructs, and the tool needs a class plus an entry point plus a result type | A single module would exceed the cap and would fail the structural review |
| The procedure states a manual check, not a CI job | A sweep runs before the commit, and the check must stop the commit, not the merge | A CI job reports the defect after the push, and a reviewer then reads a red build instead of a clean difference |
