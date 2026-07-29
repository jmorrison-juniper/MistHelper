# Implementation Plan: CI Gate Silencer Removal

**Branch**: `ci/891-893-gate-silencers` (SpecKit feature directory `1033-ci-gate-silencer-removal`) | **Date**: 2026-07-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1033-ci-gate-silencer-removal/spec.md`

**GitHub Issues**: [#891](https://github.com/jmorrison-juniper/MistHelper/issues/891), [#892](https://github.com/jmorrison-juniper/MistHelper/issues/892), [#893](https://github.com/jmorrison-juniper/MistHelper/issues/893)

## Summary

Three CI quality gates hide findings from the reviewer. This work removes the silencer from each one.

Two of the three changes are small and proven. Issue #891 deletes `--ignore=maps,ssh,ui` from the pylint step. Issue #892 lowers the vulture confidence floor from 90 to 70. A local run on this checkout confirms that both gates still exit 0. Neither change needs a code fix first.

The third change is a CI experiment. Issue #893 removes two CodeQL query exclusions. Nobody can measure a CodeQL result on a workstation, because CodeQL runs only in CI. The implementer removes the exclusions, opens the pull request, reads the CodeQL result, and then either keeps the removal or restores an exclusion with a written rationale.

The plan puts all three edits in one push. One CI run then answers the CodeQL question while the pylint gate and the vulture gate are already verified. The implementer never waits for a second round trip to learn a result that a local command already proved.

## Technical Context

**Language/Version**: Python 3.13. The workstation interpreter is `.venv\Scripts\python.exe`. The global `python` on this machine is broken and must not run any gate command.

**Primary Dependencies**: `pylint`, `vulture`, and the GitHub CodeQL Action v4. This work adds no dependency and pins no version.

**Storage**: N/A. The work changes two configuration files and one changelog file.

**Testing**: The `pytest` suite is unaffected, because no Python source file changes. Validation runs the two gate commands on the workstation and reads the CI result for the third gate.

**Target Platform**: The CI runner is `ubuntu-latest`. The developer workstation is Windows 11.

**Project Type**: CI configuration change. This work creates no module, no class, and no function.

**Performance Goals**: The pylint job must finish inside its existing 10 minute timeout. The vulture job must finish inside its existing 5 minute timeout.

**Constraints**:

- CodeQL runs only in CI. The implementer cannot measure a CodeQL result locally.
- Both workflows trigger on `pull_request` against `main` and on `push` to `main`. A push to the feature branch alone triggers neither workflow. The pull request must open before any gate runs.
- Line 291 of `.github/workflows/ci.yml` also belongs to open issue #888. Only one pull request may hold that line at a time.

**Scale/Scope**: 2 configuration files, 3 gate edits, and 1 changelog entry. The edit touches about 6 lines and adds about 20 comment lines.

### Measurement contract

The implementer re-measured the vulture baseline on 2026-07-28 at commit `e985807` on branch `ci/891-893-gate-silencers`. The result matches the specification exactly.

```powershell
.venv\Scripts\python.exe -m vulture src/ --min-confidence 90   # 0 findings
.venv\Scripts\python.exe -m vulture src/ --min-confidence 70   # 0 findings
.venv\Scripts\python.exe -m vulture src/ --min-confidence 60   # 306 findings
```

| Gate | Configuration | Result | Gate exit code |
| - | - | - | - |
| pylint | With `--ignore=maps,ssh,ui`, which CI runs today | 757 messages | 0 |
| pylint | Without the ignore list | 1259 messages | 0 |
| vulture | Confidence 90, which CI runs today | 0 findings | 0 |
| vulture | Confidence 70, the target of this work | 0 findings | 0 |
| vulture | Confidence 60, out of scope | 306 findings | 3 |
| CodeQL | Two exclusions active, which CI runs today | Unknown | 0 |

The pylint counts come from the specification. The vulture counts come from the command block above. The CodeQL row stays unknown until the pull request opens.

### Discovered risk 1: the vulture default appears twice in one file

The specification names line 51 of `.github/workflows/ci.yml`. That line holds the `env` fallback.

```yaml
VULTURE_CONFIDENCE: ${{ inputs.vulture-confidence || '90' }}
```

Line 35 of the same file holds a second `'90'`. That line is the `workflow_call` input default.

```yaml
      vulture-confidence:
        type: string
        default: '90'
