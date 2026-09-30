# Research: Pull request title guard

**Issue**: #3550
**Date**: 2026-09-30
**Feature**: [spec.md](spec.md)

The specification and current planning request resolve the scope.
This research uses supplied decisions and local repository evidence.
It invokes no research agent and needs no package installation or remote query.
No clarification remains.

## Decision 1: Use a small standard-library package

**Decision**: Use Python 3.13 and `scripts/pr_title_guard`.
Put behavior in `PullRequestTitleGuard`.
Keep only a compiled pattern and four methods.
Use a direct module entry point without a wrapper function.

**Rationale**: The repository requires Python 3.13 and class-based behavior.
The guard needs no application import or installed runtime dependency.
Its five-member budget can cover reading, decisions, results, and CLI control.

**Alternatives considered**: A reusable external Action adds an unnecessary dependency.
A script in `MistHelper.py` changes runtime scope.
A result class, custom logger class, constructor, or extra helper member adds unnecessary structure.

**Evidence**: `pyproject.toml`, `.specify/memory/constitution.md`, and the approved owned-path manifest.

## Decision 2: Match the complete title without rewriting it

**Decision**: Use one compiled pattern with full-match semantics.
Reject forbidden characters across the complete string.
Allow exactly nine lowercase types.
Allow one nonblank scope without parentheses and one optional breaking marker.
Require a colon, one ASCII separator space, and a nonblank one-line description.

The description can contain additional spaces and Unicode text.
Use Unicode-aware whitespace tests for blank scope and description checks.
Do not trim the value before the decision.
Do not impose a title-length limit that the specification does not define.

**Rationale**: A whole-string decision prevents partial matches and trailing-newline acceptance.
The same rule can reject controls and support Unicode descriptions.
Large-value cases test the algorithm without creating a new product restriction.

**Alternatives considered**: Splitting and normalizing the title can hide invalid whitespace.
ASCII-only descriptions reject an approved case.
A fixed maximum length changes the specification.
A repeated ambiguous pattern creates unnecessary performance risk.

**Evidence**: FR-001 through FR-006, the edge cases, and the resolved assumptions in `spec.md`.

## Decision 3: Read the event file as untrusted data

**Decision**: Read only the file that `GITHUB_EVENT_PATH` names.
Decode it as UTF-8 and parse JSON.
Require an object root, an object `pull_request`, and a string `title`.
Use the exact string without substitution.

**Rationale**: A runner-provided file separates data from executable workflow source.
Shape checks distinguish a missing title from an available invalid title.
The module needs no GitHub API call or credentials.

**Alternatives considered**: A workflow expression in a shell command permits source injection.
A live API lookup adds credentials and network dependence.
A default title or successful skip hides an input failure.

**Evidence**: FR-008, FR-015, and the current request's event-file boundary.

## Decision 4: Fix output, counts, and failure categories

**Decision**: Use `json.dumps(title, ensure_ascii=True)` for the exact title representation.
Print a checked count of one for every available string.
Print a checked count of zero for every input failure.
Return exit code zero only for a valid available title.
Return exit code one for invalid titles and input failures.

Use fixed ASCII reasons for input failures.
Do not print raw event contents, decoder byte excerpts, or unrelated fields.
Use the exact stdout contract in [title-check.md](contracts/title-check.md).

**Rationale**: JSON string escapes preserve Unicode, quotes, backslashes, and controls.
They prevent a title from creating a separate workflow command line.
Counts prove whether the checker reached a title decision.

**Alternatives considered**: Raw title output permits line insertion.
Python `repr` is not the requested double-quoted JSON representation.
Truncation prevents exact-title verification.
A zero exit code after an input failure gives a false passing result.

**Evidence**: FR-007 through FR-010 and the two exact requested examples.

## Decision 5: Use real structured action logging

**Decision**: Use standard-library logging with stable key/value fields.
Configure the CLI to show before and after records.
Send logs to stderr and decision output to stdout.
Log event reading before it starts and after it succeeds or fails.
Log the actual title decision before and after it runs.

Use `%s` argument formatting in logging calls.
Report status and count after each action.
Escape variable stack-frame text through ASCII JSON string encoding.
Retain the exception category and complete stack without printing raw exception data.

