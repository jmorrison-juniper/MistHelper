# Feature Specification: Stale and Bulk Run Controls

**Feature Branch**: `fix/2447-stale-bulk-run-controls`

**Created**: 2026-09-11

**Status**: Ready to implement

**Input**: Follow issue #2447 with stale visibility, safe reconciliation,
safe bulk controls, isolated browser tests, and a safe deployment workflow.

**Base**: The branch starts at current `origin/main`. The prior clean-branch
blocker does not apply.

## Background

The portal permits one run that is not final for each site. This guard
prevents two firmware plans from acting on one site.

The history page does not identify stale runs or support bulk actions. Hidden
browser selections can also outlive the rows that created them.

The local store held 24 runs that were not final. Eight records belonged to
Morrison House Site. Sixteen records came from browser tests.

This feature makes stale records visible and gives operators safe controls.
It does not weaken the one-run guard or stop active firmware work.

## Definitions

- A **final run** has state `complete`, `failed`, `stopped`, or `cancelled`.
- A **pre-cloud run** has not submitted firmware work.
- A **cloud-active run** can hold submitted firmware work.
- A **stale run** is not final and has no stored update for 24 hours.
- A **bulk request** applies one action to 1 through 50 distinct runs.
- An **authoritative preview** is a server result for the visible selection.
- A **bulk action** is a cancel or retry request that uses a preview.
- A **reconciliation action** is a single-run request that uses no bulk
  preview.
- A **refused outcome** means a rule prevented a mutation.
- An **unknown outcome** means the portal cannot prove a mutation result.
- An **unprocessed outcome** is `unknown` with reason `not_processed`.
- A **claimed item** has a durable processing claim. Recovery never repeats
  its possible mutation.

## User Scenarios and Testing

### User Story 1 - Find stale runs quickly (Priority: P1)

An operator opens the history page and sees each last-update age. The history
page and the run page use the same stale decision.

**Independent Test**: Seed fresh, stale, final, malformed, and future records.
Confirm the same age and stale result on both pages.

**Acceptance Scenarios**:

1. **Given** an update 23 hours ago, **When** the page opens, **Then** the run
   shows an age and no stale badge.
2. **Given** an update 24 hours ago, **When** the page opens, **Then** the run
   shows a stale badge.
3. **Given** a final old run, **When** the page opens, **Then** the run shows
   an age and no stale badge.
4. **Given** a missing, invalid, or future time, **When** the page opens,
   **Then** the page shows `unknown` and no stale badge.

### User Story 2 - Reconcile a stale run safely (Priority: P1)

An operator explicitly reconciles a stale pre-cloud run or stale `stopping`
run. The portal rechecks access and records one durable outcome.

**Independent Test**: Reconcile complete, active, conflicting, unavailable,
and changed evidence sets.

**Acceptance Scenarios**:

1. **Given** a stale pre-cloud run, **When** current access checks pass,
   **Then** one transaction changes the run to `cancelled` and records success.
2. **Given** a stale `stopping` run, **When** complete evidence proves no task
   remains, **Then** one transaction changes the run only to `stopped`.
3. **Given** active writing or a live task, **When** reconciliation runs,
   **Then** the run stays `stopping`.
4. **Given** incomplete, conflicting, or unavailable evidence, **When**
   reconciliation runs, **Then** the result is `unknown`.
5. **Given** the same actor and request key again, **When** the request
   returns, **Then** it returns the durable first result without new reads.
6. **Given** a reconciliation request, **When** the portal creates its action
   record, **Then** it uses the single-run source and no bulk preview.

### User Story 3 - Cancel selected pre-cloud runs (Priority: P1)

An operator selects visible runs, requests a server preview, and types one
phrase from the exact preview count.

**Independent Test**: Select eligible and ineligible runs across sites. Change
permission and lock state during the batch.

**Acceptance Scenarios**:

1. **Given** hidden stored identifiers, **When** preview runs, **Then** the
   server removes non-visible identifiers before it returns counts.
2. **Given** eligible runs on two sites, **When** cancel runs, **Then** each
   mutation and its outcome commit together.
3. **Given** access or lock loss before an item, **When** the guard fails,
   **Then** the portal stops later writes for that site.
4. **Given** stopped processing, **When** results return, **Then** each
   unprocessed item is `unknown` with reason `not_processed`.
5. **Given** one site refusal, **When** another site stays valid, **Then** the
   valid site continues.

### User Story 4 - Retry selected unsuccessful runs (Priority: P2)

An operator retries failed, stopped, or cancelled runs. The portal copies only
approved fields and validates them through the current options validator.

**Independent Test**: Use valid, unknown, stale-time, and no-time sources.
Use two sources for one site and concurrent requests.

**Acceptance Scenarios**:

