# Implementation Plan: Ruff S Family Decision

**Branch**: The implementation needs its own branch. This document sits on `docs/1778-1780-specs`. | **Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1780-ruff-s-family-decision/spec.md`

**GitHub Issue**: [#1780](https://github.com/jmorrison-juniper/MistHelper/issues/1780)

## Summary

The root ruff configuration does not select the `S` family. Every `# noqa: S...` annotation therefore has no effect. Issue #1780 asks the team to choose between three options and to record the reason.

The research phase is complete. [research.md](research.md) holds the measured data for all three options. This plan turns that data into a decision, a written record, a contract update, and a guard that keeps the decision true.

The plan recommends Option 2, which keeps the current select list. The recommendation rests on two measurements. Option 3 would leave 111 Python files with no security scan. Option 1 would buy 10 new results for a cost of 62 double suppression comments and one ignore block for 13,440 test asserts.

## Technical Context

**Language/Version**: Python 3.13. The change touches configuration and documentation only.

**Primary Dependencies**: ruff 0.16.0 and bandit 1.9.4. Both versions come from `requirements-dev.txt`. The change adds no dependency.

**Storage**: N/A.

**Testing**: The guard in User Story 3 needs one new test. The existing suite must keep its pass count.

**Target Platform**: CI runs on Linux. Developers work on Windows. Both platforms report the same ruff counts, because ruff normalizes the path separator.

**Project Type**: static analysis policy and repository governance.

**Performance Goals**: The ruff job runs in under 1 second. The bandit job runs in about 10 seconds. Both sit in the fast group of the workflow. Neither sets the total workflow time.

**Constraints**:

- The root ruff `extend-exclude` list holds `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`.
- The bandit `exclude_dirs` list holds `tests`, `.venv`, `node_modules`, `scripts`, `specs`, and `tools/test_quality_analyzer/fixtures`.
- The two lists do not match, so the two tools read different trees.
- The test tree holds 13,440 `assert` statements. Pytest needs them.

**Scale/Scope**: 1 decision, 1 record, 1 contract update, and 1 guard test.

### Measurement contract

Run each command from the repository root with `.venv\Scripts\python.exe`.

```powershell
.venv\Scripts\python.exe -m ruff check --select S --statistics .
.venv\Scripts\python.exe -m ruff check --select S --statistics --exclude tests .
.venv\Scripts\python.exe -m ruff check --select S --ignore-noqa --statistics .
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1780.json" -q
```

| Measurement | Value on 2026-08-05 |
| - | - |
| Ruff `S` results, whole repository | 13,566 |
| Ruff `S` results, no test tree | 121 |
| Bandit results, tracked files | 0 |
| Latent `# noqa: S...` annotations | 1 |

The implementer must re-run every command before the decision. A count that differs means the code base moved, and the recommendation needs a fresh reading.

### Verified mechanics

The implementer probed four behaviors before this plan.

1. **Ruff reads `# noqa` only.** It does not read `# nosec`. Bandit reads `# nosec` only. The two forms never overlap.
2. **A `# noqa: S...` annotation is latent.** A run with `--ignore-noqa` reports a result that a normal run hides. Section R9 of [research.md](research.md) holds the proof.
3. **Ruff can add a `# noqa` comment automatically.** A person who runs `--fix` after adding `S` can create thousands of annotations in one command. The plan forbids that path.
4. **A subtree can hold its own ruff configuration.** The `mist-ops-platform/pyproject.toml` file selects a different rule set. The root `extend-exclude` entry means CI never reads it.

### Discovered risk: the ordering against issue #1778

Issue [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778) removes a latent `# noqa: S104` annotation from an untracked settings module. Bandit reports that same line as a MEDIUM `B104`.

Warning: If this work selects the `S` family before issue #1778 lands, the annotation activates and hides the MEDIUM result. The defect then stays invisible to both tools.

The control is simple. Choose Option 2, which never selects `S`. If the team overrides the recommendation, run `ruff check --select S --ignore-noqa` first and triage every hidden result.

### Discovered risk: the recommendation may not survive review

The plan recommends Option 2. A reviewer can disagree. Two counter arguments deserve a written answer.

1. **"Ruff finds 10 results that bandit misses."** True. Section R4 of [research.md](research.md) names all 10. Two of them are default passwords in `src/db/__init__.py`. The correct answer is a separate issue that corrects those 10 lines, not a second tool that reports 13,566 results to find them.
2. **"Editors show ruff inline and never show bandit."** True. That is a real developer experience gain. It costs 62 double suppression comments and a permanent second comment form. A bandit editor extension solves the same problem with no repository change.

The implementer must record the chosen answer even when the team overrides the recommendation.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS | The guard test holds one function. The configuration change touches one list. |
| II. Class-Based Architecture (No Wrappers) | PASS | The work adds no wrapper. |
| III. Safety-First | PASS | The work adds no input handling and no destructive operation. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request flow. The container needs no rebuild, because no runtime behavior changes. |
| V. Observability and Logging | PASS | The guard test uses ASCII only. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | Every line of the guard test carries a comment that states why the line exists. |
| VII. Action Logging (NON-NEGOTIABLE) | NOT APPLICABLE | A test needs no action log. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS with a statement | Option 2 keeps the current coverage. Requirement FR-018 demands a written statement if a choice reduces coverage. |

