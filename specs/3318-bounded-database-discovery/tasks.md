# Tasks: Bounded database discovery

**Input**: Design documents from `specs/3318-bounded-database-discovery/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), and the documents in `design/`.

**Tests**: Controlled regression and resource tests are required.

**Organization**: Tasks use the three independently testable user stories.

## Phase 1: Setup

- [x] T001 Verify the issue claim and all open pull request files before reserving `src/foundation/persistence/db/__init__.py`. (delivered: plan.md)
- [x] T002 Create the file-only specification and design documents in `specs/3318-bounded-database-discovery/`. (delivered: spec.md, plan.md, design/)
- [x] T003 Validate the specification checklist in `checklists/requirements.md`. (delivered: checklists/requirements.md)

## Phase 2: Foundational

- [x] T004 Add controlled resolver and clock support in `tests/unit/db_discovery/fakes.py`. (delivered: tests/unit/db_discovery/fakes.py)
- [x] T005 Prove the unchanged repeated lookup and blocked caller defects in `tests/unit/db_discovery/test_config.py`. (delivered: tests/unit/db_discovery/test_config.py, controlled red evidence)

## Phase 3: User Story 1 - Limit the discovery wait

**Goal**: Bound each central name lookup and reuse recent failed results.

**Independent Test**: Measure a blocked resolver with a real caller deadline.

- [x] T006 [US1] Add the bounded resolver, cache, and worker classes in `src/foundation/persistence/db/host_resolver.py`. (delivered: src/foundation/persistence/db/host_resolver.py)
- [x] T007 [US1] Use the shared resolver for `_hosts_unreachable` in `src/foundation/persistence/db/__init__.py` and remove `_can_resolve`. (delivered: src/foundation/persistence/db/__init__.py)
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

- [x] T013 [US3] Use cached numeric addresses for `_can_connect` in `src/foundation/persistence/db/__init__.py`. (delivered: src/foundation/persistence/db/__init__.py)
- [x] T014 [US3] Prove single-flight, capacity refusal, zero queued jobs, cache limits, and recovery in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)
- [x] T015 [US3] Prove bounded shutdown and complete controlled helper cleanup in `tests/unit/db_discovery/test_resolver.py`. (delivered: tests/unit/db_discovery/test_resolver.py)
- [x] T016 [US3] Prove DNS and TCP distinction, address reuse, IPv6, and TCP budgets in `tests/unit/db_discovery/test_probe.py`. (delivered: tests/unit/db_discovery/test_probe.py)
- [x] T017 [US3] Isolate all new tests from production DNS and service connections in `tests/unit/db_discovery/conftest.py`. (delivered: tests/unit/db_discovery/conftest.py)
- [x] T017a [US3] Share the DNS preflight in `src/foundation/persistence/db/redis_writer.py` after fresh exact ownership checks. (delivered: src/foundation/persistence/db/redis_writer.py)
- [x] T017b [US3] Add the shared DNS preflight in `src/interfaces/portals/upgrade_portal/capture/store.py` without changing client URLs or errors. (delivered: src/interfaces/portals/upgrade_portal/capture/store.py)
- [x] T017c [US3] Preserve directly coupled test isolation in `tests/unit/test_standalone.py`, `tests/unit/test_redis_writer.py`, and `tests/unit/upgrade_portal/test_store.py`. (delivered: all three named test files)
- [x] T017d [US3] Expose the current owned ArangoDB preflight boundary in `tests/unit/db_discovery/test_config.py`. (delivered: tests/unit/db_discovery/test_config.py)
- [x] T017e [US3] After the verified position-25 release, migrate only the inherited DNS preflight in `src/foundation/persistence/db/arango_writer.py`. (delivered: the preflight and necessary imports on accepted 67a1ca625ab3526c68a8e54d1580dc1c92d3abc4)
- [x] T017f [US3] Prove the inherited ArangoDB preflight with controlled red, green, deadline, and resource tests before publication. (delivered: tests/unit/db_discovery/test_probe.py, five current red cases, and passing native proofs)

## Phase 6: Documentation and local delivery

- [x] T018 [P] Document the central discovery contract and writer boundary in `documentation/bounded-database-discovery.md`. (delivered: documentation/bounded-database-discovery.md)
- [x] T019 [P] Add the release note in `changelog.d/issue-3318-bounded-database-discovery.md`. (delivered: changelog.d/issue-3318-bounded-database-discovery.md)
- [x] T020 Run the focused regression suite and changed-method coverage for `src/foundation/persistence/db/__init__.py` and `src/foundation/persistence/db/host_resolver.py`. (delivered: 354 passing cases, 194 covered resolver statements, and six fully covered changed call boundaries)
- [x] T021 Run all requested feasible local gates and analyze the specification, plan, tasks, and implementation. (delivered: configured lint, format, 664-file type scope, Bandit, 995-file ratchet, complexity, source score, dead-code, docstrings, and 10-file links)
- [x] T022 Commit only the reserved files locally with the required coauthor trailer. (delivered: original preparation commit 4477312b0c891a59954c07044efc2f4afabf905f, preserved before the authorized local rebase)
- [ ] T023 Stop before any push or pull request until the coordinator issues a separate explicit publication grant.
- [ ] T024 After the publication grant, repeat the required base and local gates before a protected exact-head squash merge.
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

## Preserved preparation evidence and limits

The unchanged central baseline checked two tests and failed both.
Two configuration reads performed four controlled DNS calls.
The blocked caller still waited after 2.610 real seconds.
The unchanged released-preflight baseline checked two more tests and failed both.

The original preparation suite checked 354 cases without a skip.
The resolver covers all 194 executable statements.
Six changed call boundaries have complete executable-line coverage.
The measured DNS caller returned after 1.011 seconds.
The measured Redis preflight returned after 1.005 seconds.
The then-owned ArangoDB preflight remained blocked after 1.310 seconds.
That historical result proved the incomplete implementation prerequisite, not a successful router deadline.

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
The original preparation changed no baseline, suppression, exclusion, dependency manifest, shared record, or then-owned ArangoDB writer.

## Accepted predecessor source proof

The later local source grant releases the inherited ArangoDB preflight on accepted `67a1ca625ab3526c68a8e54d1580dc1c92d3abc4`.
Five controlled tests failed against that exact unchanged preflight.
The blocked native caller still waited after 1.301 real seconds.
The preflight repeated failed and successful lookups instead of using the central cache.

The migrated preflight uses the current shared resolver.
The affected offline suite checked 732 tests and passed without a skip or warning.
It includes the inherited declared-index unit and SDK contract tests.
Native guard refusal reports one checked hostname and prevents client creation.
The numeric TCP probe still uses resolved addresses and its separate budget.
Configured driver URLs, TLS/SNI, credentials, error types, and data behavior remain unchanged.
The local source grant does not authorize a driver handshake deadline or publication.

The required native analyzer preflight reads six inputs and checks all three active guide procedures.
The complete analyzer checks 1,026 discovered files, analyzes 978 files, and reports zero new findings against the unchanged baseline.
Its 48 existing exclusions remain separate from pytest skips.
The native guide and analyzer behavior suite checks 528 cases and passes.
It includes actual refusals for missing inputs, malformed inputs, wrong revisions, dirty selected content, and narrowed gate controls.

The current exact CI type scope checks 668 source files and passes.
The current full Ruff and Black gates pass.
The source score remains 9.83 against 9.5.
The full Bandit scan reports zero findings and zero read errors.
The existing security suppressions remain unchanged.
The complete complexity, dead-code, docstring-style, and docstring-coverage gates pass.
All 10 owned Markdown files have valid links, and all 251 source/test citations resolve.

Seven changed call boundaries cover 89 of 89 executable lines.
The broad affected-package measurement is 89.65 percent.
The final affected-package run meets the current CI 80-percent threshold.
That measurement is not a claim about whole-repository coverage.
The dedicated resolver run meets the unchanged 90-percent threshold.
Native controlled timings include 1.006 seconds for the ArangoDB preflight and 0.000913 seconds for the cached partial-backend refusal.
No full driver or router handshake deadline is claimed.

The normal current audit again aborts during the temporary `ensurepip` invocation on macOS.
The complete current runtime compilation and strict hashed audit report zero known vulnerabilities.
The Git-only development-tool audit limit remains explicit.
The writing heuristic checks all 23 owned paths and passes, with a minimum score of 90.
Its missing authorized dictionary still means partial coverage.

Exact protected-source comparison checks 17 paths and all 44 other ArangoDB writer methods.
Their bytes match the accepted predecessor.
The ArangoDB change contains only the released preflight and necessary imports.
`tests/unit/test_arango_writer.py` and every inherited declared-index fixture remain unchanged.