1. **Given** one valid source for each site, **When** retry runs, **Then** one
   new `created` run exists for each site.
2. **Given** two sources for one site, **When** retry runs, **Then** the newest
   source wins by valid `updated_at` and run identifier.
3. **Given** a source with no valid update time, **When** retry runs, **Then**
   the portal refuses it with `retry_source_time_unknown`.
4. **Given** an unknown option field, **When** retry runs, **Then** the portal
   refuses it with `retry_options_unsupported`.
5. **Given** a live run for the site, **When** retry runs, **Then** the portal
   identifies that run and creates no retry.

### User Story 5 - Use bulk controls through browser changes (Priority: P2)

An operator reloads, navigates, renews a session, or uses another tab. The
server remains the authority for preview, identity, and outcomes.

**Independent Test**: Use reload, back, forward, two tabs, session renewal,
response loss, keyboard input, and three viewport widths.

**Acceptance Scenarios**:

1. **Given** a stored tab selection, **When** the page restores it, **Then**
   no action starts.
2. **Given** a restored selection, **When** confirmation opens, **Then** a new
   server preview supplies the exact visible counts.
3. **Given** a renewed session for the same normalized actor, **When** the
   actor reuses a request key, **Then** the first result returns.
4. **Given** another actor, **When** that actor requests the action identifier,
   **Then** the endpoint returns no action information.
5. **Given** response loss, **When** the page recovers, **Then** it reads the
   stored result and never repeats a write.

### User Story 6 - Keep browser tests isolated (Priority: P1)

A maintainer runs browser tests. Factory overrides install every stand-in and
trap before route registration.

**Independent Test**: Run the complete browser suite with unreachable
sentinels and persistent connector traps.

**Acceptance Scenarios**:

1. **Given** ArangoDB, Redis, cloud, and file traps, **When** the application
   starts, **Then** no production connector runs.
2. **Given** production credentials in the parent process, **When** the child
   starts, **Then** the child contains no production credential value.
3. **Given** two browser sessions, **When** both run, **Then** they use unique
   ports, record stores, run identifiers, and artifact directories.
4. **Given** an isolated response, **When** the browser receives it, **Then**
   `X-MistHelper-E2E-Run-ID` matches the expected test run.
5. **Given** all traps, **When** the full E2E suite runs, **Then** persistent
   run, action, and audit counts do not change.

## Edge Cases

- A run crosses the stale limit while the page stays open.
- A request contains zero runs, 51 runs, or a duplicate run identifier.
- A hidden selection names another organization or an absent row.
- A source changes after preview.
- Access or lock ownership changes before any item mutation.
- A lock token changes between two items of one site.
- An action process stops after some committed items.
- A duplicate request arrives after browser session renewal.
- Two actors use the same request key.
- A retry source has equal time, invalid time, or no time.
- A retry record contains an unknown option.
- A cloud response covers only some targets.
- A database fault occurs before or after a transaction starts.
- A worker stops after it claims an item but before it stores a final outcome.
- A worker stops while later items remain unclaimed.
- A test process inherits a database, Redis, or cloud credential.

## Requirements

### Stale visibility

- **FR-001**: The portal MUST calculate stale status from `updated_at` and a
  fixed 24-hour limit.
- **FR-002**: Every terminal-state check MUST use
  `RunStateMachine.TERMINAL`. The implementation MUST remove the divergent
  sets from `runtime/signals.py` and `app/routes/review.py`.
- **FR-003**: The history page MUST show the last-update age for each run.
- **FR-004**: The history page MUST show a stale badge only for a stale run.
- **FR-005**: The run page MUST show the same age and stale decision.
- **FR-006**: A missing, invalid, or future time MUST produce `unknown`.
- **FR-007**: Display-only age updates MUST NOT change server eligibility.

### Safe reconciliation

- **FR-008**: Only an explicit confirmed operator action MAY reconcile a run.
- **FR-009**: A stale pre-cloud run MAY move only to `cancelled`.
- **FR-010**: A stale `stopping` run MAY move only to `stopped`.
- **FR-011**: The portal MUST use complete evidence for every target and task.
  The evidence MUST use the typed fields, null rules, safe fields, and
  canonical serialization in `data-model.md`.
- **FR-012**: The portal MUST claim `stopped` only when evidence proves no
  target writes and no live cloud task remains.
- **FR-013**: Incomplete, conflicting, or unavailable evidence MUST cause no
  run mutation and an `unknown` outcome.
- **FR-014**: Reconciliation MUST NOT send a cloud submit, stop, or cancel
  request.
- **FR-015**: The final run mutation and the item outcome MUST commit in one
  authoritative transaction. The transaction MUST also store the safe evidence
  summary and its matching action digest.

### Preview, selection, and confirmation

