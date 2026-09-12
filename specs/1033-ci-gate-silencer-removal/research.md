# Phase 0 Research: CI Gate Silencer Removal

**Feature**: `1033-ci-gate-silencer-removal` | **Branch**: `ci/891-893-gate-silencers` | **Date**: 2026-07-28

The Technical Context in [plan.md](plan.md) holds no open `NEEDS CLARIFICATION` marker. This document records the eight decisions that closed the open questions before the design phase.

---

## R1: Remove the pylint ignore flag before any code fix

**Decision**: Delete `--ignore=maps,ssh,ui` from line 291 of `.github/workflows/ci.yml` in this work. Do not fix the 502 messages that the deletion makes visible.

**Rationale**: The specification records a measured baseline. The gate reports 757 messages with the flag and 1259 messages without it. Both runs exit 0, because the threshold is `--fail-under=9.5` and the score stays above it. The deletion therefore adds visibility and adds no build failure. A fix is a much larger slice that would hide the one line deletion inside 502 unrelated changes.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Fix the 502 messages first, then delete the flag. | The pull request would grow past a reviewable size. The deletion is the deliverable. The messages are a separate backlog. |
| Add a per-file `pylintrc` disable for the three packages. | This trades one silencer for three quieter silencers. It fails the goal of the feature. |
| Lower the threshold below 9.5 as insurance. | The measurement proves that no insurance is needed. Non-goal NG-007 forbids a threshold change. |

---

## R2: Change both vulture defaults in the workflow file

**Decision**: Set `'70'` at line 35 and at line 51 of `.github/workflows/ci.yml`.

**Rationale**: The file holds two `'90'` values for the same setting. Line 35 is the `workflow_call` input default. Line 51 is the `env` fallback that reads `${{ inputs.vulture-confidence || '90' }}`.

A `push` trigger and a `pull_request` trigger leave `inputs` empty, so the line 51 fallback applies. A `workflow_call` trigger that omits the input applies the line 35 default instead, and that value wins over the fallback. A change to line 51 alone therefore leaves a caller at confidence 90.

Requirement FR-008 asks for a default of 70. A partial change would satisfy the letter of the requirement for this repository and would break it for a caller. The plan changes both values.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Change line 51 only, because the specification names line 51. | A caller that uses `workflow_call` would still run at confidence 90. The silencer would survive in the reusable path. |
| Delete the `workflow_call` input and hardcode 70. | This removes a caller override that other repositories may need. Non-goal NG-008 forbids a new gate design. |

---

## R3: Leave the portable workflow copy out of scope

**Decision**: Do not change `.github/quality-gates-portable.yml` in this work. Record the divergence in the plan and in the pull request.

**Rationale**: That file is a template copy for other repositories. It sits outside `.github/workflows/`, so GitHub never runs it here. It holds `'90'` at line 41 and at line 57. It does not hold the pylint ignore flag, so issue #891 has exactly one site.

The specification scope table names `.github/workflows/ci.yml` only. A change to the portable copy would widen the pull request past the specification and would touch a file that no gate reads.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Update the portable copy in the same pull request. | The change would sit outside the specification scope. A reviewer would need to verify a file that no CI job runs. |
| Delete the portable copy, because it drifts from the live workflow. | Deletion is a separate decision with its own consumers. It belongs to its own issue. |

**Follow-up**: The implementer notes the drift in the pull request body. A maintainer decides later whether the portable copy needs a sync or a deletion.

---

## R4: Delete the whole `query-filters` block, not the entries inside it

**Decision**: When both exclusions leave the file, delete the `query-filters` key and the comment above it. Do not leave `query-filters:` with nothing under it.

**Rationale**: A YAML key with no value parses as `null`. The CodeQL Action expects a list under `query-filters`. A `null` value can fail the configuration parse and can stop the whole analysis. A stopped analysis produces no finding count, which is the exact evidence that this work needs.

The resulting file holds only the `name` key. That is a valid CodeQL configuration file.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Leave `query-filters: []` as an empty list. | An empty list parses, but it leaves a key that carries no meaning. A future reader would wonder what the team removed. |
| Comment out the two exclusions instead of deleting them. | A commented suppression is a suppression that waits to return without a review. Requirement FR-017 asks for zero undefended exclusions. |

---