```

A `push` trigger and a `pull_request` trigger leave `inputs` empty, so the line 51 fallback applies. A `workflow_call` trigger that omits the input applies the line 35 default instead. A change to line 51 alone therefore leaves a caller at confidence 90.

**Decision**: the implementer changes both values to `'70'`. Research decision R2 records the reasoning.

### Discovered risk 2: a portable copy of the workflow carries the same default

The file `.github/quality-gates-portable.yml` is a template copy for other repositories. It holds `'90'` at line 41 and at line 57. It sits outside `.github/workflows/`, so GitHub never runs it in this repository.

The specification scope table names `.github/workflows/ci.yml` only. This work leaves the portable copy alone and records the divergence. Research decision R3 states the reason and names the follow-up.

### Discovered risk 3: a push alone produces no CodeQL result

Both workflows declare the same triggers.

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

The branch `ci/891-893-gate-silencers` is not `main`. A `git push` on that branch starts no run. The implementer must open the pull request to start the CodeQL analysis. The Quality Gates workflow also accepts `workflow_dispatch`, but the CodeQL workflow does not. The pull request is the only path to a CodeQL result.

### Discovered risk 4: zero findings can mean the query never ran

The CodeQL configuration declares no `queries` key, so CodeQL runs the default suite. A removed exclusion produces a finding only when the default suite holds that query. A result of zero findings is therefore ambiguous on its own.

The implementer must confirm that each query ran before the implementer records a count of zero. [quickstart.md](quickstart.md) states the confirmation procedure.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | N/A | The work changes YAML and Markdown. It adds no function and no class. |
| II. Class-Based Architecture (No Wrappers) | N/A | The work adds no Python code. |
| III. Safety-First | PASS | The work changes no input handling and no destructive operation. The CodeQL experiment reads a report. It writes no device configuration. |
| IV. Full Deployment Pipeline | ADAPTED | Principle IV describes a direct push to `main` and a container rebuild. This work follows the multi-agent branch workflow instead. No runtime code changes, so the container image needs no rebuild. See Complexity Tracking. |
| V. Observability and Logging | PASS | Every comment that this work adds uses ASCII only. The existing CodeQL comment holds an em dash. The rewrite replaces it with an ASCII hyphen. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS with a mapping | The rule targets executable Python lines. This work edits YAML. The equivalent duty is the review comment contract. Every gate that this work touches carries a comment that states why the gate runs as it does. |
| VII. Action Logging (NON-NEGOTIABLE) | N/A | The work adds no Python action. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS with a gate | This work removes suppressions. It restores an exclusion only when the CodeQL evidence supports the restoration. A restored exclusion carries the three facts from the issue #890 precedent. A bare exclusion fails review. |

### The two suppression questions

A reviewer will ask two questions. The plan answers both here.

**Question 1: why does this work leave 502 pylint messages unfixed?**

The messages were always there. The `--ignore` flag hid them from the report and from the reviewer. It never hid them from the score, because pylint scores only the files that it reads. The gate threshold is `--fail-under=9.5` and the measured run without the ignore list exits 0. The removal therefore adds visibility and adds no build failure. Non-goal NG-001 defers the fix. Requirement FR-020 opens a follow-up issue that tracks the messages.

**Question 2: why does this work stop at vulture confidence 70?**

The measured cliff sits between 70 and 60. A move to 70 costs nothing today. A move to 60 reports 306 findings with a high false positive rate. Two patterns drive that rate. The first pattern is module level dependency injection. The second pattern is a dynamic `mh.*` lookup that vulture cannot resolve. Issue #1703 removes the second pattern. A move to 60 belongs to a later slice that waits for that issue. Non-goal NG-003 states the boundary. Requirement FR-021 records the future slice.

## Project Structure

### Documentation (this feature)

```text
specs/1033-ci-gate-silencer-removal/
├── plan.md              # This file
├── research.md          # Phase 0 output: the eight decisions
├── data-model.md        # Phase 1 output: the gate ledger and the CodeQL decision states
├── quickstart.md        # Phase 1 output: how to verify each gate
├── contracts/
│   └── review-comment.md   # The three-fact comment format and the gate command contract
├── checklists/          # Pre-existing
└── tasks.md             # Phase 2 output from /speckit.tasks. This command does not create it.
```

### Source code (repository root)

The work changes three files. It creates no source file and deletes no source file.

```text
.github/
├── workflows/
│   └── ci.yml                    # Issue #891 line 291, issue #892 lines 35 and 51, plus two step comments
└── codeql/
    └── codeql-config.yml         # Issue #893, the two query-filters exclusions and the header comment

