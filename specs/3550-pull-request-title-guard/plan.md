# Implementation Plan: Pull request title guard

**Branch**: `jmorrison-juniper-pull-request-title-guard` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3550-pull-request-title-guard/spec.md`

**Issue**: [MistHelper #3550](https://github.com/jmorrison-juniper/MistHelper/issues/3550)

**Template**: `.specify/templates/plan-template.md`

## Summary

Add one offline checker for the exact pull request title.
Use the Python standard library and one small `PullRequestTitleGuard` class.
Read the title from the JSON file that `GITHUB_EVENT_PATH` names.
Never insert the title into executable workflow source.

Report the check as `Conventional Commits PR title`.
Reject invalid titles from contributors and bots without an exemption.
Print the exact title through ASCII JSON string escapes and report the checked count.
An input failure must fail with a checked count of zero.

Change only two Dependabot prefixes.
Keep all update settings and existing repository enforcement unchanged.
Document the check and title correction in the owned Part 6 section.

### Planning boundary

This step creates planning artifacts only.
It creates no implementation, task list, branch, issue, commit, push, or pull request.
It invokes no other agent and installs no package.
It does not access the main checkout.

Use `SPECIFY_FEATURE_DIRECTORY=specs/3550-pull-request-title-guard` for each SpecKit step.
Keep `.specify/feature.json` and shared agent instructions unchanged.
Use the templates and issue-owned context instead of the unavailable PowerShell and companion commands.
Do not run the shared agent-context update script.
Record the equivalent planning context in this feature's `.spec-context.json`.

### Resolved specification refinements

The planning request supplies two refinements.
The implementation request also specifies concise comments for non-obvious logic.
These refinements do not require a specification edit.

| Subject | Planning decision |
| --- | --- |
| Check name | Use `Conventional Commits PR title` as the exact job and check name. Keep `Pull request title` as the workflow label. |
| Event set | Include `ready_for_review` with `opened`, `edited`, `reopened`, and `synchronize`. |
| Implementation comments | Use concise STE comments for non-obvious logic, as the implementation request directs. |

Part 6 must identify the workflow label and the exact check name.
The current request also confirms Conventional Commits subjects and a metadata-only delivery cycle.

## Technical Context

**Language/Version**: Python 3.13. The existing worktree environment uses Python 3.13.13.

**Primary Dependencies**: Only the Python standard library for the checker. Use `json`, `logging`, `os`, `pathlib`, `re`, and `traceback`. Use the existing pytest and YAML parser for tests. Use the repository's approved `actions/checkout@v7` and `actions/setup-python@v7` references.

**Storage**: Read one UTF-8 event file. Keep the title and result in memory. Write no application data, database record, or runtime file.

**Testing**: Use direct pytest decisions, temporary event files, captured output, and CLI subprocess tests. Add offline contracts for workflow, Dependabot, and Part 6 policy. Use the existing repository test quality config and baseline without changes.

**Target Platform**: A standard GitHub Linux runner with Python 3.13. Direct decisions must also work on supported local Python 3.13 platforms.

**Project Type**: A repository CI checker with a module CLI and a direct class interface.

**Performance Goals**: Check one title per run. Use one compiled full-match pattern with no repeated ambiguous groups. Use a five-minute job timeout. Do not add an arbitrary title-length limit.

**Constraints**: Use at most five class members. Keep each method within 25 lines, five parameters, five logical blocks, and five operations per block. Use ASCII output, real before/after logging, and explanatory inline comments.

**Scale/Scope**: One checker package, one workflow, two test modules, two Dependabot prefix edits, one Part 6 edit, and one release fragment. No runtime, menu, portal, database, container, protection, or required-status change.

All technical decisions are resolved.
The [research record](research.md) contains the decisions and alternatives.

## Constitution Check

*Gate: Check before research. Check again after design.*

### Initial gate

The initial gate passes with the narrow exceptions in Complexity Tracking.
Existing oversized parents do not grant permission for unrestricted additions.
The requested locations need explicit exceptions where they add a child to an oversized parent.

| Principle or constraint | Design obligation | Initial result |
| --- | --- | --- |
| I. Five-Item Rule | Keep the new package at two files and the checker at five members. Keep each test class within five members. Record parent debt separately. | Pass with narrow location exceptions. |
| II. Class-Based Architecture | Put behavior in `PullRequestTitleGuard`. Use no standalone wrapper or compatibility function. | Pass. |
| III. Safety-First | Validate the event shape and title type. Fail on unavailable input. Treat titles as data. Use no interactive or destructive action. | Pass. |
| IV. Full Deployment Pipeline | Preserve the parent's later local checks, one commit/push, template PR, required checks, CodeQL, squash merge, and exact merged-tree verification. | Pass with the metadata-only delivery exception. |
| V. Observability & Logging | Use standard-library structured logging. Escape every variable output. Print no event payload or credentials. | Pass. |
| VI. Inline Comments | Explain non-obvious logic with concise STE comments under the implementation request. Preserve existing Dependabot comments. | Confirmed task scope. |
| VII. Action Logging | Log before event reading and title decisions. Log after each action with status and count. Log sanitized exception stacks. | Required implementation gate. |
| Python and file paths | Use Python 3.13 and `pathlib.Path`. Open the event with explicit UTF-8 decoding. | Pass. |
| API, export, and database rules | Add no Mist API call, export, operational store, or database key. CI process output is not a collected-data export. | Not applicable. |
| Release notes | Add only `changelog.d/issue-3550-pull-request-title-guard.md` during implementation. Do not edit `CHANGELOG.md`. | Pass with the fragment-location exception. |
| Instruction precedence | Use Conventional Commits instead of the older timestamp subject. Apply the current git-flow instruction and the owner's explicit decision. | Pass with the recorded policy reconciliation. |

### Existing parent debt

Counts describe tracked direct children before planning.
The issue directory already exists as untracked specification work.
Do not change these parents as a cleanup during issue #3550.

| Existing parent | Tracked children | Feature effect | Separate incremental remediation |
| --- | ---: | --- | --- |
| Repository root | 48 | No direct addition. | Propose one legacy file-family move with all callers updated. |
| `.github` | 15 | No direct addition. | Group movable tooling configuration under separate ownership. Preserve GitHub discovery locations. |
| `scripts` | 48 | Add the requested nested package. The parent reaches 49. | Move one existing script family into a compliant package in a separate change. |
| `tests` | 38 | No direct addition. | Group one existing test family in a separate change. Preserve collection and isolation. |
| `tests/unit` | 148 | No direct addition. Use its existing `scripts` directory. | Move one existing test family under a compliant nested directory. |
| `tests/guardrails` | 36 | Add one owned contract test. The parent reaches 37. | Group related guardrails after separate ownership approval. |
| `.github/workflows` | 11 | Add one discoverable workflow. The parent reaches 12. | Review obsolete workflows separately. Never nest active workflow files. |
| `changelog.d` | 26 | Add one unique release fragment. The parent reaches 27. | Let the release coordinator archive consumed fragments. Preserve active fragments. |
| `specs` | 733 | Use the issue directory that the specification step already created. | Review completed feature records under separate archive ownership. |

`tests/unit/scripts` currently has four tracked children.
Its owned test becomes the fifth child.
The new checker package has two files and no extra helper module.
The contracts directory has two files.

### Post-design gate

The post-design gate passes with the same narrow exceptions.
All six design artifacts exist and use the resolved scope.
The plan contains every required template section, and all local artifact links resolve.
The STE checks pass at 97 or 98 against the threshold of 80.
Dictionary grading is unavailable, so the STE result records that coverage limit.
No unresolved design question remains.
The later implementation must prove method limits, logging, and test quality.
Planning evidence does not replace executable test evidence.

### Post-implementation analysis

The required analysis covers all 26 implementation-related requirements.
It found no functional coverage gap.
It identified eight operations in the original event-reader block.
The reader now separates file reading and JSON decoding through a file context.
All four methods meet the structural limits.

An offline probe also found that an exact workflow snapshot blocked normal Actions updates.
The policy tests now accept newer major versions of the two approved actions.
They still reject downgrades, different action names, and changes to the execution boundary.
The combined local run reports 853 passing tests and no skips.
The repository test quality ratchet reports zero new findings.

The analysis also identified existing constitution conflicts with this task's bounded scope.
The coordinator confirmed the scope after the analysis.
Keep the documented location exceptions, concise intent comments, Conventional Commits, and metadata-only delivery.
Do not change the constitution, production deployment, branch protection, or required checks.
These decisions do not authorize a general exception for another feature.

## Project Structure

### Documentation for this feature

```text
specs/3550-pull-request-title-guard/
  spec.md
  .spec-context.json
  checklists/requirements.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
    title-check.md
    workflow-policy.md
