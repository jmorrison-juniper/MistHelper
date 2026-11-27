# Feature Specification: Remediate the five-child debt of three folders

**Issue**: #4944, `Chore: remediate the five-child debt of scripts/, tests/unit/scripts/, and documentation/noc-runbooks/`

**Status**: Draft

**Main commit checked**: f03c6c9b36d612a48d7b9652998c2fd87dd777ca (`main`, 2026-11-26T07:15:01Z)

**Input**: Reduce each debt folder to five tracked children or fewer. Add a guard that blocks growth. Move one move group in each pull request.

## Clarifications

### Session 2026-11-26

- Q: Which counts form the baseline? A: The main counts are `scripts/` 53, `tests/unit/scripts/` 10, and `documentation/noc-runbooks/` 17. The issue states 52, 10, and 16. Commit f03c6c9b (PR #4941) added one child to each of the three folders. Before that commit, the folders held 52, 9, and 16 children. The issue's count for `tests/unit/scripts/` was never correct.
- Q: What does "keep one index file" mean? A: Keep `documentation/noc-runbooks/SSR_ALARM_INDEX.md` at the top level. It is the only index file in that folder.
- Q: Do documented entry points move? A: No. `scripts/compose.ps1` stays at the top level, because operator documents name it. Every other moved command updates its documents in the same pull request.
- Q: Which pull request closes the issue? A: Only the final pull request uses `Closes #4944`. Earlier pull requests use `Refs #4944`.
- Q: Do historical records change? A: No. The `specs/` and `changelog.d/` trees, `CHANGELOG.md`, and three named historical files keep their text.
- Q: Does a move change behavior? A: No. Each move changes paths only. Module logic, output, and menu behavior stay the same.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop the debt from growing (Priority: P1)

A maintainer adds a child to a debt folder. The guard fails and names the folder.

**Why this priority**: Growth during the remediation undoes the work of each move group.

**Independent Test**: The guard test adds one tracked child to a temporary copy of the count and expects a failure.

**Acceptance Scenarios**:

1. **Given** main at commit f03c6c9b, **When** the guard runs, **Then** it prints three counts and passes.
2. **Given** a debt folder with one child above its baseline, **When** the guard runs, **Then** it fails and names the folder.

### User Story 2 - Find each tool by its purpose (Priority: P1)

A developer opens `scripts/` and sees five entries. Four entries are category folders. One entry is `compose.ps1`.

**Why this priority**: The issue asks for purpose groups. The top level must stay under the limit.

**Independent Test**: List the top level of `scripts/` after the final pull request. Five entries appear.

**Acceptance Scenarios**:

1. **Given** the final pull request is merged, **When** a developer lists `scripts/`, **Then** five entries appear.
2. **Given** a tool in a category folder, **When** a developer compiles its file at the new path, **Then** the compile succeeds.

### User Story 3 - Find each test beside its tool (Priority: P2)

A developer finds the test for a tool in the mirrored category folder under `tests/unit/scripts/`.

**Independent Test**: Run pytest on the mirrored folders. Every test in them passes.

### User Story 4 - Find each runbook by platform (Priority: P2)

An NOC engineer opens `documentation/noc-runbooks/gateway/` for a gateway alarm. The index stays at the top level.

**Independent Test**: Follow each runbook link from the index and from each runbook. Every link opens an existing file.

**Acceptance Scenarios**:

1. **Given** a platform runbook, **When** an engineer follows a link, **Then** the linked file exists.

### User Story 5 - Keep every command and path working (Priority: P1)

A developer runs each documented command. Each command reaches its moved file. Each repository-root path resolves to the repository.

**Independent Test**: Run the path-depth test, the affected test folders, and the old-path sweep.

**Acceptance Scenarios**:

1. **Given** a moved module, **When** the path-depth test runs, **Then** its repository-root expression names the new depth.
2. **Given** the final pull request, **When** the old-path sweep runs, **Then** it prints no line outside the historical files.

### Edge Cases

- A moved module keeps its old root depth. The path-depth test fails.
- A runbook link names a file in another folder. The markdown link test fails.
- Two moved test modules share a basename. Pytest reports an import mismatch. Main has no duplicate basename today.
- Issue #4934 or another pull request adds a child first. The guard fails. The author rebases and records the new count in the same pull request.
- A generated page keeps old command text. The drift check fails until the tool regenerates the page.
- A local-only folder or `__pycache__` exists in the working tree. The guard counts tracked children only.
- A developer stages an unrelated local file. Each pull request stages files by explicit path only.

### Out of Scope

- Changes to module logic, menu behavior, output formats, or data files.
- Splitting `MistHelper.py` or any `src/` package.
- Other debt folders, including `src/`, `tests/guardrails/`, and the `tests/` root.
- Editing historical records.
- Mist API endpoint behavior, mistapi calls, container images, and compose settings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each debt folder MUST hold five tracked children or fewer after the final pull request.
- **FR-002**: The guard MUST print the tracked child count of each debt folder.
- **FR-003**: The guard MUST fail when a debt folder count exceeds its baseline.
- **FR-004**: The baseline MUST start at the main counts. Each move group pull request MUST lower its folder baseline to the new count.
- **FR-005**: `scripts/` MUST hold `compose.ps1` and four category folders at its top level.
- **FR-006**: `tests/unit/scripts/` MUST mirror the category folders. `test_script_imports.py` MUST stay at its top level.
- **FR-007**: `documentation/noc-runbooks/` MUST hold `SSR_ALARM_INDEX.md` and four platform folders at its top level.
- **FR-008**: Each move group pull request MUST update every active import, path string, workflow path, and link that names a moved item. The pull request MUST NOT add an alias or a shim.
- **FR-009**: Each moved module MUST compute its repository root at the depth of its new folder. A test MUST check each such module.
- **FR-010**: Each documented command MUST name its new path in the same pull request.
- **FR-011**: Each generated page MUST match the output of its tool. The menu reference drift check MUST pass.
- **FR-012**: No active tracked file MUST name an old path after the final pull request. The historical files in decision D-7 keep their text.
- **FR-013**: Each pull request MUST add one changelog fragment that names issue 4944.
- **FR-014**: Each pull request MUST run the local gates that apply to its changed files and list the results in its body.
- **FR-015**: The final pull request body MUST contain `Closes #4944`. Each earlier pull request body MUST contain `Refs #4944`.

### Mist Cloud Transport Requirements

Not applicable: the change moves files and edits paths. It adds no Mist REST request and no WebSocket transport.

### Key Entities

- **Debt folder**: One of the three folders named in issue 4944. The guard counts its tracked children.
- **Item**: A file or folder that one move moves.
- **Category folder**: A new folder that groups tools by purpose. It holds five children or fewer.
- **Move group**: The items that one pull request moves. The plan defines six move groups.
- **Baseline**: The tracked child count that the guard accepts for one debt folder.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the final pull request, `scripts/` holds 5 tracked children, `tests/unit/scripts/` holds 4, and `documentation/noc-runbooks/` holds 5.
- **SC-002**: The old-path sweep prints no line outside the historical files in decision D-7.
- **SC-003**: The guard test passes on main and fails in its growth case.
- **SC-004**: The path-depth test passes for each of the 24 moved modules.
- **SC-005**: Each pull request passes its applicable local gates and each required remote check.
- **SC-006**: The menu count stays at 308 registered operations, and the menu reference shows no drift.

## Assumptions

- Main stays at commit f03c6c9b until the first pull request merges. The implementer rebases and recounts when main moves.
- Reviewers accept one pull request per move group, as issue 4944 requests.
- Operators accept the new paths for the documented tools in the same release.
- The four local-only folders named in research unverified item U-4 are not repository content.