## R5: Remove both CodeQL exclusions in one experiment

**Decision**: Remove the exclusion of `py/stack-trace-exposure` and the exclusion of `py/clear-text-logging-sensitive-data` in the same commit.

**Rationale**: Requirement FR-012 covers the first query and requirement FR-013 covers the second one. Both need a CI round trip, and one run answers both. A split into two runs would double the wait for no extra information.

The two queries carry different starting points. The first exclusion holds no rationale at all. The second exclusion holds an eight line rationale with one stale claim. Issue #1710 found a partial API token value in `data/script.log`, which contradicts the claim that the tool never logs an actual secret. Both exclusions therefore need fresh evidence, and one run supplies it.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Remove `py/stack-trace-exposure` first, then `py/clear-text-logging-sensitive-data` in a second pull request. | Two round trips return the same information as one. Requirement FR-013 already asks for both counts in this feature. |
| Keep the second exclusion and correct only its rationale text. | A rationale without a fresh measurement repeats the mistake that issue #1710 exposed. The evidence must come first. |

**Risk note**: If both queries report findings, the pull request carries two decisions instead of one. [data-model.md](data-model.md) holds a separate decision record for each query, so the two decisions stay independent.

---

## R6: Land all three edits in one push

**Decision**: Commit the pylint edit, the vulture edit, and the CodeQL edit together. Push once. Open one pull request.

**Rationale**: Only the CodeQL question needs CI. The other two questions already hold a local answer. One push starts one Quality Gates run and one CodeQL run. The pylint job and the vulture job then confirm the local result at the same time that the CodeQL job produces the new evidence.

A split would also create a merge conflict. Issue #891 and issue #892 edit the same file, and issue #891 edits line 291, which open issue #888 also edits. The specification section "Sequencing and the line 291 collision" sets the merge order.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Merge the pylint edit and the vulture edit first, then run the CodeQL experiment in a second pull request. | This spends two round trips and reopens line 291 a second time while issue #888 waits. |
| Run the CodeQL experiment alone first to reduce the blast radius. | The two proven edits carry no risk, so they add no blast radius. A separate run would only add delay. |

---

## R7: Confirm that a CodeQL query ran before recording a count of zero

**Decision**: Treat a result of zero findings as unconfirmed until the implementer sees the query identifier in the run output or in the alert list for the branch.

**Rationale**: The configuration declares no `queries` key, so CodeQL runs the default suite. A removed exclusion produces a finding only when the default suite holds that query. A count of zero can therefore mean one of two different things. The first meaning is a clean result. The second meaning is a query that never executed.

The two meanings lead to opposite conclusions. A clean result closes the issue. A query that never ran means the exclusion was always inert, which is a different finding and needs a different note in the pull request.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Accept a zero count at face value. | A false clean result would close a security issue on no evidence. |
| Add an explicit `queries` key that names both queries. | This changes the gate design. Non-goal NG-008 forbids a new query pack. The default suite most likely already holds both queries, because the team excluded them for a reason. |

[quickstart.md](quickstart.md) states the confirmation procedure.

---

## R8: Stop the vulture floor at 70

**Decision**: Set the confidence floor to 70. Do not set it to 60 in this work.

**Rationale**: The re-measured baseline shows the cliff.

| Confidence | Findings |
| - | - |
| 90 | 0 |
| 70 | 0 |
| 60 | 306 |

A move to 70 costs nothing today and removes a silencer that could hide a future defect. A move to 60 reports 306 findings with a high false positive rate. Two patterns drive that rate. The first pattern is module level dependency injection. The second pattern is a dynamic `mh.*` lookup that vulture cannot resolve. Issue #1703 removes the second pattern, so the rate needs a fresh measurement after that issue lands.

**Alternatives considered**:

| Alternative | Why the plan rejects it |
| - | - |
| Move straight to 60 and suppress the 306 findings with a whitelist file. | A whitelist is a new silencer. It fails the goal of the feature. |
| Move straight to 60 and fix all 306 findings. | Most of them are false positives today. The team would spend the effort twice, because issue #1703 changes the input. |
| Stay at 90 until issue #1703 lands. | The measurement proves that 70 is free now. A free improvement should not wait. |

Non-goal NG-003 states the boundary. Requirement FR-021 records the later slice.
