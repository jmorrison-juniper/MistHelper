# Research: Stale and Bulk Run Controls

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Date**: 2026-09-11

The specification has no open clarification. This document records the final
design decisions after the SpecKit analysis.

## R0. Branch ownership and overlap

**Decision**: Start implementation only from current `origin/main`.

The branch now points at current `origin/main`. The earlier clean-branch
blocker is closed.

Before a source edit, claim issue #2447 and add `in-progress`. Compare active
worktrees, active branches, and open pull request files with the complete
feature manifest.

Stop implementation when another owner or open pull request overlaps a
feature path.

## R1. Stale threshold and time source

**Decision**: A run becomes stale at 24 hours without a valid `updated_at`.

The service accepts an offset and converts the time to UTC. A missing, invalid,
or future time produces an unknown age.

## R2. Canonical terminal states

**Decision**: The final set is `complete`, `failed`, `stopped`, and
`cancelled`.

Every stale check, stop guard, history view, live-run guard, retry rule,
contract, and test uses `RunStateMachine.TERMINAL`.

The implementation removes `TERMINAL_RUN_STATES` from `runtime/signals.py` and
`FINISHED_RUN_STATES` from `app/routes/review.py`.

## R3. Structural remediation

**Decision**: Grandfather existing tracked hierarchy violations and add no new
debt.

New behavior enters `api/run_controls/` and `persistence/actions/`. Both
parents can accept one child and remain compliant.

The implementation edits existing overfull modules only where integration
requires it. It does not add a child to those parents, and it does not add a
top-level symbol when an existing class can own the change.

Related test files become same-name packages. This replacement keeps the child
count of each existing test parent unchanged.

The plan records broader package extraction as separate incremental
remediation.

## R4. Action persistence

**Decision**: ArangoDB is the only authority for action mutations.

The action record and the related run mutation must commit together. Existing
CSV, SQLite, Redis, memory, and file paths cannot join that transaction.

The portal returns `action_store_unavailable` before any mutation when
ArangoDB is unavailable. It does not claim a fallback success.

This exception applies only to portal-internal transactional state. API data
exports continue to use the required multi-backend facilities.

The deployment procedure creates and verifies a backup. The recovery drill
restores it to an isolated target. The first release retains action records for
the lifetime of their referenced runs.

## R5. Composite domain key

**Decision**: The action domain key is
`(actor_scope, idempotency_key_digest)`.

`actor_scope` comes from the identity kind and normalized durable actor
identity. The browser identifier and signed session key are not part of the
domain key.

The implementation adds the primary-key strategy before it adds action
persistence.

## R6. Action record initialization

**Decision**: The first transaction creates one ordered durable item for every
requested run.

Each item starts as `pending`, `unknown`, and `not_processed`. A
compare-and-swap write claims the item before work.

Successful run mutations finalize the item in the same transaction. Refused,
failed, and unknown results use outcome-only compare-and-swap writes.

The action becomes `complete` only after every item becomes final.

## R7. Replay and resume

**Decision**: A replay can resume only an item with no possible prior mutation.

Replay returns `processing` while the stored lease is current.

After lease expiry, one worker takes ownership with compare-and-swap. It marks
old claimed items `unknown` with reason `processing_interrupted`.

The worker resumes only pending items. It never repeats a claimed or final
item. It preserves a durable site block and finalizes every remaining item.

## R8. Authoritative preview

**Decision**: The server previews the selection before phrase entry.

The preview applies the current organization and history scope. It removes
hidden or inaccessible identifiers and returns exact counts.

The browser replaces its stored selection with the returned list. A signed
preview token binds the action request to that list and those counts.

Reconciliation is not a bulk action. It creates one single-run action with
null preview fields and counts of one.

## R9. Duplicate identifiers

**Decision**: The request rejects duplicate run identifiers.

The service does not normalize duplicates into one identifier. Silent
de-duplication would make the typed count differ from the submitted request.

## R10. Bulk order and site stop rule

**Decision**: The service processes sites by stable site identifier. It
processes each site's items in preview order.

The service rechecks permission and the exact lock token before each mutation.
If either guard fails, it stops later writes for that site.

The failed item receives the guard refusal. Later site items remain `unknown`
with reason `not_processed_after_site_guard_loss`.

## R11. Retry source order

**Decision**: A retry source needs a valid `updated_at`.

The newest source wins by UTC `updated_at`. The run identifier breaks an equal
time tie. A missing, invalid, or future time causes
`retry_source_time_unknown`.

## R12. Retry option copy