CHANGELOG.md                      # One entry under ## [Unreleased]
```

**Structure Decision**: this feature edits CI configuration in place. It introduces no directory and no module. The `src/` tree stays untouched, because non-goal NG-009 forbids a refactor of `src/maps`, `src/ssh`, and `src/ui`.

## Execution Phases

The plan orders the work so that one CI run answers every open question.

### Phase A: the two proven edits

The implementer makes the pylint edit and the vulture edit first. Both carry a measured result, so the implementer verifies each one on the workstation before the push.

1. Delete `--ignore=maps,ssh,ui` from the pylint `run` line.
2. Add a comment above the pylint step that repeats the issue #890 review rule for any future ignore flag.
3. Change both `'90'` defaults for `vulture-confidence` to `'70'`.
4. Add a comment above the vulture step that states the review date, the measurement, and issue #1703 as the next review trigger.
5. Run the two verification commands from [quickstart.md](quickstart.md). Both must exit 0.

### Phase B: the CodeQL experiment setup

The implementer removes both exclusions and prepares the pull request. No local command can predict the result.

1. Delete the whole `query-filters` block from `.github/codeql/codeql-config.yml`, including the header comment above it. Research decision R4 explains why an empty key is unsafe.
2. Confirm that the file still parses as YAML.
3. Write the changelog entry under `## [Unreleased]`. Record the pylint counts and the vulture counts. Leave a clear placeholder for the CodeQL counts.

### Phase C: one push and one pull request

The implementer commits Phase A and Phase B together and pushes once.

1. Commit all three edits on `ci/891-893-gate-silencers`.
2. Push the branch.
3. Open the pull request against `main`. This step starts the Quality Gates workflow and the CodeQL workflow. A push alone starts neither.
4. Confirm that the pylint job and the vulture job pass in CI. The local run already predicted this result.

### Phase D: read the CodeQL result and branch on it

The implementer reads the CodeQL result for the branch and then follows one of three paths for each query. [data-model.md](data-model.md) holds the full decision table.

| Outcome | Action | Artifact |
| - | - | - |
| The query ran and reported zero findings. | Keep the removal. | The pull request records the count and the run link. |
| The query reported findings that the team accepts as false positives. | Restore that one exclusion with the three required facts. | The comment holds the review date, the CodeQL run link, and the next review trigger. |
| The query reported findings that the team accepts as real. | Restore that one exclusion with the three facts and open a follow-up issue for the fix. | The pull request links the follow-up issue. |

The implementer pushes any restoration as a second commit on the same pull request. The pull request stays open until every query holds a recorded decision.

### Phase E: close the record

1. Open the follow-up issue for the 502 pylint messages and link it from the pull request. This satisfies FR-020.
2. Record the vulture confidence 60 slice against issue #1703. This satisfies FR-021.
3. Fill the CodeQL counts into the changelog entry.
4. Run the Simplified Technical English linter on every changed prose file. Each file must score 80 or above.

### Why this order

The CodeQL question needs a CI round trip. The pylint question and the vulture question do not. A separate pull request for each issue would spend three round trips and would create a merge conflict on line 291, because issue #891 and issue #892 edit the same file. One push spends one round trip and creates no internal conflict.

The order also protects the sequencing rule in the specification. This work must merge before issue #888 starts, because this work deletes part of line 291 and issue #888 rewrites the rest of it.

## Complexity Tracking

> The Constitution Check records three deviations. Each one carries a justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| One pull request closes three GitHub issues. The global git rule asks for one issue per pull request. | Issue #891 and issue #892 edit the same file, and issue #891 edits a line that open issue #888 also edits. Three pull requests would create a three way conflict on one line. All three issues share one acceptance rule from issue #890. | Three separate pull requests would spend three CI round trips and would produce a conflict on line 291 of `.github/workflows/ci.yml`. The specification records this grouping decision in the section "Grouping decision". |
| Principle IV asks for a direct push to `main` and a container rebuild. | The multi-agent git workflow requires a branch and a pull request for every change. The CodeQL result is only readable from a pull request run. | A direct push to `main` would place an unverified CodeQL experiment on the default branch. No runtime code changes, so a container rebuild would produce an identical image. |
| The work makes 502 pylint messages visible and fixes none of them. | The gate threshold is `--fail-under=9.5`, and the measured run without the ignore list exits 0. Visibility is the deliverable. A fix is a separate, much larger slice. | A combined visibility and fix slice would produce an unreviewable pull request. Non-goal NG-001 defers the fix and requirement FR-020 tracks it in a follow-up issue. |
