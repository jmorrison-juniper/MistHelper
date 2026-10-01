# Tasks: Bounded database discovery

**Input**: Design documents from `specs/3318-bounded-database-discovery/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), and the documents in `design/`.

**Tests**: Controlled regression and resource tests are required.

**Organization**: Tasks use the three independently testable user stories.

## Phase 1: Setup

- [x] T001 Verify the issue claim and all open pull request files before reserving `src/db/__init__.py`. (delivered: plan.md)
- [x] T002 Create the file-only specification and design documents in `specs/3318-bounded-database-discovery/`. (delivered: spec.md, plan.md, design/)
- [x] T003 Validate the specification checklist in `checklists/requirements.md`. (delivered: checklists/requirements.md)

## Phase 2: Foundational

- [x] T004 Add controlled resolver and clock support in `tests/unit/db_discovery/fakes.py`. (delivered: tests/unit/db_discovery/fakes.py)
- [x] T005 Prove the unchanged repeated lookup and blocked caller defects in `tests/unit/db_discovery/test_config.py`. (delivered: tests/unit/db_discovery/test_config.py, controlled red evidence)

## Phase 3: User Story 1 - Limit the discovery wait

**Goal**: Bound each central name lookup and reuse recent failed results.

**Independent Test**: Measure a blocked resolver with a real caller deadline.

- [x] T006 [US1] Add the bounded resolver, cache, and worker classes in `src/db/host_resolver.py`. (delivered: src/db/host_resolver.py)
- [x] T007 [US1] Use the shared resolver for `_hosts_unreachable` in `src/db/__init__.py` and remove `_can_resolve`. (delivered: src/db/__init__.py)
- [x] T008 [US1] Prove the single-name deadline and repeated failed cache results in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)
- [x] T009 [US1] Preserve explicit standalone mode and credential validation in `tests/unit/db_discovery/test_config.py`. (delivered: tests/unit/db_discovery/test_config.py)

## Phase 4: User Story 2 - Detect a later database

**Goal**: Refresh positive and negative results after 30 monotonic seconds.

**Independent Test**: Change a controlled result when the controlled cache clock reaches expiry.

- [x] T010 [US2] Prove positive expiry, negative expiry, changed hostname, and recovery in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)
- [x] T011 [US2] Prove partial-backend behavior and later configuration recovery in `tests/unit/db_discovery/test_config.py`. (delivered: tests/unit/db_discovery/test_config.py)
- [x] T012 [US2] Prove that late completion does not extend a negative period in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)

## Phase 5: User Story 3 - Keep work and readiness distinct

**Goal**: Bound worker resources and retain a separate TCP readiness decision.

**Independent Test**: Count controlled resolver workers and verify numeric socket connection targets.

- [x] T013 [US3] Use cached numeric addresses for `_can_connect` in `src/db/__init__.py`. (delivered: src/db/__init__.py)
- [x] T014 [US3] Prove single-flight, capacity refusal, zero queued jobs, cache limits, and recovery in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)
- [x] T015 [US3] Prove bounded shutdown and complete controlled helper cleanup in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)
- [x] T016 [US3] Prove DNS and TCP distinction, address reuse, IPv6, and TCP budgets in `tests/unit/db_discovery/test_probe.py`. (delivered: tests/unit/db_discovery/test_probe.py)
- [x] T017 [US3] Isolate all new tests from production DNS and service connections in `tests/unit/db_discovery/conftest.py`. (delivered: tests/unit/db_discovery/conftest.py)
- [x] T017a [US3] Share the DNS preflight in `src/db/redis_writer.py` after fresh exact ownership checks. (delivered: src/db/redis_writer.py)
- [x] T017b [US3] Add the shared DNS preflight in `src/upgrade_portal/capture/store.py` without changing client URLs or errors. (delivered: src/upgrade_portal/capture/store.py)
- [x] T017c [US3] Preserve directly coupled test isolation in `tests/unit/test_standalone.py`, `tests/unit/test_redis_writer.py`, and `tests/unit/upgrade_portal/test_store.py`. (delivered: all three named test files)
- [x] T017d [US3] Expose the current owned ArangoDB preflight boundary in `tests/unit/db_discovery/test_config.py`. (delivered: tests/unit/db_discovery/test_config.py)
- [ ] T017e [US3] After the verified position-25 release, migrate only the inherited DNS preflight in `src/db/arango_writer.py`. This implementation prerequisite remains blocked.
- [ ] T017f [US3] Prove the inherited ArangoDB preflight with controlled red, green, deadline, and resource tests before publication.

## Phase 6: Documentation and local delivery

- [x] T018 [P] Document the central discovery contract and writer boundary in `documentation/bounded-database-discovery.md`. (delivered: documentation/bounded-database-discovery.md)
- [x] T019 [P] Add the release note in `changelog.d/issue-3318-bounded-database-discovery.md`. (delivered: changelog.d/issue-3318-bounded-database-discovery.md)
- [x] T020 Run the focused regression suite and changed-method coverage for `src/db/__init__.py` and `src/db/host_resolver.py`. (delivered: 354 passing cases, 194 covered resolver statements, and six fully covered changed call boundaries)
- [x] T021 Run all requested feasible local gates and analyze the specification, plan, tasks, and implementation. (delivered: configured lint, format, 664-file type scope, Bandit, 995-file ratchet, complexity, source score, dead-code, docstrings, and 10-file links)
- [ ] T022 Commit only the reserved files locally with the required coauthor trailer.
- [ ] T023 Stop before any push or pull request until the coordinator grants a fully verified main SHA after position 25.
- [ ] T024 After the grant, rebase and repeat local gates before a protected exact-head squash merge.
- [ ] T025 Test the exact actual merged main SHA locally in this isolated worktree.

## Dependencies & Execution Order

T004 and T005 precede T006 through T017.
The resolver implementation precedes central caller migration.
Each user story has its own controlled behavior tests.
T018 and T019 can proceed independently after the implementation contract is stable.
T020 and T021 precede T022.
T023 blocks T024, and T024 precedes T025.
T017e depends on the coordinator's explicit verified position-25 main-SHA release.
T017f depends on T017e, and both tasks block publication under T024.

## Parallel Opportunities

The configuration, resolver, and probe tests occupy separate files.
The operator document and release note also occupy separate files.
No delegated agent or remote action is necessary for local implementation.

## Implementation Strategy

Prove the existing defect first.
Implement the resolver at one shared boundary.
Complete each user story with controlled tests.
Preserve owned files and existing backend behavior.
Deliver one verified local commit before the remote authorization decision.

## Local evidence and limits

The unchanged central baseline checked two tests and failed both.
Two configuration reads performed four controlled DNS calls.
The blocked caller still waited after 2.610 real seconds.
The unchanged released-preflight baseline checked two more tests and failed both.

The related suite now checks 354 cases without a skip.
The resolver covers all 194 executable statements.
Six changed call boundaries have complete executable-line coverage.
The measured DNS caller returned after 1.011 seconds.
The measured Redis preflight returned after 1.005 seconds.
The still-owned ArangoDB preflight remained blocked after 1.310 seconds.
That last result proves the incomplete implementation prerequisite, not a successful router deadline.

The full test-quality ratchet checked 995 files and reported zero new findings against the unchanged baseline.
The source score gate reported 9.83 against its 9.5 threshold.
The writing heuristic checked 22 files and passed its 80-point threshold.
Its `dictionary_unavailable` result means partial coverage.
No authorized dictionary was copied or created.

The normal dependency audit aborted while its temporary environment ran `ensurepip`.
UV then compiled all runtime dependencies with exact versions and hashes.
The strict audit with `--disable-pip`, `--no-deps`, and `--require-hashes` checked 105 dependencies.
It reported zero known vulnerabilities.
That runtime result does not audit the Git-only development-tool commit.

The first link scan checked zero untracked files and was not accepted as evidence.
After explicit staging, the scan checked all 10 owned Markdown files and found zero broken links.
No baseline, suppression, exclusion, dependency manifest, shared record, or owned ArangoDB writer changed.
