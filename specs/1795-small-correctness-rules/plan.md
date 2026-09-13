# Implementation Plan: Small Correctness Rule Cleanup

**Branch**: `lint/1795-small-correctness` (SpecKit feature directory `1795-small-correctness-rules`) | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1795-small-correctness-rules/spec.md`

**GitHub Issue**: [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795)

## Summary

Six small rule families report 146 sites. Five families come from ruff and one family comes from pylint.

This plan clears one family at a time, in order of risk. The family that names a real cross-platform defect lands first. The family that can change behavior lands last.

Each family takes its own pull request. The gate change lands after every family reports zero results.

## Technical Context

**Language/Version**: Python 3.13 (`pyproject.toml` target `py313`)

**Primary Dependencies**: `ruff` 0.16.0 and `pylint` 4.0.6. This work adds no dependency. It adds one standard-library import, which is `typing.ClassVar`, to several modules.

**Storage**: Not applicable. The work changes call sites, annotations, and one configuration line.

**Testing**: `pytest` with `--cov=src/ --cov-fail-under=80`. The suite must keep its pass count for each family.

**Target Platform**: The CI runner uses Linux. A developer works on Windows. The `W1514` family exists because those two platforms use a different default encoding.

**Project Type**: Static analysis cleanup with one behavior-sensitive family. The work adds no module and no class.

**Performance Goals**: The lint gate must stay inside its current runtime.

**Constraints**:

- The root ruff line length is 120 characters. A `ClassVar` annotation and an `encoding` argument both make a line longer, so a long line can need a wrap.
- `ruff check .` reads the whole repository. Its `extend-exclude` list drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`.
- `mypy` reads `src/` and `MistHelper.py`. Every `RUF012` annotation faces that gate.
- `pylint` reads `MistHelper.py` and `src` only. Pull request #1788 changed the job scope, so the implementer must confirm the current scope.

**Scale/Scope**: 146 sites, 6 families, about 70 files, and one configuration line.

### Measurement contract

Run the two commands below before each family. Record the value in the family pull request.

```powershell
.venv\Scripts\python.exe -m ruff check . --select DTZ005,ISC004,C408,RUF012,SIM103 --statistics
.venv\Scripts\python.exe -m pylint MistHelper.py src --disable=all --enable=W1514 --score=n
```

The expected ruff output holds five lines.

```text
60      RUF012  mutable-class-default
56      DTZ005  call-datetime-now-without-tzinfo
13      ISC004  implicit-string-concatenation-in-collection-literal
 9      SIM103  needless-bool
 3      C408    unnecessary-collection-call
```

The expected pylint output holds 5 result lines.

If any count differs, stop. Record the new count in this plan and continue with the new value.

### Verified mechanics

A maintainer probed the counts on 2026-08-06 at commit `08a75d2`. Four results shape the tasks.

1. The five family counts in issue #1795 all match the measured values. The issue total of 137 is correct for its own family set.
2. Ruff reports no automatic repair for these families under the safe setting. It offers 16 repairs under `--unsafe-fixes`. This plan does not use that flag.
3. `DTZ005` reports 56 by default and 57 with `--ignore-noqa`. One site hides behind a directive that issue #1792 removes.
4. `SIM103` reports 9 sites. That family sits outside the issue text, and the section "Correction" in [spec.md](spec.md) records the reason.

### Discovered risk: two files carry sites in two families

`src/firmware/firmware_manager.py` holds 5 `DTZ005` sites and 3 `RUF012` sites. `src/reports/e911_bssid.py` holds 3 of each.

The two families land in two pull requests. A concurrent edit of the same file produces a merge conflict.

The control is the order in requirement FR-010. The `RUF012` family lands before the `DTZ005` family, and neither family starts before the earlier one merges.

### Discovered risk: an unsafe repair changes behavior

Ruff reports 16 hidden repairs under `--unsafe-fixes`. The `DTZ005` repair sits in that set, because an aware value can change the result of a comparison.

The control is a hand repair with a byte-identical proof. This plan forbids `--unsafe-fixes` for every family.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS | The work adds no function. A `SIM103` repair removes two blocks and adds one line, which lowers the block count. |
| II. Class-Based Architecture (No Wrappers) | PASS | The work adds no class and no wrapper function. |
| III. Safety-First | PASS with a gate | The `DTZ005` family changes a value that the code compares and prints. Requirement FR-007 demands a proof for each site. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request workflow. The container needs a rebuild, because the runtime code changes. |
| V. Observability and Logging | PASS with a note | A `DTZ005` change can alter a printed timestamp. The proof step covers the log text and the filename. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | Every changed line carries an inline comment. A `ClassVar` annotation states that the attribute is a class constant. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS | The work adds no action and therefore adds no log call. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS | The work adds no suppression. Non-goal NG-001 states this rule. |

## Project Structure

### Documentation (this feature)

```text
specs/1795-small-correctness-rules/
├── spec.md              # The feature specification
├── plan.md              # This file
└── tasks.md             # The task list
```

### Source code (repository root)

The work touches about 70 files across six families.