**Decision**: The copy policy uses an exact allowlist and the existing
`upgrade.options.build_options` validator.

Unknown fields cause `retry_options_unsupported`. Invalid allowed values cause
`retry_options_invalid`.

Only stored duration fields can create new schedule times. An absolute time
without a valid duration does not copy.

## R13. Reconciliation outcome

**Decision**: A stale `stopping` run can move only to `stopped`.

The evidence must cover every target. It must prove that no target writes
firmware and no live task remains.

Age, a cancel acceptance, a partial response, or a network fault is not proof.

Each target uses the typed `TargetEvidence` record. The complete decision input
uses `ReconciliationEvidence`.

The final item stores a safe canonical `ReconciliationEvidenceSummary`. The
parent action stores its matching digest. A success transaction stores the run
change and both evidence fields together.

## R14. Factory override order

**Decision**: The application factory receives an explicit override object.
It installs the overrides before it registers blueprints.

The normal factory supplies production dependencies. The E2E factory supplies
all record, lock, authorization, cloud, audit, connector, and file stand-ins.

A missing required E2E override fails application construction.

## R15. E2E traps and sentinels

**Decision**: Install ArangoDB, Redis, cloud, and file traps before any browser
process starts.

The child uses loopback port 1 as the explicit unreachable network sentinel.
It removes all production credentials and output paths.

Each server uses a unique port, test run identifier, and artifact directory.
Each response includes `X-MistHelper-E2E-Run-ID` in test mode only.

## R16. Browser execution order

**Decision**: No browser test runs before all isolation controls pass unit and
contract tests.

After installation, the implementation runs the complete
`tests/e2e/upgrade_portal` suite. A targeted browser run cannot replace it.

The implementation records persistent run, action, and audit counts before the
full suite. It compares the same counts immediately after the suite.

## R17. Performance measurements

**Decision**: Use fixed local workloads and a fixed clock.

The history measurement uses 50 fixed records, 10 warm-up calls, and 30 timed
calls. The result reports the median and maximum.

The bulk measurement uses 50 pre-cloud runs, one local actor, one lock token,
no cloud stand-in calls, 5 warm-up calls, and 20 timed calls.

The history maximum must stay below 1 second. The bulk maximum must stay below
5 seconds.

## R18. Quality scope

**Decision**: Use `feature-files.txt` as the explicit feature staging and gate
manifest.

The changed set includes the branch diff from the merge base, staged changes,
unstaged changes, and untracked files.

The 79-path manifest lists all planned paths before the first source edit. The
implementation updates the manifest before it edits an additional path.

The comparison rejects an unlisted feature path. It excludes unrelated
pre-existing worktree paths because only explicit manifest paths belong to the
feature.

The staging command uses the manifest. A final comparison proves that every
changed feature file is staged.

Each Python file receives syntax, Ruff, Black, mypy, pylint, radon, vulture,
pydocstyle, interrogate, and applicable pytest coverage.

Each JavaScript file receives `node --check` and the existing asset and browser
tests. The implementation records the applicable gate for every manifest row.

No workflow edit is planned. The existing quality, auto-merge, and container
workflows already cover this feature. A later workflow edit requires a
manifest update before its first edit.

## R19. Failure ownership

**Decision**: Fix each feature-caused failure in this branch.

If a failure is unrelated, create one GitHub issue before any repair. Do not
repair the unrelated failure in this feature.

A distinct pre-existing defect that this feature exposes also needs its own
issue.

## R20. Deployment

**Decision**: Use the active pull request workflow and existing CI.

Update the README, portal operator guide, and changelog because the controls
change operator instructions. Run local gates, stage every manifest path, and
commit the feature.

Fetch `origin/main` and rebase the committed feature branch. Rerun affected
gates, push the feature branch, and open the pull request with all required
fields.

Use the required title and complete the pull request template. Add the type,
scope, and status labels.

After approval and every check, including CodeQL, passes, add `auto-merge`.
The workflow uses a squash merge to `main`. Wait for the main container
workflow. Verify the image revision equals the merged commit before deployment.

A feature branch push does not build or update `latest`.

## R21. Backup, recovery, and retention

**Decision**: Back up the operational store before schema work or deployment.

Verify the backup before use. Restore it to an isolated target and verify the
run and action collections, indexes, and linked sample records.

Retain each action record for the lifetime of its referenced run records. The
first release adds no automatic action cleanup.

## R22. Optional live verification

**Decision**: The Morrison House SRX action remains optional.

Run it only after the merged image is deployed and all safe checks pass. The
operator must type the separate live phrase before the normal firmware phrase.
