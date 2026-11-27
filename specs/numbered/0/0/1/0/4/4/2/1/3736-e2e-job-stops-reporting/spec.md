# Feature Specification: E2E stall diagnostics

**Issue**: #3736, "CI: E2E job stops reporting results before its 15-minute limit"
**Feature Branch**: `fix/3736-e2e-stall-diagnostics` (planned)
**Record**: `specs/numbered/0/0/1/0/4/4/2/1/3736-e2e-job-stops-reporting`
**Created**: 2026-11-26
**Status**: Draft
**Input**: Read-only research of the failing run 37073211456 and of the current `main` branch. The evidence appears in `design/research.md`.

## Terms

These terms have one meaning in this record.

- **Job limit**: The `timeout-minutes` value of a job. Each shard has a job limit of 20 minutes.
- **Per-test budget**: The pytest-timeout value for one E2E item. The value is 120 seconds.
- **Shard**: One matrix row of the `playwright_shards` job.
- **Phase trail**: The file `test-artifacts/e2e-phase-trail.jsonl`.
- **Stack dump**: Text that the `faulthandler` module writes to `test-artifacts/e2e-stack-dumps.txt`.
- **Watch**: The per-item `faulthandler` timer that writes a stack dump.
- **Silent interval**: The time from the last recorded line to the job cancellation.
- **Stall**: A silent interval longer than the per-test budget, with no recorded outcome.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A stalled case leaves stack evidence (Priority: P1)

A CI maintainer opens the diagnostics artifact of a stalled shard. The artifact shows the blocked frames of each thread.

**Why this priority**: The issue cannot advance without the blocked operation. The failing run recorded no evidence during a silent interval of 427 seconds.

**Independent Test**: A synthetic E2E item that runs longer than the watch threshold writes a stack dump. A synthetic item that finishes earlier writes no dump text.

**Acceptance Scenarios**:

1. **Given** an item runs past the threshold, **When** the job runs, **Then** the dump file holds a `Timeout (` line and each thread's stack.
2. **Given** an item finishes before the threshold, **When** the job runs, **Then** the dump file holds no text for that item.

### User Story 2 - The boundary of a stop is recorded (Priority: P1)

A CI maintainer finds the item that was open when the job stopped. The phase trail names the item without a console log.

**Why this priority**: Pytest writes the item name only when the item starts. A missing line does not prove where the stop occurred.

**Independent Test**: A synthetic run writes one `protocol_start` record and one `protocol_end` record for each item, in order.

**Acceptance Scenarios**:

1. **Given** two synthetic items, **When** the run completes, **Then** the trail holds the boundary and phase records of each item in order.
2. **Given** a cancelled run with one open item, **When** the trail is read, **Then** the stalled-item rule names that item.

### User Story 3 - Cancellation reports its cause (Priority: P2)

A reviewer reads a cancelled shard and sees whether the job limit or a concurrency cancel stopped it.

**Why this priority**: Run 44962483189 reported a concurrency cancel with the text of the 20-minute limit.

**Independent Test**: A guard test reads the cancel message of the workflow and checks that it names both causes.

**Acceptance Scenarios**:

1. **Given** a cancelled shard, **When** the reviewer reads the annotation, **Then** the message names the job limit, the concurrency cancel, and the diagnostics artifact.

### User Story 4 - Budgets are documented accurately (Priority: P3)

A maintainer reads the quality-gate document and finds the current job limits and the effective per-test budget.

**Why this priority**: The issue title and the document describe a 15-minute limit. The CLI value of 180 seconds does not apply to E2E items.

**Independent Test**: Each budget value in `documentation/quality-gates.md` matches `.github/workflows/ci.yml` and `tests/e2e/conftest.py`.

## Edge Cases

