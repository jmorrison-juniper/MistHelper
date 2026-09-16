# Feature Specification: Python optimization skill

**Feature Branch**: `docs/2394-python-optimization-skill`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2394 asks for a repository skill for measured Python optimization work.

## User Scenarios and Testing

### User Story 1 - Require measurement first (Priority: P1)

A junior NOC engineer asks an agent to make Python code faster.
The skill makes the agent record a baseline before it changes code.

**Why this priority**: An unmeasured optimization is a guess.

**Independent Test**: Read the skill entry point and confirm that it states the measurement rule first.

**Acceptance Scenarios**:

1. **Given** a Python speed request, **When** the agent opens the skill, **Then** it establishes the workload and baseline first.
2. **Given** no representative input, **When** the agent ranks a change, **Then** it marks the idea as a hypothesis.

---

### User Story 2 - Use MistHelper evidence (Priority: P2)

A maintainer needs performance guidance that fits this repository.
The skill routes the maintainer to repository benchmarks, performance spans, and workflow run evidence.

**Why this priority**: Generic Python advice can miss MistHelper constraints and measured hot paths.

**Independent Test**: Read the benchmark reference and confirm that it names the repository evidence and commands.

**Acceptance Scenarios**:

1. **Given** a performance package claim, **When** the skill states a number, **Then** it names the benchmark command.
2. **Given** a coverage-shard claim, **When** the skill states a duration, **Then** it names the workflow run source.

---

### User Story 3 - Preserve repository rules (Priority: P3)

A contributor finds a faster implementation that increases complexity.
The skill rejects the change when it violates the 5-Item Rule or a quality gate.

**Why this priority**: MistHelper values safe operation and maintainable code over isolated speed.

**Independent Test**: Read the optimization checklist and confirm that speed never overrides house rules.

**Acceptance Scenarios**:

1. **Given** a 60-line function rewrite, **When** the agent applies the skill, **Then** it extracts a small method or rejects the change.
2. **Given** broad `except Exception` logic, **When** the agent measures the path, **Then** it verifies that the handler did not hide the failure.

### Edge Cases

- If another Python optimization skill exists in the repository, improve it instead of adding a duplicate.
- If the user asks for parallelism, route the request out of scope for this skill.
- If a benchmark cannot run, state the blocker and the exact next measurement.
- If a cited value comes from another host, require a local rerun before using it as proof.

## Requirements

### Functional Requirements

- **FR-001**: The repository MUST contain exactly one Python optimization skill.
- **FR-002**: The skill MUST state that an unmeasured optimization is a guess.
- **FR-003**: The skill MUST require before and after numbers for each retained optimization.
- **FR-004**: The skill MUST exclude multiprocessing, threads, asyncio, worker-count changes, distributed work, task sharding, and GPU work.
- **FR-005**: The skill MUST cite MistHelper performance package and coverage-shard evidence with verification commands.
- **FR-006**: The skill MUST mention `scripts/benchmarks/bench_flatten_dict.py`, `delay_metrics.json`, `tuning_data.json`, `--fast`, and `FAST_MODE_MAX_CONCURRENT_CONNECTIONS`.
- **FR-007**: The skill MUST state that speed never permits a 5-Item Rule violation.
- **FR-008**: The skill MUST name Ruff, Black, mypy, Pylint, Radon, Vulture, pydocstyle, interrogate, and coverage gates.
- **FR-009**: The skill MUST warn that broad `except Exception` handlers can hide the slow or failing path.
- **FR-010**: The skill MUST keep all prose in Simplified Technical English.

### Key Entities

- **Skill entry point**: The Markdown file that activates the Python optimization guidance.
- **Reference guide**: A Markdown file that gives a bounded measurement or report workflow.
- **Measurement claim**: A numeric result with its command, source, and environment.
- **Optimization decision**: The retained, rejected, blocked, or hypothesis status for one change.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The repository has one `optimizing-python` skill folder and no duplicate skill for the same concept.
- **SC-002**: The skill contains the measurement-first rule before detailed optimization guidance.
- **SC-003**: Each repository-specific numeric claim has a command or workflow run source.
- **SC-004**: The STE linter scores each written Markdown file at 80 or higher.
- **SC-005**: Local validation gates complete or report a clear blocker.

## Assumptions

- The existing branch work is useful because it already adds the requested five-file skill.
- The correct action is to improve the existing `optimizing-python` skill, not add a second skill.
- The change is documentation-only and needs no live Mist API request.
- The user profile skill does not satisfy the repository requirement, because it is outside version control.