- **FR-016**: One request MUST contain 1 through 50 distinct run identifiers.
- **FR-017**: The server MUST reject duplicate identifiers and MUST NOT
  de-duplicate them.
- **FR-018**: The browser MUST request an authoritative preview before phrase
  entry.
- **FR-019**: The preview MUST remove identifiers that are not visible in the
  actor's current organization and history scope.
- **FR-020**: The preview MUST return the exact run count, site count, and
  per-site counts for the retained identifiers.
- **FR-021**: The action request MUST include a signed preview token bound to
  the actor, action, scope, ordered identifiers, and counts.
- **FR-022**: Cancel confirmation MUST require `CANCEL <run-count> RUNS`.
- **FR-023**: Retry confirmation MUST require `RETRY <run-count> RUNS`.

### Atomic bulk actions

- **FR-024**: After request validation, the portal MUST create one ordered
  durable outcome placeholder for each requested run before processing starts.
- **FR-025**: Each run in an initialized action MUST have exactly one durable
  outcome. The portal MUST set the action to `complete` only after all items
  have final outcomes.
- **FR-026**: A refusal, failure, or unknown result that changes no run MUST
  replace its placeholder with an outcome-only compare-and-swap write. An
  unprocessed item MUST remain `unknown` with reason `not_processed`.
- **FR-027**: Before each mutation, the portal MUST recheck write permission
  and the exact current lock token.
- **FR-028**: If either guard fails, the portal MUST stop later writes for that
  site.
- **FR-029**: After a site guard failure, later site items MUST remain
  `unknown` with reason `not_processed_after_site_guard_loss`.
- **FR-030**: A refusal or failure for one site MUST NOT stop another site.
- **FR-031**: A cancel MUST accept only a current pre-cloud state.
- **FR-032**: A cancel MUST send no cloud request.
- **FR-033**: A cancel mutation and its outcome MUST commit atomically.

### Safe retry

- **FR-034**: Retry MUST accept only `failed`, `stopped`, or `cancelled`.
- **FR-035**: A retry source MUST contain a valid `updated_at`.
- **FR-036**: The newest source MUST use `updated_at`, then `run_id` as the
  stable tie breaker.
- **FR-037**: The retry option allowlist MUST contain only `reboot`,
  `junos_file_action`, `strategy`, `force`, `stable_version`, `canary`, `rrm`,
  `peer_to_peer`, `ssr`, and `schedule`.
- **FR-038**: Nested option fields MUST match the fields accepted by
  `upgrade.options.build_options`.
- **FR-039**: An unknown option or invalid stored value MUST cause a
  deterministic refusal.
- **FR-040**: The portal MUST revalidate copied options with
  `upgrade.options.build_options`.
- **FR-041**: The portal MUST copy targets and approved options only.
- **FR-042**: The portal MUST drop old pre-checks, confirmations, task
  identifiers, and absolute schedule times without valid durations.
- **FR-043**: The live-run check, retry insert, and success outcome MUST commit
  in one transaction.

### Durable idempotency and replay

- **FR-044**: Idempotency MUST use the normalized durable actor identity and
  the request key.
- **FR-045**: Browser identifiers and session identifiers MUST NOT define the
  durable idempotency scope.
- **FR-046**: Another actor MUST receive 404 for an action result that the
  actor does not own.
- **FR-047**: The action store MUST use the composite domain key
  `(actor_scope, idempotency_key_digest)`.
- **FR-048**: The implementation MUST add the action primary-key strategy
  before it adds action persistence.
- **FR-049**: A same-key same-request replay MUST return the stored record
  without a new mutation.
- **FR-050**: A same-key different-request replay MUST return 409.
- **FR-051**: Replay MUST return an active `processing` lease. After lease
  expiry, one worker MAY take ownership with compare-and-swap. Recovery MUST
  finalize claimed items as `unknown` and MUST process only unclaimed items.
- **FR-052**: Recovery MUST NOT repeat a claimed or final item. It MUST
  preserve site stop decisions, finalize every remaining item, and change the
  action from `processing` to `complete` with compare-and-swap.

### Browser isolation

- **FR-053**: Factory overrides MUST install before route registration.
- **FR-054**: Browser tests MUST trap ArangoDB, Redis, cloud, and portal record
  file access.
- **FR-055**: The child environment MUST scrub all database, Redis, cloud,
  output, and backup credentials or paths.
- **FR-056**: The child MUST use explicit loopback port-1 sentinels for blocked
  network connectors.
- **FR-057**: Each browser session MUST use a unique port, test run identifier,
  record store, and artifact directory.
- **FR-058**: Each E2E response MUST include
  `X-MistHelper-E2E-Run-ID` only when test overrides are active.
