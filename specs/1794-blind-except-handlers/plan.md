# Implementation Plan: Blind Except Handler Audit

**Branch**: `refactor/1794-blind-except` (SpecKit feature directory `1794-blind-except-handlers`) | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1794-blind-except-handlers/spec.md`

**GitHub Issue**: [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794)

## Summary

Ruff reports 500 blind handlers once a maintainer removes the inert `# noqa` directives. Ruff repairs none of them, and no mechanical repair exists. Each site needs a judgment.

This plan runs the work in three stages. It reconciles the baseline first. It then audits the sites in 15 slices, from the smallest area to the largest area. It closes both gates last.

The plan treats the existing project judgment as a starting point, not as a conclusion. The comment at `pyproject.toml` line 475 states that 493 sites are intentional in cleanup handlers and error handlers. The audit tests that statement one site at a time.

## Technical Context

**Language/Version**: Python 3.13 (`pyproject.toml` target `py313`)

**Primary Dependencies**: `ruff` 0.16.0 and `pylint` 4.0.6. This work adds no dependency.

**Storage**: Not applicable. The work changes handler blocks, comments, and two configuration entries.

**Testing**: `pytest` with `--cov=src/ --cov-fail-under=80`. The suite must keep its pass count for each slice.

**Target Platform**: The CI runner uses Linux. A developer works on Windows. Both report the same ruff count.

**Project Type**: Behavior-sensitive refactor. A narrowed exception type changes which errors propagate.

**Performance Goals**: The lint gate must stay inside its current runtime. A narrow exception clause costs the same as a broad one at run time.

**Constraints**:

- The root ruff line length is 120 characters.
- `ruff check .` reads the whole repository. Its `extend-exclude` list drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`.
- `pylint` reads `MistHelper.py` and `src` only. The two roots differ, and that difference produces part of the count gap.
- `radon` fails on any block above complexity 10. A narrowed type adds no branch, so the score stays flat. An added `if` inside a handler does add a branch.
- The action logging rule in `.github/copilot-instructions.md` demands a log call on each meaningful action. Requirement FR-011 extends that rule to every handler that the code continues past.

**Scale/Scope**: 500 sites, 161 files, 15 slices, and two configuration entries.

### Measurement contract

Run the three commands below before the first slice. Record all three values.

```powershell
.venv\Scripts\python.exe -m ruff check . --select BLE001 --statistics
.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --statistics
.venv\Scripts\python.exe -m pylint MistHelper.py src --disable=all --enable=W0718 --score=n
```

The expected values are 412, 500, and a value near 493.

**Warning**: The scope uses the 500 count, not the 412 count. A scope built on 412 leaves 88 sites unaudited, and the gate never reports them.

### Verified mechanics

A maintainer probed the counts on 2026-08-06 at commit `08a75d2`. Four results shape the tasks.

1. The default count reads 412 and the `--ignore-noqa` count reads 500. The gap is 88.
2. The default run touches 122 files. The `--ignore-noqa` run touches 161 files. 39 files hold hidden sites only.
3. `src/ssh` shows the largest hidden share. It reports 14 sites by default and 32 with `--ignore-noqa`.
4. `starlink_dashboard.py` holds 8 sites. Pylint never reads that file, so those 8 sites sit inside the count gap between the two tools.

### Discovered risk: the two tools disagree by 7 sites

Ruff reports 500 with `--ignore-noqa`. The `pyproject.toml` comment records 493 for pylint. The gap is 7.

The largest known cause is the root difference. Ruff reads `starlink_dashboard.py`, `tools/`, and `tests/`. Pylint reads `MistHelper.py` and `src` only. That difference alone covers more than 7 sites, so a second effect must run the other way. The likely second effect is the pylint scope in the current CI workflow, which the team changed in pull request #1788.

The control is task T005. It measures the pylint count again on the current tree instead of trusting the recorded 493.

### Discovered risk: a narrowed type can turn a caught error into a crash

The audit narrows the exception type at some sites. A narrow clause lets an unexpected error propagate, which is the whole point. It also changes the behavior on any path that already raises that unexpected error today.

The control is the full unit suite on each slice plus a read of the caller. A site whose caller cannot handle the propagated error receives a `keep` outcome with a log call instead of a `narrow` outcome.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS with a constraint | An added log call adds one line to a handler. Each touched function must stay inside 25 lines and 5 blocks. |
| II. Class-Based Architecture (No Wrappers) | PASS | The work adds no class and no wrapper function. |
| III. Safety-First | PASS with a gate | A narrowed type changes which errors reach the operator. Each `narrow` outcome needs a read of the caller. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request workflow. The container needs a rebuild after the last slice. |
| V. Observability and Logging | PASS with a gain | The work adds a log call to every handler that the code continues past. Every message stays ASCII. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | Each `keep` outcome carries a comment that states the reason. Each changed line carries an inline comment. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS with a gain | Requirement FR-011 adds the missing log call at every silent site. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS with a gate | Requirement FR-013 forbids a `# noqa: BLE001` directive. A `keep` outcome uses a plain comment and needs a stated reason. |

### The keep question

This plan expects a `keep` outcome at most sites. That expectation needs a justification against the "fix over suppress" rule.

A `keep` outcome is not a suppression. The site keeps the broad catch, gains a log call, and gains a comment that states the reason. The gate still reports the site, and the ruff `select` list still holds the rule, because a `keep` site holds no directive.

**Warning**: A contributor who adds `# noqa: BLE001` to reach a green gate defeats the whole work. Requirement FR-013 forbids that action, and the review must reject it.

A `keep` outcome therefore turns a silent handler into a loud one. That is the fix. The breadth is not the defect. The silence is the defect.