```

This step does not create `tasks.md`.
The later `/speckit.tasks` step owns that artifact.

### Source code and related files

```text
scripts/pr_title_guard/
  __init__.py
  __main__.py
tests/unit/scripts/
  test_pr_title_guard.py
tests/guardrails/
  test_pr_title_workflow.py
.github/workflows/
  pull-request-title.yml
.github/
  dependabot.yml
  instructions/git-flow-multi-agent.instructions.md
changelog.d/
  issue-3550-pull-request-title-guard.md
```

**Structure Decision**: Use the exact issue-owned locations.
The package contains the class and its module entry point.
The entry point calls the class directly and exits with its result.
It adds no wrapper function and imports no application runtime module.

### Class and validation design

`PullRequestTitleGuard` owns one compiled pattern and four methods.
It needs no custom constructor, result class, or stored logger.

| Member | Responsibility |
| --- | --- |
| Compiled pattern | Match the complete grammar and reject forbidden characters. |
| `is_valid_title` | Return an exact Boolean decision without changing the supplied value. Log the decision before and after. |
| `read_title` | Read `GITHUB_EVENT_PATH` and return one exact string. Reject file, decoding, JSON, and payload failures. |
| `check` | Print the escaped title, decision, correction guidance when needed, and checked count of one. Return exit code zero or one. |
| `main` | Configure structured ASCII logging, call the reader and checker, and report input failures with count zero. |

Use no actor, author, draft, or changed-file condition.
Use `json.dumps` with `ensure_ascii=True` for the title representation.
Do not trim, normalize, truncate, or add a length policy.
Preserve large valid descriptions and reject large invalid descriptions through the same rule.

The [title contract](contracts/title-check.md) defines exact output and failure categories.
The [workflow contract](contracts/workflow-policy.md) defines workflow and bot policy.

### Test design

Use four small classes in `tests/unit/scripts/test_pr_title_guard.py`.
Separate grammar decisions, printed results, event input, and CLI behavior.
Keep each class within five members.
Use parameterized cases instead of long methods or large classes.

Use three small classes in `tests/guardrails/test_pr_title_workflow.py`.
Separate workflow settings, Dependabot policy, and Part 6 text.
Use the existing YAML parser without a successful missing-dependency skip.
Account for the parser's Boolean representation of an unquoted `on` key.

Assert exact Boolean results, exact stdout, exit codes, and counts.
Verify logging order and escaped variable fields.
Mock only unavailable file capabilities where a real temporary file cannot prove the failure reliably.
Do not mock the guard's decisions or accepted pattern.

Use semantic Part 6 contracts without a hash of unrelated instruction text.
During implementation, use git to prove that text outside Part 6 remains unchanged.
Record this one-time proof in the feature-owned context.
Do not turn that proof into a permanent restriction on future changes to another Part.

The test quality ratchet must receive `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.
Before the commit, scan explicit test roots so untracked tests receive a measurement.
Do not change a baseline, rule, exclusion, or suppression to make the feature pass.
Do not edit `.github/workflows/ci.yml` or `documentation/quality-gates.md`.