**Rationale**: The constitution requires observable actions and ASCII output.
Fixed messages and escaped frame data preserve the diagnostic boundary.
Direct decision tests can verify that logging surrounds the operation.

**Alternatives considered**: Decorative logging before or after the entire CLI does not measure each action.
Raw `logging.exception` output can include unescaped input.
An extra structured-logging dependency is unnecessary for this small module.

**Evidence**: Constitution principles V and VII and the current logging requirement.

## Decision 6: Use one read-only pull request workflow

**Decision**: Use the workflow label `Pull request title`.
Use the exact job and check name `Conventional Commits PR title`.
Declare only `pull_request` with five activity types.
Include `opened`, `edited`, `reopened`, `synchronize`, and `ready_for_review`.

Use the exact concurrency group and cancellation condition in [workflow-policy.md](contracts/workflow-policy.md).
Grant only `contents: read`.
Disable checkout credential persistence.
Set up Python 3.13 and run `python -m scripts.pr_title_guard`.
Use one job with a five-minute timeout.

**Rationale**: Title edits receive a new result.
The workflow reports one decision without privileged execution.
The current request refines the earlier spec's check label and adds `ready_for_review`.

**Alternatives considered**: Push events duplicate PR runs.
Path or branch filters omit relevant pull requests.
`pull_request_target`, secrets, write permissions, or actor exceptions weaken the trust boundary.
A required-status change exceeds this issue.

**Evidence**: FR-013 through FR-017 and git-flow Parts 3, 4, and 6.

## Decision 7: Change only the two invalid bot prefixes

**Decision**: Change pip `deps` to `chore`.
Change npm `deps(ops-portal)` to `chore(ops-portal)`.
Keep the github-actions prefix `ci`.
Preserve every other update field and comment.

**Rationale**: New bot titles can use the common grammar without disabling updates.
Existing invalid bot titles need a maintainer rename.
No bot receives an exemption.

**Alternatives considered**: Allowing `deps` expands the accepted types.
Automatically renaming existing PRs requires a write capability.
Closing bot PRs or disabling streams interrupts dependency maintenance.

**Evidence**: `.github/dependabot.yml`, FR-011, and FR-012.

## Decision 8: Prove behavior locally without changing the ratchet

**Decision**: Add direct parameterized decisions and exact-output assertions.
Use temporary files for input and CLI cases.
Add semantic YAML contracts and a complete baseline snapshot for Dependabot settings.
Restore only the two prefixes before comparing that snapshot.

Use `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.
Scan explicit test roots before the feature commit.
The installed analyzer's `--changed-from` option compares a revision with `HEAD`, so it cannot measure new untracked tests.

**Rationale**: Direct negative tests prove that the guard fails.
Exact decisions and outputs avoid weak or self-mocked assertions.
A full policy comparison detects unrelated Dependabot changes.

**Alternatives considered**: A temporary bad remote commit adds avoidable CI runs.
Loose text searches can miss YAML policy drift.
Changing the baseline, exclusions, or CI workflow hides or expands the issue.

**Evidence**: The two repository ratchet files, the read-only `ci.yml` ratchet command, and installed analyzer help.

## Decision 9: Record structural and delivery exceptions

**Decision**: Keep the approved package, test, workflow, fragment, and SpecKit artifact locations.
Record exact parent debt and separate remediation in [plan.md](plan.md).
Treat required discovery and artifact locations as narrow exceptions.
Keep checker and test class limits unchanged.

Use Conventional Commits under the current git-flow rule and owner decision.
Keep the later PR, required checks, CodeQL, squash merge, and exact merged-tree validation.
Do not deploy production containers for this metadata-only guard.

**Rationale**: Shared cleanup, timestamp subjects, and production deployment do not prove this feature.
The owner restricts the file set and supplies the complete later delivery boundary.

**Alternatives considered**: Moving unrelated children violates ownership.
Using grandfathered debt as unrestricted permission adds structural risk.
Editing shared instructions or protection changes unrelated policy.

**Evidence**: Constitution 1.5.0, git-flow precedence, the owned context, and the current planning request.
