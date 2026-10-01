# Implementation Plan: History scope descriptions

**Branch**: `jmorrison-juniper-history-scope-descriptions` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3485-history-scope-descriptions/spec.md`

## Summary

Keep the existing `HistoryScope` unchanged.
Add `HistoryCardDescription` and `HistoryCardScope` in the reserved `history_descriptions.py` module.
Each group contains a note lead, caption lead, and empty statement.
Use the existing scoped capture name or the words "the selected site".
Without a site filter, name the selected organization.
Print those settled values in the history template.
Keep every history reader and query unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing Flask, Jinja, pytest, and Playwright.

**Storage**: No production storage change.
Tests use existing synthetic query inputs, temporary audit files, and process-owned browser stores.

**Testing**: Dedicated unit, real route, and Chromium tests.
Repeat the existing history, organization isolation, attribution, pagination, and authentication contracts.

**Target Platform**: The current macOS worktree and the existing Linux CI scope.

**Project Type**: A Python web application.

**Performance Goals**: Add zero source calls.

**Constraints**: Do not change readers, stores, schemas, primary keys, firmware decisions, dependencies, exclusions, or baselines.

**Scale/Scope**: Three cards on `/history`.
Change the two original production files and the newly reserved semantic view-model module.

## Constitution Check

The repair preserves the entire existing scope class.
The new description record has three fields and one shared subject formatter.
The new card scope has two validated fields and three computed card properties.
Each new property stays below 25 lines and five logical blocks.
Each description group contains three strings.
No wrapper or compatibility alias is necessary.
The two new semantic class names and the route import are intentional symbol additions.

The existing module and `HistoryScope` exceed the five-child structural limit.
The requested dedicated test paths also enter existing directories with more than five children.
The parent authorizes the helper module and dedicated test locations.
Record the existing directory limits rather than restructure unrelated routes or tests.
A separate structural repair can divide the existing history view responsibilities.

The existing scope builder logs before and after its read.
The new properties perform pure text formatting and read no additional source.
Names stay outside logs.
Jinja's existing escaping remains enabled.

The parent explicitly withholds publication.
Complete local implementation, checks, and the commit before requesting a publication grant.
Do not start a container, cloud action, or production deployment.

**Post-design check**: The bounded extraction resolves finding C1 without increasing existing scope members.
Only the history page context wiring changes.
Every other route body and reader remains unchanged.
Pre-existing directory debt remains separate.

## Project Structure

### Documentation (this feature)

```text
specs/3485-history-scope-descriptions/
  spec.md
  plan.md
  tasks.md
  research.md
  data-model.md
  quickstart.md
  contracts/history-scope.md
  checklists/requirements.md
  .spec-context.json
```

### Source Code (repository root)

```text
src/upgrade_portal/app/routes/review.py
src/upgrade_portal/app/history_descriptions.py
src/upgrade_portal/app/assets/templates/review/history.html
tests/unit/upgrade_portal/test_history_card_scope.py
tests/contract/upgrade_portal/test_history_card_scope_routes.py
tests/e2e/upgrade_portal/test_history_card_scope_journey.py
changelog.d/issue-3485-history-scope-descriptions.md
```

**Structure Decision**: Use the dedicated semantic module that the parent authorized after analysis.
Reuse the existing validated scope fields and do not modify a shared fixture.

## Complexity Tracking

| Existing constraint | Reason for the narrow change | Separate remediation |
| --- | --- | --- |
| `review.py` and `HistoryScope` already exceed five children. | The existing class remains unchanged. New models enter a separate bounded module. | Divide unrelated route responsibilities in a separate issue. |
| Existing application and test directories exceed five children. | The parent authorizes one helper module and the three dedicated test modules. | Reorganize directories in a separate issue. |
| The configured branch hook uses raw checkout commands. | The app owns the current branch and worktree. | Retain the app branch and use file-only specification artifacts. |
| The Bash plan script is absent. | `bash .specify/scripts/bash/setup-plan.sh --json` returned code 127. | Use the current checked-in plan and task templates. |
| The companion hook has no installed local entry point. | Only the Git extension files exist in this worktree. | Record each completed phase in the issue-owned `.spec-context.json`. |

Optional automatic commits remain disabled in the checked-in Git extension configuration.
No shared `.specify` file changes.