```text
pyproject.toml                                        # Family 6: add five rules to the select list

MistHelper.py                                         # W1514 x2, ISC004 x4, C408 x2
starlink_dashboard.py                                 # RUF012 x4

src/
├── analytics/site_analytics_configurator.py          # RUF012 x6
├── api/api_data_fetcher.py                           # SIM103 x1
├── audit/filter.py                                   # SIM103 x1
├── cache/cache_utils.py                              # RUF012 x2, SIM103 x1
├── config/config_utils.py                            # W1514 x1
├── export/const_definitions_exporter.py              # RUF012 x3
├── firmware/
│   ├── bulk_switch_upgrader.py                       # DTZ005 x5
│   ├── firmware_manager.py                           # DTZ005 x5, RUF012 x3
│   └── org_ap_upgrader.py                            # DTZ005 x3
├── reports/e911_bssid.py                             # DTZ005 x3, RUF012 x3
├── site/bulk_radius_wlan_config_manager.py           # DTZ005 x4, RUF012 x3
├── ssh/batch/interactive_batch_executor.py           # DTZ005 x4
├── utils/
│   ├── address_utils.py                              # RUF012 x4
│   ├── operation_registry.py                         # RUF012 x3
│   └── rate_limiting.py                              # W1514 x2
└── websocket/
    ├── diagnostics/arp_executor.py                   # ISC004 x1
    └── service_ping_manager.py                       # SIM103 x1

tools/
├── codemod_logging_lazy.py                           # SIM103 x1
├── compliance_analyzer/analyzers.py                  # SIM103 x1
├── refactor_analyzer/reporting.py                    # ISC004 x8
├── ste_linter/parsing/markdown.py                    # SIM103 x1
└── test_quality_analyzer/discovery.py                # SIM103 x1

tests/
├── unit/org/test_org_synthetic_probes_manager.py     # SIM103 x1
└── unit/troubleshooting/                             # C408 x1
    └── test_marvis_troubleshoot_utils_extended.py
```

**Structure Decision**: The work stays inside the current tree. It creates no file and deletes no file.

## Phased approach

The work runs one family at a time. Each family ends with a measurement.

### Family 1 - W1514, the cross-platform defect (5 sites, 4 files)

This family lands first, because it is the only one that names a real defect.

Add `encoding="utf-8"` to each `open()` call. Confirm the file mode first, because a binary mode takes no encoding argument.

Then check the pylint job scope in `.github/workflows/ci.yml`. The job must read every file that holds a site. Pull request #1788 changed that scope.

**Exit measurement**: The pylint `W1514` count reads 0.

### Family 2 - C408, the smallest family (3 sites, 2 files)

Replace each `dict()` call with a `{}` literal. The change is safe, because the two forms produce the same object.

**Exit measurement**: `C408` reads 0.

### Family 3 - SIM103, the boolean returns (9 sites, 9 files)

Replace each `if` and `else` pair with a direct return of the condition.

**Caution**: Confirm that the condition is a boolean. A condition that returns a truthy value changes the return type after the repair. Add `bool(...)` where the type is not certain.

**Exit measurement**: `SIM103` reads 0.

### Family 4 - ISC004, the implicit concatenation (13 sites, 3 files)

Read each site first. A missing comma produces the same shape as a deliberate concatenation, and the two need a different repair.

Record the count of sites that held a missing comma. Success criterion SC-005 reads that count. A value above zero names a real defect that this work repaired.

**Exit measurement**: `ISC004` reads 0.

### Family 5 - RUF012, the class constants (60 sites, 32 files)

Add a `typing.ClassVar` annotation to each attribute. Add the import where the module does not hold it.

**Warning**: Run mypy after each file. A wrong annotation changes the inferred type for every reader of that attribute, and the type gate then fails in a file that this work never touched.

The family holds 60 sites in 32 files, so it needs two or three pull requests to stay reviewable.

**Exit measurement**: `RUF012` reads 0 and the mypy gate stays green.

### Family 6 - DTZ005, the naive datetime values (57 sites, 26 files)

This family lands last, because it is the only one that can change behavior.

**Warning**: This family must not start before issue #1792 lands. One site hides behind a `# noqa` directive, and the default run reports 56 instead of 57.

Each site needs a byte-identical proof. Capture the printed output before the change and after the change. Compare the two captures. Pull request #1791 records the model for 4 sites.

Check each comparison. A naive value and an aware value raise `TypeError` when they compare. The repair must convert both sides or neither.

The family holds 57 sites in 26 files, so it needs two pull requests to stay reviewable.

**Exit measurement**: `DTZ005` reads 0 with `--ignore-noqa` and every site holds a proof.

### Family 7 - Close the gate (1 file)

Add the five ruff rules to the `select` list.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G", "C408", "DTZ005", "ISC004", "RUF012", "SIM103"]
```

**Warning**: This step must follow every family. The gate fails on every push while any site remains.

**Exit measurement**: `ruff check .` passes with the new list. A test site in each family fails the gate.

## Risk register

| Risk | Likelihood | Effect | Control |
| - | - | - | - |
| An `ISC004` site held a missing comma | Medium | The repair changes the list length and changes behavior | Task T017 reads each site before the edit |
| A `RUF012` annotation names the wrong type | Medium | The mypy gate fails in another file | Task T021 runs mypy after each file |
| A `DTZ005` change shifts a printed timestamp | High | An operator reads a different value | Task T025 captures the output before and after each site |
| A `DTZ005` change breaks a comparison | Medium | The code raises `TypeError` at run time | Task T026 reads every comparison that reads the changed value |
| The `DTZ005` family starts before issue #1792 lands | Medium | One site stays unrepaired and the gate hides it | Task T024 blocks the family until the two counts match |
| Two families edit the same file at the same time | Medium | A merge conflict | The family order in FR-010 keeps them apart |
| The pylint job does not read a `W1514` file | Medium | The gate reports a clean state that is not true | Task T009 reads the job scope in `.github/workflows/ci.yml` |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The work spans about 9 pull requests | The `RUF012` family and the `DTZ005` family each hold more sites than one reviewable difference | A single pull request would hold 146 sites across six families with six different risk profiles |
| The `DTZ005` family needs a proof for each site | An aware value can change a printed timestamp and can break a comparison | A mechanical repair with no proof would ship a silent output change to every operator |
| This plan forbids `--unsafe-fixes` | Ruff marks the repair unsafe because it can change behavior | An automatic repair would apply 16 behavior changes without a review |