- **FR-059**: The complete `tests/e2e/upgrade_portal` suite MUST run after all
  isolation controls are installed.

### Persistence, quality, and deployment

- **FR-060**: ArangoDB MUST be the declared operational store and the only
  authority for a run mutation and its action outcome.
- **FR-061**: If ArangoDB is unavailable, the portal MUST refuse the action
  before mutation and MUST NOT use SQLite, Redis, memory, or file fallback.
- **FR-062**: The action collection MUST use the registered composite domain
  key and indexes for actor-scoped result reads.
- **FR-063**: The deployment procedure MUST create and verify an ArangoDB
  backup before it changes the action schema or deploys the feature.
- **FR-064**: The recovery procedure MUST restore the backup to an isolated
  target and verify the run and action collections before production use.
- **FR-065**: The first release MUST retain action records for the lifetime of
  their referenced run records. It MUST perform no automatic action cleanup.
- **FR-066**: The portal MUST NOT report item or action success until it
  verifies the required durable transaction.
- **FR-067**: The combined verification matrix MUST cover every requirement at
  the appropriate unit, contract, integration, browser, or manual layer.
- **FR-068**: The explicit feature manifest MUST include committed branch
  changes, staged changes, unstaged changes, and feature-owned untracked files.
  It MUST list every planned path before the first source edit. It MUST reject
  a new feature path that is outside its approved scope.
- **FR-069**: Before implementation, the team MUST claim issue #2447 and MUST
  compare active worktrees, active branches, and open pull request files with
  the complete feature manifest.
- **FR-070**: The staging step MUST use the explicit feature manifest and MUST
  prove that every changed feature file is staged.
- **FR-071**: The team MUST fix feature-caused failures in this feature.
- **FR-072**: Before any unrelated repair, the team MUST create one GitHub
  issue for that failure.
- **FR-073**: The verification MUST measure a fixed 50-row history workload and
  a fixed 50-run local no-cloud batch.
- **FR-074**: The README, portal operator guide, and changelog MUST update
  before local gates.
- **FR-075**: Deployment MUST run local gates, rebase onto `origin/main`, push
  the feature branch, open the required pull request, pass all CI and approval,
  add `auto-merge`, squash merge, wait for the merged `main` image, verify its
  exact revision, deploy, and check health.
- **FR-076**: Automated tests MUST NOT start a live Morrison House firmware
  action.

## Key Entities

- **Run**: One firmware plan for one site.
- **Stale assessment**: The age and stale result from one server clock.
- **Authoritative preview**: The visible ordered selection and exact counts.
- **Action record**: The durable request, placeholders, and final outcomes.
- **Action outcome**: One result for one requested run.
- **Action source**: Bulk preview or single-run reconciliation.
- **Item processing state**: Pending, claimed, or final.
- **Actor scope**: The normalized durable identity that owns an action.
- **Reconciliation evidence**: The proof for one stale `stopping` run.
- **Factory overrides**: The complete test-owned construction dependencies.

## Success Criteria

- **SC-001**: Both pages agree on stale status for all tested records.
- **SC-002**: Every initialized request reaches one durable final outcome for
  each requested run, including after worker recovery.
- **SC-003**: Duplicate run identifiers cause a request-level refusal.
- **SC-004**: A mixed batch continues valid sites and stops a site after guard
  loss.
- **SC-005**: Replayed requests create zero duplicate mutations.
- **SC-006**: A retry creates at most one new nonfinal run for each site.
- **SC-007**: Reconciliation uses `stopped` only with complete proof.
- **SC-008**: The full browser suite makes zero persistent connector calls.
- **SC-009**: The 50-row fixed workload completes in less than 1 second.
- **SC-010**: The 50-run fixed no-cloud batch completes in less than 5 seconds.
- **SC-011**: The verification matrix maps all 76 requirements to evidence.
- **SC-012**: Every changed executable file has a recorded applicable gate.
- **SC-013**: The deployed image revision equals the merged `main` revision.
- **SC-014**: Every feature Markdown file scores at least 80 with the STE
  linter.

## Assumptions

- The current authentication, authorization, lock, and audit rules remain
  authoritative.
- `updated_at` is the only age and newest-source time.
- The existing options validator remains the option authority.
- The production run record and action outcome share one ArangoDB transaction.
- Existing SQLite and file fallbacks cannot join that transaction.
- Reconciliation creates a single-run action record without a preview.
- The first release retains action records while their run records exist.
- The optional live check occurs only after the merged image is deployed.

## Out of Scope

- Automatic cancellation of cloud-active work.
- Repetition of a claimed or completed action item.
- A SQLite, Redis, memory, or file authority for run actions.
- Automatic cleanup of action records.
- A bulk stop action.
- Changes to Mist cloud firmware behavior.
- Repairs for unrelated failures.
