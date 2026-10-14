# Tasks: SSR lab runbook validation

**Input**: [Specification](spec.md), [plan](plan.md), and the four records under `design/`.

**Prerequisites**: [Research](design/research.md), [evidence model](design/data-model.md),
[observation contract](design/contracts/lab-evidence.md), and [validation guide](design/quickstart.md).

**Status**: Generated, not executed. All six physical observations remain blocked on human lab access.
The current assignment stops after artifact validation and analysis.
These are future implementation tasks, not permission to execute them.

## Format: `[ID] [P?] [Story] Description`

Each task names its output path.
All paths are repository-relative.
`test-artifacts/issue-3960/` is an ignored, local evidence directory, not a tracked deliverable.
Do not add raw output or secrets to Git.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm current ownership before a later implementation begins.

- [ ] T001 Recheck #3959 and open pull request overlap. Record ownership in `test-artifacts/issue-3960/ownership.md`. Exclude the protected verifier. Respect FR-011.
- [ ] T002 Obtain human lab access and record the SSR releases, fiber port, and independent console in `test-artifacts/issue-3960/preflight.md`. Stop without authorization.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define reviewable records before any human observation.

- [ ] T003 Create `test-artifacts/issue-3960/evidence-index.md` using `design/data-model.md`. Apply FR-001, FR-008, and FR-009 to all six rows.

T003 must apply these model constraints verbatim:

| Field | Required constraint |
| --- | --- |
| Observation ID | One of OBS-01 through OBS-06. Keep the issue order. |
| Release | Record the measured SSR release. Never infer it from the intended target. |
| Port type | Required for interface observations. OBS-04 requires a fiber port. |
| Timestamp | Record UTC in ISO 8601 form. |
| Command or action | Use the matching observation contract. |
| Sanitized output | Preserve exact errors and field names. Remove customer identifiers and secrets. |
| Status | One of `Not run`, `Observed`, `Accepted`, or `Inconclusive`. |
| Cause or limitation | Required for `Not run` or `Inconclusive`. |
| Reviewer | Identify the reviewer when status becomes `Accepted`. |
| Destination | Identify the specific runbook section from the contract. |

Start all six rows at `Not run`.
Do not change status from a source citation or an artifact check.

## Phase 3: User Story 1 - Verify optic guidance (Priority: P1)

**Goal**: Obtain four release-specific optic observations.

**Independent Test**: A reviewer can compare OBS-01 through OBS-04 with the exact release and port conditions.
Unexpected output must remain visible.
No US2 or US3 result is required to review this story.

- [ ] T004 [US1] Ask the human to collect OBS-01 on SSR 7.0.x in `test-artifacts/issue-3960/obs-01.md`. Preserve the exact malformed-command result for FR-002.
- [ ] T005 [US1] Ask the human to collect OBS-02 on SSR 7.0.x in `test-artifacts/issue-3960/obs-02.md`. Preserve the exact named-command result for FR-003.
- [ ] T006 [US1] Ask the human to collect OBS-03 in `test-artifacts/issue-3960/obs-03.md`. Compare all four fallback-interface field claims for FR-004.
- [ ] T007 [US1] Ask the human to collect OBS-04 from a fiber port on SSR 7.1.0-50r1 or later in `test-artifacts/issue-3960/obs-04.md`. Record exact fields for FR-005.
- [ ] T008 [US1] Review all four sanitized outputs. Update section 11, step C2, the fallback optic procedure, and corresponding verification rows in `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md`.

T004 through T007 use the exact commands in the observation contract.
No agent executes them during the current assignment.
T008 requires accepted evidence and separate authorization for runbook changes.

## Phase 4: User Story 2 - Verify Mist state fields (Priority: P2)

**Goal**: Confirm the detailed command output without assuming summary columns are detailed fields.

**Independent Test**: Compare OBS-05 with both claimed field names.
This story does not depend on the optic observations.

- [ ] T009 [US2] Ask the human to collect `show mist detail` in `test-artifacts/issue-3960/obs-05.md`. Confirm or correct `Agent` and `Connection` for FR-006.
- [ ] T010 [US2] Review the sanitized detailed output. Correct step D7 and its verification row in `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md` only from accepted evidence.

## Phase 5: User Story 3 - Verify portal cloud-loss behavior (Priority: P3)

**Goal**: Observe portal behavior safely during verified lab cloud loss.