### Later delivery boundary

The parent owns the later full cycle.
Use the existing app-managed branch and the explicit owned-file manifest.
Use one Conventional Commits commit and one push after local validation.
Complete the repository PR template and include `Closes #3550`.
Wait for all required checks, including CodeQL, before a coordinated squash merge.

Verify the exact merged commit locally in an isolated workspace.
Do not call a check of the old feature tip merged-tree verification.
Do not access the main checkout.
No production container build, deployment, or health check is needed for this metadata-only guard.

The owner reports strict protection and existing required checks that include CodeQL.
The owner also reports `squash_merge_commit_title=PR_TITLE` and 19 open PRs without owned-path overlaps.
These are supplied planning facts, not a fresh remote audit.
Do not change protection, required statuses, or the squash-title setting.
Making the new title check required needs separate owner approval.

## Complexity Tracking

These exceptions apply only to the named issue-owned locations and delivery behavior.
They do not exempt the checker or test classes from structural limits.
They do not authorize unrelated restructuring.

| Violation or reconciliation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| New package under oversized `scripts` | The owner requires `python -m scripts.pr_title_guard` and owns that package. | A different parent changes the agreed invocation. Moving unrelated scripts exceeds ownership. |
| New test under oversized `tests/guardrails` | The owned contract test must participate in established guardrail collection. | Another path changes the approved manifest. Restructuring existing tests exceeds this issue. |
| Workflow under oversized `.github/workflows` | GitHub discovers new workflows directly in this directory. This is a narrow tooling exception. | A nested workflow file does not provide the required discovered check. |
| Fragment under oversized `changelog.d` | The release policy requires a unique issue-owned fragment. | A shared changelog edit creates overlap. Archiving other fragments belongs to the release coordinator. |
| Eight entries in the issue directory | SpecKit requires the named sibling artifacts and owned context. This is a narrow tooling-layout exception. | Moving the requested artifacts changes the resolved feature paths and breaks the standard layout. |
| Conventional Commits instead of timestamp subjects | The current git-flow instruction and #3550 require Conventional Commits. | The older timestamp subject fails the title rule and conflicts with the current owner decision. |
| No production container deployment | This feature checks CI metadata and changes no running application behavior. | A deployment adds unrelated production risk and proves no title-check behavior. The later PR and merged-tree checks remain required. |

There is no planning blocker.
The unavailable native commands have an authorized issue-owned equivalent.
Stop after the planning artifacts and context pass validation.