- An item runs longer than the threshold and then passes: the dump holds text, and the outcome does not change.
- If the threshold variable is not a positive number below 120, the session stops before the first item. The error names the variable.
- The diagnostic file cannot open: the session stops before the first item, and the error names the path.
- If the job is cancelled during the session teardown of the last item, that item has a `protocol_start` record and no `protocol_end` record. The stalled-item rule names it.
- Pytest collects no E2E item: no watch is armed, and the trail holds no record.
- The job limit stops the job after all tests pass: every item has a `protocol_end` record. The cause is setup or post-test time, not a stall. Run 42084190844 shows this case.
- The pytest-timeout plugin is missing: the existing guard skips the E2E items, and no watch runs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The E2E harness MUST arm one watch for each E2E item before the first phase of that item starts.
- **FR-002**: The watch MUST write a stack dump of all threads to `test-artifacts/e2e-stack-dumps.txt` when an item exceeds the threshold.
- **FR-003**: The threshold MUST default to 100 seconds. The variable `MISTHELPER_E2E_STACK_DUMP_SECONDS` MUST override it, with a positive finite value below 120.
- **FR-004**: The watch MUST cancel when the protocol of each item finishes.
- **FR-005**: The phase trail MUST write a `protocol_start` record before the first phase record of each item. It MUST write a `protocol_end` record after the last phase record.
- **FR-006**: The shard diagnostics upload MUST run on failure or cancellation and MUST include the phase trail and the stack dump file.
- **FR-007**: The cancel message MUST name the job limit, the concurrency cancel, and the diagnostics artifact.
- **FR-008**: A guard test MUST read the workflow and fail when the diagnostics path, the upload condition, or the cancel message changes.
- **FR-009**: The change MUST keep `E2E_TIMEOUT_SECONDS = 120`, `--timeout=180`, the 20-minute shard limit, the 5-minute aggregator limit, and the 30-minute journeys limit.
- **FR-010**: The change MUST NOT modify a file under `src/`, `web_portal/`, or `container/`, and MUST NOT modify `Containerfile` or `compose.yml`.
- **FR-011**: The change MUST add one changelog fragment under `changelog.d/`.
- **FR-012**: The pull request MUST contain `Refs #3736` and MUST NOT contain a closing keyword for #3736.

### Mist Cloud Transport Requirements *(not applicable)*

This change sends no Mist Cloud request. The E2E harness uses its own stand-in services.

### Key Entities *(include if feature involves data)*

- **PhaseRecord**: One line of the phase trail. The fields appear in `design/contracts/e2e-diagnostic-files.md`.
- **ItemLifecycle**: The derived state of one item. The states appear in `design/data-model.md`.
- **StackDump**: The text of one threshold crossing.
- **ShardRow**: One matrix row of `playwright_shards`. The current rows are `upgrade-portal`, `web-portal`, and `websockets-tab`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A synthetic item that runs 1.5 times the threshold leaves a dump with at least one `Timeout (` line.
- **SC-002**: A synthetic item that finishes before the threshold leaves no dump text.
- **SC-003**: The trail holds exactly one `protocol_start` record and one `protocol_end` record for each synthetic item.
- **SC-004**: The workflow guard fails for each of three mutations: a removed diagnostics path, a changed upload condition, and a changed cancel message.
- **SC-005**: After merge, each cancelled shard uploads a diagnostics artifact that names the open item or shows that no item was open.

## Assumptions

- The shards run on `ubuntu-latest`. Source: `.github/workflows/ci.yml`, line 781 on `main`.
- Pytest 9.2.0 and pytest-timeout 2.4.0 stay pinned. Source: `requirements-dev.txt`, line 335 on `main`, and the local `.venv` installation.
- The `faulthandler` watchdog writes a dump while the main thread is blocked. Source: the Python documentation at `https://docs.python.org/3/library/faulthandler.html`, fetched 2026-11-26.

## Out of Scope

- A change to any timeout value, the shard partition, any test selection, or any assertion.
- A repair of the root cause. No blocked operation is identified yet.
- A change to the timeout method or to the pytest-timeout version.
- The session teardown budget of #3517. The budget is already on `main`.
- The WAN evidence upload of open issue #4208.
- Product code, container images, and deployment.
- The backup, firmware, and WAN evidence uploads. Their `!cancelled()` condition belongs to product evidence rules.

## Clarifications

### Session 2026-11-26

- Q: Which per-test budget applies to E2E items? A: 120 seconds. The item marker overrides the CLI value of 180 seconds. Evidence: research rows RC-17, RC-18, and RC-42.
- Q: Which job limit applied to the failing run? A: 15 minutes. Commit `38d06c48` changed the single E2E job to 20 minutes on 2026-10-03. Evidence: research section 4.
- Q: Does the body count of the issue still apply? A: No. The owner correction gives 442 outcomes. The local parse of the log gives the same count. Evidence: research section 3.
- Q: Should the pull request close #3736? A: No. Decision D-7 uses `Refs #3736`.
- Q: Does the stall still occur on `main`? A: The sampled cancelled shards show no silent interval before cancellation. Research section 6 gives the counts.