### The coverage question

The constitution prefers a correction over a suppression. Option 2 makes no correction and adds no coverage. That needs a defense.

Option 2 does not reduce coverage. It keeps the bandit gate that issue #889 hardened, and that gate reports zero results in tracked files today. The 10 results that ruff would add are real, and the plan routes them to their own issue. That route delivers the same corrections without a second tool, a second comment form, and 13,440 ignored test results.

## Project Structure

### Documentation (this feature)

```text
specs/1780-ruff-s-family-decision/
├── spec.md              # The feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output: the measured data for all three options
└── tasks.md             # The task list
```

### Source code (repository root)

The exact file list depends on the chosen option. The table states the file set for each option.

```text
specs/1780-ruff-s-family-decision/decision.md          # All options: the decision record

specs/1032-bandit-severity-gate/contracts/
└── suppression-comment.md                             # All options: state which comment form works

tests/guardrails/
└── test_no_latent_noqa_s.py                           # Option 2 only: the guard

pyproject.toml                                         # Option 1 and Option 3 only: the select list
.github/workflows/ci.yml                               # Option 3 only: delete the bandit job
```

**Structure Decision**: The work adds one decision record and one guard test. It changes one contract. Under Option 2 it changes no configuration, which is the point of the option.

## Phased approach

### Phase 0 - Re-measure (complete for the recorded date)

[research.md](research.md) holds the full measurement from 2026-08-05. The implementer must re-run every command in the measurement contract and must compare the counts.

**Exit measurement**: Every count matches [research.md](research.md), or the implementer records the drift and re-reads the recommendation.

### Phase 1 - Decide

- Read [research.md](research.md) section R10, which states the cost of each option.
- Choose one option.
- Write the decision record.

**Exit measurement**: The record names the option, the reason, the date, and the tool versions.

### Phase 2 - Update the suppression contract

- State which comment form suppresses a security result.
- State whether a `# noqa: S...` annotation has any effect.
- Under Option 2, state that such an annotation is latent and state the consequence.

**Exit measurement**: A reader learns the correct comment form from one document.

### Phase 3 - Add the guard (Option 2 only)

- Add a test that searches every tracked Python file for a `# noqa: S...` annotation.
- The test reports the file and the line number for each hit.
- The test must report zero hits at the time it lands.

**Exit measurement**: The test passes. A deliberate annotation makes it fail.

### Phase 4 - Apply the choice (Option 1 and Option 3 only)

The plan does not recommend this phase. It states the steps so that the team can price the work.

- Run `ruff check --select S --ignore-noqa` and triage every hidden result first.
- Add an ignore rule for `S101` under `tests/` in `[tool.ruff.lint.per-file-ignores]`.
- Add `S` to the select list.
- Add a second annotation to each of the 62 lines that already hold a `# nosec` comment.
- Under Option 3, delete the bandit job from `.github/workflows/ci.yml`, remove the `[tool.bandit]` table, remove `bandit` from `requirements-dev.txt`, and remove every one of the 117 `# nosec` comments.
- Under Option 3, remove `mist-ops-platform`, `web_portal`, and `src/maps` from the ruff exclude list, or record that 111 Python files lose their security scan.

**Exit measurement**: Every gate is green and no security result hides behind a latent annotation.

### Phase 5 - Close the loop

- Open a separate issue for the 10 production results in [research.md](research.md) section R4.
- State the ordering against issue #1778 in the pull request body.

**Exit measurement**: The new issue exists and the pull request names it.

## Complexity Tracking

| Item | Why it is needed | Simpler option that the plan rejected |
| - | - | - |
| A guard test under Option 2 | Issue #1719 removed the annotations once. Without a gate they return, and each one is a latent suppression. | A note in the contributing guide. A reader can miss a note. A gate cannot. |
| A separate issue for the 10 results | The results are real and need a correction. They do not need a second tool. | Fold them into this work. That mixes a policy decision with a code correction. |
| A written answer to each counter argument | A reviewer will raise them. An unwritten answer restarts the debate. | Record the choice only. The question then returns in six months. |

## Risks

| Risk | Effect | Control |
| - | - | - |
| The team selects `S` before issue #1778 lands. | The MEDIUM `B104` result hides for good. | Requirement FR-013 states the order. The pull request repeats it. |
| A person runs `ruff --fix` after adding `S`. | The repository gains thousands of unreviewed annotations in one command. | Task T014 forbids the flag and states the reason. |
| The team chooses Option 3 without reading section R6. | 111 Python files lose their security scan with no visible warning. | Success criterion SC-010 demands a written list of what the option gives up. |
| The recommendation ages out. | A future ruff release closes the rule gap and changes the answer. | Requirement FR-005 demands that the record state what would change the decision. |