**Independent Test**: A reviewer sees approval, a healthy baseline, confirmed loss, actual tool results, and confirmed recovery in OBS-06.
An ineffective block or failed recovery cannot pass.

Caution: blocking TCP port 443 can interrupt Mist management and require console recovery.

- [ ] T011 [US3] Obtain explicit human approval for the isolated experiment in `test-artifacts/issue-3960/cloud-approval.md`. Verify the console, stop conditions, and restoration procedure before any network change.
- [ ] T012 [US3] Have the approved human collect OBS-06 in `test-artifacts/issue-3960/obs-06.md`. Record baseline, confirmed cloud loss, portal results, and confirmed recovery for FR-007.
- [ ] T013 [US3] Review OBS-06. Correct the cloud-path conclusion and verification row in `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md` only when the evidence proves the result.

T012 is a human lab task, not an automated implementation step.
If the tools operate, T013 must correct the last sentence.
If cloud loss or recovery is unconfirmed, keep OBS-06 incomplete and escalate to the human.

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T014 Review all six rows in `test-artifacts/issue-3960/evidence-index.md`. Check redaction, release, timestamp, reviewer, destination, and missing-result causes for FR-008 through FR-010.
- [ ] T015 Add `changelog.d/issue-3960-ssr-lab-results.md` for the later evidence-based runbook change. Name issue #3960 and the actual change type for FR-012.
- [ ] T016 Run STE and local link checks on every changed Markdown file. Record exact commands and results in `test-artifacts/issue-3960/checks.md`.
- [ ] T017 Perform the authorized publication gates from `AGENTS.md` and the constitution. Record the reviewed six-observation completion decision in `test-artifacts/issue-3960/publication.md`.

T017 requires separate authorization to implement and publish.
It includes the applicable commit, rebase, push, pull request, CI, merge, and deployment decisions.
Do not close issue #3960 until all six observations and recovery evidence receive review.
No publication or lab action belongs to the current artifact-only assignment.

## Dependencies & Execution Order

| Task | Prerequisites |
| --- | --- |
| T001 | Separate implementation authorization. |
| T002 | T001. |
| T003 | T002. |
| T004 | T003 and an SSR 7.0.x lab router. |
| T005 | T004. Reuse the verified release and port context. |
| T006 | T005. |
| T007 | T003 and the required later release with a fiber port. |
| T008 | T004, T005, T006, and T007. |
| T009 | T003 and lab console access. |
| T010 | T009. |
| T011 | T003 and a separately approved recovery procedure. |
| T012 | T011. |
| T013 | T012 with accepted recovery evidence. |
| T014 | T008, T010, and T013. |
| T015 | T014. |
| T016 | T015. |
| T017 | T016 and publication authorization. |

US1, US2, and US3 are independently reviewable after the shared foundation.
The same operator may serialize all lab work.
Serialize T008, T010, and T013 because they modify the same runbook.

## Parallel Execution Examples

**US1**: No automatic parallel marker. SSR 7.0.x commands share one router and port context.
OBS-04 may use a separate lab router only after its own preflight.

**US2**: A separate reviewer may inspect `obs-05.md` while US1 evidence receives review.
Runbook edits still require one writer.

**US3**: Never parallelize cloud blocking with other tests on the affected router.
An offline reviewer may inspect accepted US1 or US2 evidence without changing the runbook.

No task carries `[P]` because target allocation and concurrent lab access are not confirmed.

## Implementation Strategy

Deliver US1 as the first independently useful evidence set.
Then deliver US2 and US3 under their own acceptance conditions.
Publish one reviewed change only after the six-observation record is complete.
If lab access remains absent, preserve `Not run` and the blocker instead of reducing scope.

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| FR-001 | T003, T014 |
| FR-002 | T004, T008 |
| FR-003 | T005, T008 |
| FR-004 | T006, T008 |
| FR-005 | T007, T008 |
| FR-006 | T009, T010 |
| FR-007 | T011, T012, T013 |
| FR-008 | T003, T014 |
| FR-009 | T003, T014 |
| FR-010 | T008, T010, T013, T014 |
| FR-011 | T001, T002 and the current assignment boundary |
| FR-012 | T001, T015, T016, T017 |

SC-001 is the current six-observation and unchecked-task review.
SC-002 maps to T003 and T014.
SC-003 maps to T014.
SC-004 maps to T011 and T012.
SC-005 maps to T016 and T017.