## Project Structure

### Documentation (this feature)

```text
specs/1794-blind-except-handlers/
├── spec.md              # The feature specification
├── plan.md              # This file
└── tasks.md             # The task list
```

### Source code (repository root)

The work touches 161 files. The list below names the slice boundary for each area. Each count uses the `--ignore-noqa` value.

```text
pyproject.toml                                        # Slice 15: the select list and the disable list

MistHelper.py                                         # Slice 11: 33 sites, coordinate with issue #1709
starlink_dashboard.py                                 # Slice 2: 8 sites, pylint never reads this file

src/
├── export/                                           # Slices 12 to 14: 94 sites, split by file
├── firmware/                                         # Slices 9 and 10: 62 sites, split by file
├── refactors/                                        # Slice 8: 43 sites, split if above 40
├── device/                                           # Slice 7: 34 sites
├── ssh/                                              # Slice 6: 32 sites, 18 of them hidden today
├── gateway/                                          # Slice 5: 24 sites
├── site/                                             # Slice 4: 18 sites
├── db/                                               # Slice 4: 17 sites
├── api/                                              # Slice 3: 16 sites
├── utils/                                            # Slice 3: 14 sites
├── websocket/                                        # Slice 3: 14 sites
├── ui/                                               # Slice 2: 12 sites
└── analytics/                                        # Slice 2: 10 sites
```

**Structure Decision**: The work stays inside the current tree. It creates no file and deletes no file.

## Phased approach

The work runs in three stages.

### Stage 1 - Reconcile the baseline

No edit starts before this stage closes. The stage produces one written record.

The record states the three counts, names the root that each tool reads, and explains each site in the difference. Requirement FR-003 blocks the first slice until the record holds an explanation for every site.

**Exit measurement**: The record exists. Issue #1792 has landed, and the default ruff count now equals the `--ignore-noqa` count at 500.

### Stage 2 - Audit the sites in slices

Slices 2 through 14 audit the sites. Each slice follows the same six steps.

1. List the sites in the slice with `ruff check <area> --select BLE001 --output-format concise`.
2. Read each site and its caller. Select an outcome of `delete`, `narrow`, or `keep`.
3. Apply the outcome. Add a log call at every site that the code continues past.
4. Record the outcome for each site in the pull request body.
5. Read the whole difference and confirm that no `# noqa: BLE001` directive appeared.
6. Run the full gate set and the full unit suite.

**Caution**: A narrowed type changes behavior. Read the caller before the edit. A caller that cannot handle the propagated error needs a `keep` outcome instead.

**Exit measurement**: The `BLE001` count reaches zero after the last slice.

### Stage 3 - Close both gates

Add `BLE001` to the ruff `select` list. Remove `W0718` from the pylint `disable` list. Rewrite the comment at `pyproject.toml` line 471, because it records a count and a judgment that this work replaces.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G", "BLE001"]
disable = ["C0114", "C0115", "C0116", "W0613"]
```

**Warning**: Both configuration changes must land in one pull request. A split leaves a window in which one tool reports the pattern and the other does not.

**Exit measurement**: `ruff check .` and the pylint gate both pass. A test handler that catches `Exception` fails both gates.

## Slice ledger

| Slice | Scope | Sites |
| - | - | - |
| 1 | Reconciliation only, no edit | 0 |
| 2 | src/analytics, src/ui, starlink_dashboard.py | 30 |
| 3 | src/api, src/utils, src/websocket | 44, split if needed |
| 4 | src/site, src/db | 35 |
| 5 | src/gateway | 24 |
| 6 | src/ssh | 32 |
| 7 | src/device | 34 |
| 8 | src/refactors | 43, split into two |
| 9 | src/firmware/firmware_manager.py | 28 |
| 10 | src/firmware, the rest | 34 |
| 11 | MistHelper.py | 33 |
| 12 | src/export, part one | about 33 |
| 13 | src/export, part two | about 33 |
| 14 | src/export, part three, and every remaining area | the remainder |
| 15 | pyproject.toml | 0 |

**Caution**: Slice 14 holds every area that the table above does not name. The implementer must split that slice further once the earlier slices land. No pull request may audit more than 40 sites.

## Risk register

| Risk | Likelihood | Effect | Control |
| - | - | - | - |
| The work starts before issue #1792 lands | Medium | 88 sites stay unaudited and the gate hides them | Task T004 blocks the first slice until the two ruff counts match |
| A contributor adds a `# noqa: BLE001` directive to reach a green gate | Medium | The gate reports a false clean state | Task T016 searches each difference for the directive. Requirement FR-013 forbids it. |
| A narrowed type turns a caught error into a crash | Medium | An operator meets a new failure | Each slice reads the caller and runs the whole unit suite |
| An added log call pushes a function above the complexity limit | Low | The radon gate fails | A log call adds no branch. Each slice runs `radon cc src/ -a -nb`. |
| Issue #1709 edits the same lines in `MistHelper.py` | Medium | A merge conflict | Slice 11 checks the state of issue #1709 first |
| The pylint count differs from the recorded 493 | High | The reconciliation record is wrong | Task T005 measures the count again instead of trusting the comment |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The work spans 15 pull requests | 500 sites each need a judgment, and a reviewer cannot judge 500 sites in one difference | A single pull request would merge without a real review, which defeats the purpose of an audit |
| Most sites receive a `keep` outcome | The breadth is correct on a cleanup path and around an undocumented third-party call | A blanket narrowing would turn a caught error into a new crash across the whole tree |
| The reconciliation stage produces no code change | A wrong baseline produces a wrong scope, and a wrong scope leaves sites unaudited in silence | An audit that starts from the 412 count misses 88 sites and reports a false clean state |
