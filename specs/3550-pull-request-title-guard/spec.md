# Feature Specification: Pull request title guard

**Feature Branch**: `jmorrison-juniper-pull-request-title-guard`

**Created**: 2026-09-30

**Status**: Specified

**Input**: User description: "Specify the remaining pull request title check for MistHelper issue #3550. Do not implement code."

**Issue**: [MistHelper #3550](https://github.com/jmorrison-juniper/MistHelper/issues/3550)

Two historical squash subjects did not meet the Conventional Commits rule.
The owner already set `squash_merge_commit_title=PR_TITLE`.
Maintainers need a check that identifies invalid pull request titles before a squash merge.
This feature checks titles only. It does not rewrite history or change merge enforcement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct a pull request title (Priority: P1)

A contributor receives a clear result for the exact pull request title.
The contributor corrects an invalid title before the maintainer starts a squash merge.

**Why this priority**: The squash subject uses the pull request title. A clear title result addresses the remaining issue.

**Independent Test**: Check supplied titles directly without network access or credentials. Confirm each decision, exact title representation, and checked count.

**Acceptance Scenarios**:

1. **Given** the title `wip: model prompts`. **When** the guard reads it. **Then** the guard fails. It prints `"wip: model prompts"` and `Checked 1 pull request title`.
2. **Given** the title `fix(web-portal): model prompts`. **When** the guard reads it. **Then** the guard passes. It prints `"fix(web-portal): model prompts"` and `Checked 1 pull request title`.
3. **Given** each of the nine allowed types with a valid description. **When** the guard checks each title. **Then** every title passes.
4. **Given** `fix: model prompts`, `fix!: model prompts`, or `feat(web-portal)!: model prompts`. **When** the guard checks the title. **Then** the title passes.
5. **Given** an unsupported type, uppercase type, empty scope, or blank description. **When** the guard checks the title. **Then** the guard fails and identifies the rule.

---

### User Story 2 - Trust the result and its measurement (Priority: P1)

A maintainer distinguishes a title failure from an input failure.
The result identifies what the guard checked. The result never treats missing input as success.

**Why this priority**: A passing result has no value if the guard did not read a title.

**Independent Test**: Supply missing, unreadable, malformed, and invalid input offline. Compare the result with a readable title result.

**Acceptance Scenarios**:

1. **Given** absent or unreadable input. **When** the guard starts. **Then** the guard fails, names the input problem, and prints `Checked 0 pull request titles`.
2. **Given** malformed input, missing pull request data, or a missing or non-string title. **When** the guard reads it. **Then** the guard fails and prints `Checked 0 pull request titles`.
3. **Given** a readable empty or whitespace-only title string. **When** the guard checks it. **Then** the guard fails and prints its exact escaped representation and `Checked 1 pull request title`.
4. **Given** `fix(web-portal): 修复模型提示`. **When** the guard checks it. **Then** the guard passes and prints `"fix(web-portal): \u4fee\u590d\u6a21\u578b\u63d0\u793a"` and `Checked 1 pull request title`.
5. **Given** a title with a control character. **When** the guard checks it. **Then** the guard fails and escapes the character. The output contains ASCII characters only.

---

### User Story 3 - Keep dependency updates active (Priority: P2)

A maintainer applies the same title rules to contributor and bot pull requests.
Dependabot continues its existing update streams with compliant title prefixes.

**Why this priority**: The title check must not stop normal dependency updates or hide invalid bot titles.

**Independent Test**: Check representative bot titles directly. Compare the update policy before and after the prefix changes.

**Acceptance Scenarios**:

1. **Given** a new pip update. **When** Dependabot supplies the title. **Then** the title uses `chore` instead of `deps` and meets the title rules.
2. **Given** a new npm update in `/ops-portal`. **When** Dependabot supplies the title. **Then** the title uses `chore(ops-portal)` instead of `deps(ops-portal)`.
3. **Given** a new github-actions update. **When** Dependabot supplies the title. **Then** the title keeps `ci` and meets the title rules.
4. **Given** an existing bot title that starts with `deps` or `deps(ops-portal)`. **When** the guard checks it. **Then** the guard fails. A maintainer renames the title and repeats the check.
5. **Given** the prefix changes. **When** a maintainer compares the update policy. **Then** the weekly schedules, groups, ignores, limits, and labels remain unchanged.

---

### User Story 4 - Use a current check without changing enforcement (Priority: P2)

A maintainer receives a new title result after a relevant pull request event.
Part 6 names the check and explains title correction. The owner retains control of required checks.

**Why this priority**: A stale result can mislead a maintainer. New merge requirements need separate owner approval.

**Independent Test**: Verify the declared events and concurrency policy. Review Part 6 and confirm that repository enforcement settings do not change.

**Acceptance Scenarios**:

1. **Given** a pull request that opens, reopens, receives an edit, or receives a new commit. **When** the event occurs. **Then** one title check run starts.
2. **Given** an invalid title. **When** a contributor changes it to a valid title. **Then** a new check reads the changed title and passes.
3. **Given** an older run for the same workflow and head branch. **When** a new run starts. **Then** the new run cancels the older run.
4. **Given** a run for another head branch. **When** a new title check starts. **Then** that other branch run continues.
5. **Given** this feature. **When** a maintainer reviews Part 6. **Then** the text names `Pull request title`. Repository settings and required checks remain unchanged.

### Edge Cases

| Input or condition | Expected result |
| --- | --- |
| Any allowed lowercase type, with valid syntax | Pass with a checked count of 1. |
| No scope, or a scope with at least one non-whitespace character | Pass if the remaining title meets the rules. |
| `fix(): model prompts` or `fix(   ): model prompts` | Fail with a checked count of 1. |
| A missing scope delimiter or parentheses inside a scope | Fail with a checked count of 1. |
| `wip: model prompts`, `deps: update`, or `Fix: model prompts` | Fail with a checked count of 1. |
| `fix:model prompts`, `fix:: model prompts`, or a leading space before the type | Fail with a checked count of 1. |
| `fix: ` or a description with whitespace only | Fail with a checked count of 1. |
| `fix!!: model prompts` or `fix!(web-portal): model prompts` | Fail with a checked count of 1. |
| Unicode description text | Pass if the remaining title meets the rules. Escape non-ASCII characters in output. |
| Quotes, backslashes, or shell punctuation in a description | Treat the characters as data. Use reversible escapes in output. |
| A tab, newline, carriage return, NUL, escape character, DEL, or another control character | Fail with a checked count of 1. Escape the exact title in output. |
| A Unicode line separator or paragraph separator | Fail with a checked count of 1. |
| An empty or whitespace-only title string | Fail with a checked count of 1. |
| Missing input, unreadable input, malformed input, wrong record structure, or a non-string title | Fail with a checked count of 0. Do not invent a title. |
| A draft, bot, or fork pull request | Apply the same title rules. Do not grant a title exemption. |
| A documentation-only change | Run the title check. Do not omit it because of changed paths. |
| An existing invalid Dependabot title | Require a maintainer rename. Keep the update pull request open. |
| A title edit during an older check run | Replace the older run for the same workflow and head branch. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The guard MUST check one exact title from the current pull request input. It MUST NOT trim, rewrite, change case, or substitute a title.
- **FR-002**: The guard MUST allow only `fix`, `feat`, `chore`, `refactor`, `test`, `docs`, `ci`, `style`, and `perf`. Types MUST use lowercase.
- **FR-003**: The title MUST start with an allowed type. It MAY contain one scope in parentheses after the type. It MAY contain one breaking marker `!` immediately before the colon.
- **FR-004**: An included scope MUST contain at least one non-whitespace character. It MUST NOT contain parentheses. An absent scope is valid.
- **FR-005**: The separator MUST be a colon followed by an ASCII space. The description MUST contain at least one non-whitespace character. The description MUST occupy one line. Unicode description text is valid.
- **FR-006**: The guard MUST reject control characters anywhere in the title. It MUST also reject Unicode line separators and paragraph separators.
- **FR-007**: A valid title MUST produce a passing result. An invalid title MUST produce a failing result. The guard MUST NOT report success or a successful skip after an input failure.
- **FR-008**: Readable input MUST contain a `pull_request` record with a string `title` field. Absent, unreadable, or malformed input MUST fail. Missing records, wrong record structures, and missing or non-string titles MUST fail. These failures MUST print `Checked 0 pull request titles`.
- **FR-009**: All guard output MUST contain ASCII characters only. Every decision on a readable title string MUST print a reversible, double-quoted representation of the exact title. It MUST print `Checked 1 pull request title`. This rule applies to passing, failing, empty, and whitespace-only title strings.
- **FR-010**: A failing result MUST identify the failed rule or input problem. A title failure MUST state the accepted form and direct the maintainer to correct the title. An input failure MUST name the unavailable source or capability without printing unrelated input or credentials.
- **FR-011**: Contributor and bot titles MUST use the same rules without exemptions. New pip titles MUST use `chore`. New npm titles in `/ops-portal` MUST use `chore(ops-portal)`. New github-actions titles MUST keep `ci`.
- **FR-012**: The Dependabot change MUST preserve all three update streams and their directories. Weekly schedules, groups, ignores, limits of five open pull requests, and labels MUST remain unchanged. Existing invalid bot titles MUST require a maintainer rename. The policy MUST NOT close update pull requests or disable updates.
- **FR-013**: The check MUST run on pull request events `opened`, `reopened`, `edited`, and `synchronize`. It MUST include draft, bot, fork, and documentation-only pull requests. It MUST NOT add branch-push triggers, schedules, branch filters, or path filters.
- **FR-014**: One supported event MUST start one title check run. Concurrency MUST distinguish the workflow and head branch, with the event reference as the fallback. A new run MUST cancel an older run in the same group outside `main`. Runs for other head branches MUST remain independent. The cancellation rule MUST preserve a `main` run.
- **FR-015**: The title MUST remain data, never an instruction. The check MUST NOT execute title text. It MUST NOT require secrets or write permission. Untrusted pull request code MUST NOT run with trusted permissions.
- **FR-016**: Part 6 of `.github/instructions/git-flow-multi-agent.instructions.md` MUST name the check `Pull request title`. It MUST state the title rules, correction steps, and Dependabot policy.
- **FR-017**: This feature MUST NOT change repository settings, branch protection, or required status checks. A new required title status needs separate owner approval. The documentation MUST state this approval boundary.
- **FR-018**: Direct positive and negative tests MUST run offline without credentials or a workflow service. They MUST cover all nine types, syntax boundaries, Unicode output, checked counts, and input failures. They MUST prove that the guard can fail.
- **FR-019**: Offline policy tests MUST verify the event set, concurrency behavior, read-only permission boundary, and Dependabot preservation rules. They MUST detect an exemption, omitted event, missing cancellation rule, or unrelated bot policy change.

### Key Entities *(include if feature involves data)*

- **Pull request title**: The exact title string for one pull request. The type, optional scope, optional breaking marker, and description determine validity.
- **Pull request input**: The event data that identifies the title, workflow, head branch, and event reference. Missing or unreadable title data prevents a decision.
- **Title result**: A passing or failing decision, a reason, an escaped title when available, and a checked count.
- **Dependency update policy**: The title prefix for each update stream. Existing schedules, groups, ignores, limits, labels, and directories remain part of this policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All nine allowed types pass with valid syntax. Every invalid-title case in this specification fails. Contributor and bot titles produce identical decisions.
- **SC-002**: Every readable title result identifies the exact title through reversible ASCII output and reports a checked count of 1.
- **SC-003**: Every absent, unreadable, malformed, missing-title, or non-string-title case fails and reports a checked count of 0. No such case reports success.
- **SC-004**: A maintainer identifies the failure and corrects a readable invalid title within two minutes. The maintainer uses only the result and Part 6.
- **SC-005**: Each supported event starts exactly one check run. A changed title replaces the older result for its branch. Other branch runs continue.
- **SC-006**: All three dependency update streams retain their existing schedules, groups, ignores, limits, labels, and directories. New titles meet the common title rules.
- **SC-007**: Offline checks reach the expected decision and checked count for 100 percent of the specified cases. No case needs network access or credentials.
- **SC-008**: The feature makes zero changes to repository settings, branch protection, or required checks. The feature changes no file outside its owned scope.

## Assumptions

### Resolved decisions and dependencies

- The owner already set `squash_merge_commit_title=PR_TITLE`. This feature depends on that setting and does not change it.
- The guard checks the complete title, not commit bodies or the historical squash subjects.
- The input supplies one `pull_request` record with a string `title` field. A readable empty string is a title decision, not an input failure.
- The accepted forms are `type: description`, `type(scope): description`, `type!: description`, and `type(scope)!: description`.
- Blank means empty or whitespace-only. Additional spaces within a nonblank description do not invalidate the title.
- A scope has one pair of parentheses. Only the type has a lowercase requirement.
- Control characters mean U+0000 through U+001F and U+007F through U+009F. The guard also rejects U+2028 and U+2029.
- Output uses JSON-style, double-quoted string escapes with ASCII characters only. It preserves quotes, backslashes, whitespace, control characters, and Unicode text without executing them.
- The stable check name is `Pull request title`. This specification does not make the check a merge requirement.
- Existing invalid bot titles need a maintainer rename. New prefix rules do not rename existing pull requests automatically.
- The project constitution governs later planning and implementation. Structural debt does not authorize unrelated changes.

### Owned implementation scope for later steps

Issue #3550 owns only the following implementation paths:

- `.github/workflows/pull-request-title.yml`
- `scripts/pr_title_guard/__init__.py`
- `scripts/pr_title_guard/__main__.py`
- `tests/unit/scripts/test_pr_title_guard.py`
- `tests/guardrails/test_pr_title_workflow.py`
- `.github/dependabot.yml`
- `.github/instructions/git-flow-multi-agent.instructions.md`
- `changelog.d/issue-3550-pull-request-title-guard.md`
- `specs/3550-pull-request-title-guard/**`

Shared `CHANGELOG.md` and other release-note fragments remain out of scope.
The approved Part 6 change is the only instruction-file change allowed during later implementation.
Other agent instruction files remain unchanged.
Other open pull requests own `ci.yml` and `quality-gates.md`. This feature does not change either file.
Runtime, menu, portal, and database code remain out of scope.
Repository settings and required checks remain out of scope.

### Specification step boundary

- Use `SPECIFY_FEATURE_DIRECTORY=specs/3550-pull-request-title-guard` for this step and all later SpecKit steps.
- This step creates only `spec.md`, `checklists/requirements.md`, and the required issue-owned `.spec-context.json`.
- The existing app branch replaces branch creation. This step creates no issue, branch, commit, pull request, or push.
- This step invokes no other agent and implements no code.
- Keep `.specify/feature.json` and agent instruction files unchanged. Record equivalent completion context in this feature directory.
- PowerShell and the local companion command are unavailable. Use the resolved repository template and record companion completion directly.
