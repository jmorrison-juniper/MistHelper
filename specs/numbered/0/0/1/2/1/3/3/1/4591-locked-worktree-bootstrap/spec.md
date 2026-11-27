# Feature Specification: Locked Worktree Bootstrap

**Feature Branch**: `fix/4591-locked-worktree-bootstrap` (planned, not created)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4591, "bug: locked worktree bootstrap rejects the current dependency metadata". The issue body and seven comments were read on 2026-11-26. Repository head: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main`.

## Clarifications

### Session 2026-11-26

- Q1: Which uv version did the reporter use? Answer: not stated. Comments of 2026-11-07 and 2026-11-11 ask for it. Effect: gate G-1.
- Q2: What full output did the failing run print? Answer: the issue body shows an excerpt only. Comments ask for the full output. Effect: gate G-1.
- Q3: Which index variables were active in the failing run? Answer: not stated. The comment of 2026-11-11 asks for the names without host names, URLs, or tokens. Effect: gate G-1 and FR-004.

**Gate G-1**: No code or test change merges until the reporter posts three items on the issue. The items are the uv version, the full output, and the active index variable names.

## Reproduction Summary

The rejection reproduces from repository and CI evidence. A live run waits for gate G-1. The metadata that uv rejects is the registry source in `uv.lock`. Each registry source names the public index, `https://pypi.org/simple`. The bootstrap gives the configured index to uv through the child environment. A configured index that differs from that registry source fails the locked sync. Details are in `design/research.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the cause of a rejected lock (Priority: P1)

An operator runs the bootstrap in a new worktree. The locked sync stops. The final message names the cause and the active index variable names. The message contains no index URL, host name, or credential.

**Why this priority**: The reporter saw only "The locked UV sync failed with code 1." That text names no cause.

**Independent Test**: In a new worktree, configure an index that differs from the public index. Run the bootstrap. The final message names the index cause and the variable name, and it contains no URL.

**Acceptance Scenarios**:

1. **Given** a configured index that differs from the registry source. **When** the locked sync fails with "needs to be updated". **Then** the message names the index cause and the variable names.
2. **Given** no configured index, **When** the locked sync fails with "needs to be updated", **Then** the final message names lock drift.
3. **Given** a failure without "needs to be updated", **When** the lock check runs, **Then** the final message keeps the original error.

---

### User Story 2 - Use the public index for one run (Priority: P2)

An operator with a configured index runs the bootstrap with `--public-lock-index`. The locked sync uses the public index for that run only. The pip configuration does not change.

**Why this priority**: The option exists since PR #4880. This change must keep the option and test it.

**Independent Test**: Run the bootstrap with `--public-lock-index` in a new worktree. The run completes, or it names a network cause. The pip configuration file keeps its content.

**Acceptance Scenarios**:

1. **Given** a configured index variable, **When** the option is set, **Then** the child environment holds `UV_INDEX_URL` for the public index and no other index variable.
2. **Given** the option is absent and the configured index answers the probe, **When** the bootstrap runs, **Then** the child environment keeps the configured index.

---

### User Story 3 - Keep system certificate trust without the deprecated variable (Priority: P2)

An operator behind TLS inspection runs the bootstrap with uv 0.11.0 or later. The child environment sets `UV_SYSTEM_CERTS=1`. It does not set `UV_NATIVE_TLS`. The run prints no deprecation warning for `UV_NATIVE_TLS`.

**Why this priority**: The reporter log shows the deprecation warning for each run.

**Independent Test**: Build the child environment in a unit test. Check that `UV_NATIVE_TLS` is absent and that `UV_SYSTEM_CERTS` equals `1`.

**Acceptance Scenarios**:

1. **Given** a locked sync, **When** the child environment is built, **Then** `UV_NATIVE_TLS` is absent and `UV_SYSTEM_CERTS` equals `1`.

---

### User Story 4 - Repeat the rejected-metadata finding from repository files (Priority: P3)

A maintainer reads `uv.lock` and the bootstrap, and repeats the finding without running uv. The maintainer counts the registry source lines.

**Why this priority**: The repository owner asked for read-only evidence before a code change.

