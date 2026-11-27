# Feature Specification: Ops platform dateutil pin (issue #4908)

**Feature Branch**: `fix/4908-ops-platform-dateutil-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Quality gate `ops_platform_pytest` failed for PR #4890. The PR bumps python-dateutil from 2.9.0.post0 to 4.0.0.

## Failure Evidence

- **Check**: `pytest (ops platform)`, job `ops_platform_pytest`, workflow Quality Gates.
- **Run**: 45064318582, attempt 1, event `pull_request`, conclusion `failure`. Job ID 137336951691.
- **Failed step**: `Install dependencies`, step 4. The step runs `pip install -r requirements.txt -e ".[dev]" -r requirements-dev.txt`.
- **Failing rule**: pip must resolve every pin. The resolver stops with `ResolutionImpossible`.
- **Failing test**: None. No test ran, because the install step stopped the job first.
- **Conflict**: `mist-ops-platform/requirements.txt` line 157 requests `python-dateutil==4.0.0`. The run log states that `celery 5.7.0 depends on python-dateutil==2.9.0.post0`.
- **Commit**: Issue #4908 cites merge commit `e30d4a95`. That commit merges PR head `4be9d2e7` into `main` at `00d9a16e`. The run head SHA is `4be9d2e7`.

## Terms

- **Ops pin**: The `python-dateutil` line in `mist-ops-platform/requirements.txt`.
- **Celery pin**: The `python-dateutil` requirement that celery 5.7.0 declares.
- **Dependabot rule**: The `ignore` entry for `python-dateutil` in `.github/dependabot.yml`.
- **Guard**: The test module `tests/guardrails/test_dependency_declaration_parity.py`.

## Clarifications

### Session 2026-11-26

- **Q**: Should this fix upgrade celery so python-dateutil 4.x installs? **A**: No. The newest celery release, v5.7.0, pins python-dateutil to 2.9.0.post0. No later release exists.
- **Q**: Should the ops pin accept python-dateutil 4.0.0? **A**: No. The ops pin keeps 2.9.0.post0 (FR-002, decision D-1).
- **Q**: Should the agent close or merge PR #4890? **A**: No. Repository rules forbid closing update pull requests. A maintainer decides (decision D-4).
- **Q**: Does a test assertion cause the failure? **A**: No. The failure happens before any test runs. The rule is pip dependency resolution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The ops platform install resolves (Priority: P1)

The `pytest (ops platform)` check installs the ops platform requirements. Every pin in the requirements file must resolve together.

**Why this priority**: A failed install blocks every ops platform pull request. It also hides the tests.

**Independent Test**: Run the ops platform gate on the fix pull request. The check `pytest (ops platform)` reports success.

**Acceptance Scenarios**:

1. **Given** the ops pin is `python-dateutil==2.9.0.post0`, **When** the install step runs, **Then** pip resolves `celery==5.7.0` and every other pin.
2. **Given** PR #4890 stays open, **When** the fix merges, **Then** `main` keeps the `pytest (ops platform)` check green.

### User Story 2 - Dependabot stops the conflicting major update (Priority: P2)

Dependabot must not propose a python-dateutil major update for the ops platform requirements.

**Why this priority**: A new proposal repeats the same failed gate each week.

**Independent Test**: Read `.github/dependabot.yml`. The pip entry ignores python-dateutil updates of type `version-update:semver-major`.

**Acceptance Scenarios**:

1. **Given** the pip entry, **When** Dependabot checks python-dateutil, **Then** it skips every 3.x and 4.x release.
2. **Given** the pip entry, **When** Dependabot checks any other package, **Then** that update stays enabled.

### User Story 3 - The guard detects drift (Priority: P3)

The guard fails when the ops pin or the Dependabot rule changes in a way that breaks the install.

**Why this priority**: PR #4890 shows that a future edit can break the install with no signal.

**Independent Test**: Run `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`. Each drift case reports a defect.

**Acceptance Scenarios**:

1. **Given** an ops pin of `python-dateutil==4.0.0`, **When** the guard reads the requirements file, **Then** it reports a defect.
2. **Given** the Dependabot rule is missing, **When** the guard reads the policy, **Then** it reports a defect.

### Edge Cases

- A celery release accepts python-dateutil 4.x. The pin test fails by design. The maintainer removes the Dependabot rule and updates the pin constant in one pull request.
- A python-dateutil 2.x release appears after 2.9.0.post0. The semver-major rule does not cover it. No such release exists (RC-54).
- Dependabot applies the pip entry to a path other than `/`. This is unverified (U-1). The post-merge check in T-MERGE detects it.
- PR #4890 stays red until a maintainer closes it or ignores its update (D-4).
- The root product keeps python-dateutil 4.0.0 (RC-26). Its major updates pause too. Its 4.x patch and minor updates still flow.
- A security advisory affects python-dateutil 2.9.0.post0. The CI audit scans root requirements only (RC-09). A separate issue must cover that advisory.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The install step of job `ops_platform_pytest` MUST resolve every pin in `mist-ops-platform/requirements.txt`.
- **FR-002**: The ops pin MUST keep `python-dateutil` at `2.9.0.post0` while the celery pin stays at `5.7.0`.
- **FR-003**: The pip entry in `.github/dependabot.yml` MUST ignore `python-dateutil` updates of type `version-update:semver-major`.
- **FR-004**: The pip entry MUST NOT ignore any other dependency. It MUST NOT ignore every update of python-dateutil.
- **FR-005**: The guard MUST fail when the ops pin differs from the value `2.9.0.post0`.
- **FR-006**: The guard MUST fail when the Dependabot rule is missing, or when it covers only minor updates.
- **FR-007**: The guard MUST fail when the pip entry is missing.
- **FR-008**: The root requirements files MUST keep `python-dateutil==4.0.0` unchanged.
- **FR-009**: `documentation/quality-gates.md` MUST state the ops pin, the reason for it, and the condition for removing it.
- **FR-010**: The change MUST add one changelog fragment for issue #4908.
- **FR-011**: The record MUST name the failing check, job, step, rule, run ID, and job ID.

### Measurable Outcomes

- **SC-001**: The check `pytest (ops platform)` reports success on the fix pull request.
- **SC-002**: All 9 new guard cases succeed on the fix branch.
- **SC-003**: The diff changes only the files in the change map of `plan.md`. No new file appears under `tests/guardrails/`.
- **SC-004**: The first Dependabot pip run after the merge opens no python-dateutil major update.
- **SC-005**: Each applicable local gate in `tasks.md` reports its expected result.

### Key Entities

Not applicable: this change creates no data entity. `design/data-model.md` records the reason.

## Assumptions

- The CI runner uses Python 3.15, as set in `.github/workflows/ci.yml` line 77 (RC-04).
- Dependabot applies the pip entry to `mist-ops-platform/requirements.txt`, as PR #4890 suggests. This is unverified (U-1).
- The celery pin stays at `2.9.0.post0` until a released celery version relaxes it.
- Maintainers handle PR #4890. This change does not touch PR #4890 or its branch.

## Out of Scope

- Upgrading celery, or changing the ops platform requirements beyond the ops pin.
- PR #4889, which bumps deepdiff past its pyproject bound (RC-22). Issue #4907 tracks that failure.
- Adding `mist-ops-platform/requirements.txt` to the pip-audit gate. Analysis item F-3 records the gap.
- Container build, image revision check, and deployment (decision D-7).
