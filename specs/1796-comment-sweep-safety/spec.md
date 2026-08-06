# Feature Specification: Automated Sweep Safety Procedure

**Feature Branch**: `docs/1792-1796-lint-debt-specs` (specification only). The implementation branch is `chore/1796-sweep-safety`.

**GitHub Issue**: [#1796](https://github.com/jmorrison-juniper/MistHelper/issues/1796) — "chore: an automated comment sweep deleted a live declaration and broke the build"

**Created**: 2026-08-06

**Status**: Specification only. No code change exists yet.

**Input**: Write a safety procedure for any automated comment sweep or code sweep. Add a test that covers the `--fast` command line flag.

---

## Background

An automated sweep deleted a live declaration from `MistHelper.py`. The same sweep removed a comment marker from a separator line. The file then failed to compile.

Issue [#1707](https://github.com/jmorrison-juniper/MistHelper/issues/1707) asked for the removal of the completed-migration `NOTE` comment blocks. Pull request #1791 carried the sweep. The commit statistics read as follows.

```text
1 file changed, 53 insertions(+), 515 deletions(-)
```

Two of the 515 deleted lines were not comments.

### Defect 1: the sweep deleted a live module global

`MistHelper.py` held the following declaration.

```python
FAST_MODE_ENABLED: bool = False  # Set to True via --fast CLI flag at startup
```

The declaration sat between two `NOTE` comment blocks. The sweep treated the whole span as comment text and removed the declaration with it.

The function `_setup_runtime_flags` assigns to that name through a `global` statement at `MistHelper.py` line 5101. Without the declaration, the module holds no such global. The `--fast` flag then raises `NameError` at run time.

### Defect 2: the sweep stripped a comment marker

The sweep removed the leading `#` from a separator line. The remaining text was not valid Python. The `py_compile` step failed on the file.

### Why no check caught the first defect

Two gaps combined.

1. **No test covers the `--fast` path.** A search of `tests/` finds two references to the name `FAST_MODE_ENABLED`. Both sit in `tests/unit/serial_cc/test_switch_vc_stats.py`, and both set an attribute on a test double. Neither reads the module global in `MistHelper.py`. No test observed the missing declaration.
2. **The mypy gate reached `MistHelper.py` only days before.** Issue [#888](https://github.com/jmorrison-juniper/MistHelper/issues/888) widened the mypy scope. The `MYPY_PATHS` value in `.github/workflows/ci.yml` line 59 now reads `src/ MistHelper.py wsgi.py`. The wider gate reported the undefined global. Before that change, the defect would have reached the container.

The compile failure is loud. The missing global is quiet. It fails only when an operator passes `--fast`.

### Why this matters beyond one commit

An automated sweep is a code change. It carries the same risk as a hand edit, and it carries more risk, because it changes many lines at once and because a reviewer reads it as a comment-only difference.

A reviewer who sees "delete comments" in a pull request title does not look for a deleted declaration. The title sets the wrong expectation. A 515-line deletion holds two defects inside a difference that looks safe.

### The sweeps that this repository still plans

Four open efforts propose a mechanical change across many files.

| Issue | Scope | Risk |
| - | - | - |
| [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) | Remove 286 unused `# noqa` directives across 94 files | A repair with the wrong ruff flag deletes 34 live suppressions |
| [#1793](https://github.com/jmorrison-juniper/MistHelper/issues/1793) | Rewrite 4478 logging calls across 223 files | A scripted rewrite can change a message text |
| [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795) | Repair 146 sites across about 70 files | An unsafe ruff repair can change behavior |
| [#886](https://github.com/jmorrison-juniper/MistHelper/issues/886) | Convert `print()` calls into logging calls | A rewrite can drop an output line |

Each of these efforts needs the procedure that this specification defines. The procedure must land before the first of them starts.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop a sweep that deletes a live declaration (Priority: P1)

A contributor runs an automated sweep. The sweep removes a line that is not a comment. The contributor runs the stated checks before the commit and finds the deleted line.

**Why this priority**: This story prevents the exact defect that issue #1796 records. It also protects the four planned sweeps that the table above lists.

**Independent Test**: A reviewer runs a sweep that deletes one declaration on purpose. The stated checks report the deletion before the commit.

**Acceptance Scenarios**:

1. **Given** a sweep that deletes a line which is not a comment, **When** a contributor runs the symbol table check, **Then** the check reports the lost name and states the file.
2. **Given** a sweep that produces a file which does not compile, **When** a contributor runs the compile check, **Then** the check fails and names the file and the line.
3. **Given** a completed sweep, **When** a contributor reads the procedure, **Then** the procedure states the exact count of deleted lines that are not comments.
4. **Given** a sweep pull request, **When** a reviewer reads the body, **Then** the body states that count and the expected value is zero.

---

### User Story 2 - Prove that the fast flag still works (Priority: P1)

A contributor removes the `FAST_MODE_ENABLED` declaration. The unit test suite fails and names the missing global.

**Why this priority**: This story shares the P1 rank. The procedure catches a sweep defect at commit time. The test catches the same defect at every later change, including a hand edit.

**Independent Test**: A reviewer removes the declaration from `MistHelper.py`. The reviewer runs the unit suite and reads a failure that names the flag.

**Acceptance Scenarios**:

1. **Given** the new test, **When** a contributor runs the unit suite on the current tree, **Then** the test passes.
2. **Given** the new test, **When** a contributor removes the `FAST_MODE_ENABLED` declaration, **Then** the test fails and the message names the flag.
3. **Given** the new test, **When** a contributor passes the `--fast` flag, **Then** the test proves that the module global receives the value `True`.
4. **Given** the new test, **When** a contributor omits the `--fast` flag, **Then** the test proves that the module global holds the value `False`.

---

### User Story 3 - Find the procedure without asking a maintainer (Priority: P2)

A contributor plans an automated sweep. The contributor opens the project instructions and finds the procedure. The contributor does not need to ask a maintainer.

**Why this priority**: This story protects the value of the first two stories over time. A written rule that nobody can find has no effect.

**Independent Test**: A contributor who never met this issue searches the project instructions for the word "sweep" and finds the procedure.

**Acceptance Scenarios**:

1. **Given** the project instructions, **When** a contributor searches for the sweep procedure, **Then** the search finds it in `.github/copilot-instructions.md`.
2. **Given** the project instructions, **When** a contributor reads the procedure, **Then** the procedure states each command and each expected result.
3. **Given** the procedure, **When** a contributor reads it, **Then** the procedure names the pull request body statement that a sweep must hold.

---

### Edge Cases

- A sweep runs on a file that the mypy gate does not read. The type check then reports nothing. The symbol table check still reports the lost name, so the procedure must not depend on mypy alone.
- A sweep deletes a name that no other module reads. Mypy reports nothing, because no reader exists. The symbol table check still reports the loss.
- A sweep adds a name instead of deleting one. The symbol table check must report an added name as well as a lost name, because an added name can shadow an import.
- A sweep changes only whitespace inside a comment. The symbol table stays the same and the compile check passes. The procedure records zero deleted lines that are not comments, and the sweep proceeds.
- A sweep touches a file that holds no Python code, such as a Markdown file or a YAML file. The compile check does not apply. The procedure must state which check applies to which file type.
- A sweep runs across many files. The compile check must cover every changed file, not the largest one alone.
- A contributor runs the sweep and the checks, then rebases onto a changed `main`. The rebase can reintroduce the defect. The procedure must run again after any rebase.

---

## Requirements *(mandatory)*

### Procedure requirements

- **FR-001**: The project instructions MUST hold a written procedure for an automated sweep. The location MUST be `.github/copilot-instructions.md`.
- **FR-002**: The procedure MUST state a compile check. The command MUST be `.venv\Scripts\python.exe -m py_compile <file>` for every changed Python file.
- **FR-003**: The procedure MUST state a lint check. The command MUST be `.venv\Scripts\python.exe -m ruff check .` across the whole repository, not across the changed files alone.
- **FR-004**: The procedure MUST state a type check. The command MUST use the `MYPY_PATHS` value from `.github/workflows/ci.yml`, which reads `src/ MistHelper.py wsgi.py`.
- **FR-005**: The procedure MUST state a symbol table check. The check MUST compare the module-level names before the sweep against the module-level names after the sweep.
- **FR-006**: The symbol table check MUST report a lost name and MUST report an added name.
- **FR-007**: The procedure MUST state a difference read. The contributor MUST count every changed line that is not a comment.
- **FR-008**: The procedure MUST state that a comment sweep deletes comment lines only. The expected count of other deletions is zero.
- **FR-009**: The procedure MUST state that a sweep pull request body records that count.
- **FR-010**: The procedure MUST state that a rebase repeats every check, because a rebase can reintroduce the defect.
- **FR-011**: The procedure MUST state that a sweep pull request title names the sweep. A title such as "delete comments" sets the wrong expectation for a reviewer.

### Test requirements

- **FR-012**: A test MUST prove that the `--fast` flag sets the `FAST_MODE_ENABLED` module global in `MistHelper.py` to `True`.
- **FR-013**: A test MUST prove that the absence of the flag leaves the module global at `False`.
- **FR-014**: A test MUST fail when a contributor removes the `FAST_MODE_ENABLED` declaration from `MistHelper.py`.
- **FR-015**: The test MUST read the module global on the `MistHelper` module itself. It MUST NOT read an attribute on a test double, because the two existing references in `tests/unit/serial_cc/test_switch_vc_stats.py` do that and neither one caught the defect.
- **FR-016**: The test MUST restore the earlier value of the module global after each run, so that no later test reads a changed flag.

### Tooling requirements

- **FR-017**: The symbol table check MUST run without a manual step. A contributor MUST be able to run one command.
- **FR-018**: The symbol table tool MUST read the file with the `ast` module. It MUST NOT run the file, because a sweep can leave a file that does not compile.
- **FR-019**: The symbol table tool MUST accept a git revision for the earlier state, so that a contributor can compare against `main`.
- **FR-020**: The symbol table tool MUST live under `tools/`, next to the other project tools.

### Quality requirements

- **FR-021**: Every quality gate MUST stay green. The unit test suite MUST keep its pass count and MUST gain the new tests.
- **FR-022**: All prose, all code comments, and all commit text MUST follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md`.
- **FR-023**: Every added Python line MUST carry an inline comment that explains why the line exists.
- **FR-024**: Every meaningful action that the new tool takes MUST log before the action and after the action.

### Key Entities

- **Automated sweep**: A scripted change that edits many lines across one or more files without a per-line judgment.
- **Symbol table**: The set of module-level names that a Python file defines. It holds each class, each function, each assignment target, and each import alias.
- **Comment-only change**: A change in which every deleted line and every added line is a comment or a blank line.
- **Silent defect**: A defect that no gate reports and that fails only on a path that no test covers.

---

## The four checks

The table states each check, its command, and its expected result.

| Check | Command | Expected result | Catches |
| - | - | - | - |
| Compile | `python -m py_compile <each changed .py file>` | Exit code 0 with no output | Defect 2, the stripped comment marker |
| Lint | `python -m ruff check .` | Exit code 0 | A broken import and an undefined name |
| Type | `python -m mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml` | Exit code 0 | Defect 1, when another module reads the lost name |
| Symbol table | `python -m tools.symbol_diff --base main <each changed .py file>` | Zero lost names and zero added names | Defect 1, in every case |

**Warning**: The type check catches the lost name only where another module reads it. The symbol table check catches the loss in every case. A contributor must run both.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The project instructions hold a procedure that states all four checks and states the expected result for each one.
- **SC-002**: A contributor who removes the `FAST_MODE_ENABLED` declaration sees the unit test suite fail with a message that names the flag.
- **SC-003**: A test proves that the `--fast` flag sets the module global to `True`.
- **SC-004**: A test proves that the absence of the flag leaves the module global at `False`.
- **SC-005**: One command reports the lost names and the added names between the current tree and a named git revision.
- **SC-006**: The symbol table tool reports the lost `FAST_MODE_ENABLED` name when a reviewer replays the sweep from pull request #1791.
- **SC-007**: The symbol table tool reads a file that does not compile without raising an unhandled error.
- **SC-008**: The procedure states that a sweep pull request body records the count of deleted lines that are not comments.
- **SC-009**: Every quality gate stays green. The unit test suite gains the new tests and keeps every earlier pass.
- **SC-010**: A contributor who never met this issue finds the procedure by a search of the project instructions for the word "sweep".

---

## Non-Goals

- **NG-001**: This work does not add any lint suppression. It adds no `# noqa` directive, no `# type: ignore` comment, and no `# nosec` comment. The whole point is a repair, not a hidden result.
- **NG-002**: This work does not revert pull request #1791. That pull request already repaired both defects.
- **NG-003**: This work does not add a test for every command line flag. The `--fast` flag is the one that the defect touched.
- **NG-004**: This work does not add a CI job for the symbol table check. The check runs before a commit, and a contributor runs it by hand. A CI job is a separate question.
- **NG-005**: This work does not change the `MYPY_PATHS` value. Issue #888 already set it, and this work reads it.
- **NG-006**: This work does not forbid an automated sweep. It states the checks that a sweep must pass.
- **NG-007**: This work does not repair a defect that an earlier sweep left. No such defect is known today.
- **NG-008**: This work does not add a rule to the ruff `select` list. The other four specifications in this set own those decisions.

---

## Assumptions

- The `MYPY_PATHS` value stays at `src/ MistHelper.py wsgi.py`. A narrower value would remove one of the four checks.
- A contributor runs the checks before the commit. The procedure states a manual step, not an automatic one.
- The `ast` module parses every file that the repository holds. A file that does not parse produces a clear message from the tool, not a crash.
- The two existing references to `FAST_MODE_ENABLED` in `tests/unit/serial_cc/test_switch_vc_stats.py` stay as they are. They test a different object and this work does not change them.
- The four planned sweeps in the table above start after this work lands. A sweep that starts earlier carries the same risk that issue #1796 records.
- A reviewer reads the pull request body. A count that the body states reaches the reviewer.

---

## Dependencies

- Issue [#1707](https://github.com/jmorrison-juniper/MistHelper/issues/1707) requested the sweep that produced both defects.
- Pull request #1791 carries the sweep and the repair. It is the reference case for success criterion SC-006.
- Issue [#888](https://github.com/jmorrison-juniper/MistHelper/issues/888) widened the mypy scope to cover `MistHelper.py`. That change reported the first defect.
- Issues [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792), [#1793](https://github.com/jmorrison-juniper/MistHelper/issues/1793), [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795), and [#886](https://github.com/jmorrison-juniper/MistHelper/issues/886) each plan a sweep. Each one needs this procedure.
- The Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` govern all prose in this work.