**Independent Test**: Count the registry source lines in `uv.lock` at blob `5445b4eb382dc9f6dd5c351ba40c521f01f93165`. The count equals 195, and the first line is line 8.

**Acceptance Scenarios**:

1. **Given** `uv.lock` on `main`, **When** the maintainer counts the registry source lines, **Then** the count equals 195 and the first one is line 8.

### Edge Cases

- A configured index that equals the public index after case and trailing-slash normalization gives no index cause. The existing `normalize_index` function handles this case.
- Only `UV_EXTRA_INDEX_URL` is set. The cause rule uses the primary index only, so the message is lock drift. Whether uv rejects the lock in this case is unverified (`design/research.md`, U-05).
- The configured index does not answer the reachability probe. The existing probe uses the public index for the run, so no cause message appears.
- `uv.lock` has no registry source line. The diagnosis returns lock drift, as before.
- Caution: a uv build older than 0.11.0 ignores `UV_SYSTEM_CERTS`. TLS inspection may then block the locked sync.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the rejected metadata with file path, line, and blob SHA.
- **FR-002**: The locked sync MUST run `uv sync --locked --extra dev`. It MUST NOT use a frozen sync as a fallback.
- **FR-003**: The cause message MUST name the index cause when the configured index differs from the registry source. It MUST NOT print an index URL or host name.
- **FR-004**: The cause message and an info log MUST name each active index variable. They MUST NOT print a value.
- **FR-005**: `--public-lock-index` MUST force the public index for the locked sync. The pip configuration MUST NOT change.
- **FR-006**: The child environment MUST NOT set `UV_NATIVE_TLS`. It MUST keep `UV_SYSTEM_CERTS=1`.
- **FR-007**: `documentation/development-setup.md` MUST describe the locked sync, the two cause messages, the option, the uv 0.11.0 minimum, and no `UV_NATIVE_TLS` setting.
- **FR-008**: Each new test for a changed behavior MUST fail on the code before the change.
- **FR-009**: One changelog fragment MUST describe the user-visible message change.
- **FR-010**: The change MUST NOT edit `pyproject.toml`, `uv.lock`, `requirements.txt`, or `requirements-dev.txt`.
- **FR-011**: Gate G-1 MUST clear before a code or test change merges.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: the change calls no Mist Cloud endpoint and no mistapi method.

### Key Entities

- **Registry Source**: A line in `uv.lock` such as `source = { registry = "https://pypi.org/simple" }`. It names the index URL of one registry package. Natural key: package name, version, and index URL.
- **Index Variable**: A child-only environment setting that uv reads. The names are `UV_INDEX_URL`, `UV_DEFAULT_INDEX`, `UV_INDEX`, and `UV_EXTRA_INDEX_URL`.
- **Cause Verdict**: The result of a failed locked sync. The values are index-mismatch, lock-drift, and unknown.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each FR maps to at least one task and at least one test or verification command in `tasks.md`.
- **SC-002**: The job `Dependency lock and exports` in `ci.yml` passes on the pull request.
- **SC-003**: Each new test fails before the change and passes after it. The pull request body records both runs.
- **SC-004**: No test output contains an index URL, a host name, or a credential.
- **SC-005**: A new Windows worktree prints the index cause in one run when the configured index differs from `uv.lock`.

## Assumptions

- **A-001**: The reporter used the bootstrap at commit `c57c9b704` or at main head `5d444bda2`. Both commits hold the same bootstrap blob and the same `uv.lock` blob. See `design/research.md`, rows RC-31 to RC-34.
- **A-002**: The reporter child environment had a configured index. No data confirms this. The local Windows machine that holds this record has a non-public primary index and an extra index in pip configuration. Only booleans were read.
- **A-003**: uv behaves as its source at commit `9bf01bef71c76643290ca17635970076fab1bd0d` describes. The reporter uv version is unknown.
- **A-004**: The public index answers the locked sync when the owner uses `--public-lock-index`. This is unverified for the reporter network.

## Out of Scope

- Changes to `pyproject.toml`, `uv.lock`, `requirements.txt`, or `requirements-dev.txt`.
- A lock regeneration with a configured index.
- An automatic frozen sync fallback.
- A change to the reachability probe or to the public index policy.
- Issue #4774 and the browser download. This record does not close issue #4774.
