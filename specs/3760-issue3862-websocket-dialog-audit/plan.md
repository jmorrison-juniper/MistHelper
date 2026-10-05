# Implementation Plan: Issue 3862 WebSocket Dialog Audit

**Branch**: `jmorrison-juniper-websocket-dialog-testing` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3760-issue3862-websocket-dialog-audit/spec.md`

## Summary

Build an independent Playwright audit of real catalog and operation form construction.
Keep dialog inspection separate from live subscription results.
Reject unknown requests before transmission.
Never execute live utilities, shell commands, captures, or device changes.
Issue #3862 remains the audit parent.
Create separate repair issues only after defects have reproducible evidence.

The original planning invocation produced design artifacts only.
Subsequent user turns authorized implementation and validation.
The parent handles environment startup, GitHub updates, and authorized publication after checks.
The harness session does not create issues, commit, push, or merge.
It leaves PR #3814's JavaScript and browser test unchanged.

### Harness publication boundary

The preceding invocation description records the planning phase, not the current execution restriction.
The user authorized implementation, local startup, read-only testing, commits, and merges.
This pull request delivers the internal audit harness, not completion of every audit acceptance criterion.
The parent issue stays open while repairs and unavailable-target journeys remain incomplete.

The app owns the branch `jmorrison-juniper-websocket-dialog-testing`.
The workspace instruction requires direct commits on that branch.
That instruction takes precedence over the repository branch-name convention.
The pull request title and commit subject will use Conventional Commits.

The explicit feature manifest contains this specification directory and `tests/e2e/websockets_tab/dialog_audit/`.
It excludes `.env`, local reports, coverage configuration, container overrides, and shared SpecKit feature-selection metadata.
No release-note fragment is required for this internal-only harness.
The repository fragment policy requires that reason in the pull request body.
Separate user-visible repairs own their release-note fragments.

Before publication, run syntax, Ruff, Black, targeted types, isolated browser tests, and support coverage.
Require at least 80 percent support coverage and zero new test-quality findings.
Run the guide-input preflight, commit the explicit manifest, and rebase onto the fetched intended `origin/main`.
Repeat affected checks after a rebase.
Require clean relevant files before the changed-base test-quality check.
Run the full test-quality gate before the push.
Preserve the pull request template and identify every unrun or blocked check.
Merge only after current required CI checks pass, including CodeQL.

The harness does not enter the product image.
Do not start a registry build or deploy an image for test-only changes.
Refresh the user-requested local portal separately when merged product repairs change its code.
Keep the persistent portal on loopback and preserve its data.

The corrected read-only stream journey passed with no remote events.
It verified connecting, live, stopping, and stopped states for its own session.
This is an explicit no-data observation, not proof that every stream receives events.
The complete dialog inspection still records three empty-everywhere target blockers.
Issue #3888 tracks cancellation, and issue #3889 tracks optional client choices.
Issue #3890 is fixed through merged pull request #3891.

## Technical Context

**Language/Version**: Python 3.13 or newer. Browser JavaScript remains unchanged.

**Primary Dependencies**: Repository runtime and development requirements, Flask, mistapi `>=0.64.0,<0.65`, Playwright `1.63.0`, pytest-playwright `0.9.0`.

**Storage**: Restricted local files under ignored `test-artifacts/websocket-dialog-audit/`. No database migration or API export.

**Testing**: Class-based pytest tests and Playwright Chromium. Real catalog, template, and scripts in isolated mode. Separate opt-in live mode.

**Target Platform**: Local macOS host and supported repository development hosts. Existing authorized portal for live mode.

**Project Type**: Test harness for an existing Flask portal. No new product service or Mist transport.

**Performance Goals**: Selection and connection each take at most 15 seconds. Observation takes at most 30 seconds.
Each operation remains bounded. All-site/map traversal shares a 90-second deadline within a 120-second
outer pytest bound that includes browser setup and report teardown.
The separate exact-key read-only journey verifies its own local stop within five seconds.

**Constraints**: Existing authentication only. No `.env` disclosure or harness-controlled service changes.
The parent started the user-authorized normal portal on loopback8055.
No live allowlist entry follows from a display name, safety badge, or SDK definition alone.

**Scale/Scope**: All operations returned by the selected revision's catalog.
Source has 18 static channels. Utilities are discovered from installed SDK facades.
Do not hardcode utility totals or replace the catalog with a fixed fixture.

**Resolved planning decisions**: See [research](design/research.md).
At planning time, missing URL, browser, environment, authentication and runtime verification were execution blockers.
They are not current blockers: see the measured implementation evidence and publication boundary above.
There are no unresolved feature-scope clarifications.

## Constitution Check

| Gate | Before research | After design |
|---|---|---|
| Five-item structure | Use a compliant existing test parent. Record process-folder debt. | PASS: proposed nested packages have at most five children. |
| Classes and bounded functions | No production restructuring. | PASS: named classes own inventory, policy, journeys, and reports. Keep five parameters and 25-line limits. |
| Safety and secrets | Fail closed. No live execution in planning. | PASS: two-layer policy, restricted artifacts, and synthetic negative tests are required. |
| Mist REST SDK | Inspect actual selector call sites. | PASS for design: eight GET methods verified upstream. Reverify installed and deployed versions before live use. |
| Owned WebSocket transport | Do not introduce or modify one. | PASS: existing transport is only audited. Its runtime proof remains a live prerequisite. |
| Logging and comments | No implementation code. | PASS: future code requires inline comments, structured ASCII logs, and before/after action logging. |
| Outputs and evidence | Product outputs stay under `data/`. | PASS: test evidence uses ignored `test-artifacts/`, not product exports. |
| Ownership | PR #3814 owns two protected files. | PASS: neither file changes. Overlapping repairs require recorded coordination. |
| Release pipeline | The historical design-only run did not start a code-release pipeline. | Current harness publication uses the checks and parent-owned workflow described above. |

Existing source transport does not create an exception for new transport work.
Any transport repair must name its SDK path and failed output contract in a separate specification.
It must prove SDK insufficiency with contract tests before implementation review.

The app manages the current branch.
Do not rename, switch, create, or rebase this branch during planning or audit execution.
Later release work must reconcile branch/base policy and the full deployment pipeline with the session owner.
Do not silently rebase onto a guessed base.
Use Conventional Commit subjects and the required pull request template in later release work.
Never merge with failed, missing, skipped, or stale required checks.
Never deploy or restart production without separate human approval.

## Project Structure

### Documentation

```text
specs/3760-issue3862-websocket-dialog-audit/
  spec.md
  plan.md
  checklists/
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      audit-contract.md
  tasks.md                    # Later speckit.tasks output, not created here
```

The design subdirectory keeps this feature within five direct children after task generation.
The existing `specs/` folder has 775 direct entries at inspection time.
Use the constitution's unique process-record exception for this feature.
Track incremental process-folder organization separately. Do not move unrelated specifications in this audit.

### Implemented harness

```text
tests/e2e/websockets_tab/dialog_audit/
  conftest.py                  # Local options and isolated network/browser fixtures
  support/
    __init__.py
    inventory.py              # InventoryBuilder and OperationOracle
    policy.py                 # BrowserRequestPolicy, LiveRequestPolicy, ReadonlyLifecyclePolicy
    journeys.py               # Form, picker, SDK/DOM UX and all-parent inspectors
    reporting.py              # Restricted distinct-mode AuditReportWriter
  test_inventory.py
  test_dialogs.py
  test_live.py
```

Each implemented package has at most five children; the harness root uses namespace imports, not another initializer.
The designated browser CI job collects `tests/e2e/` and installs Chromium.
The root-and-contracts shard does not install Chromium; browser tests must not live under its test-tools scope.
Place this nested harness in the existing WebSockets e2e group.
Correct browser-job ownership takes precedence over that group's existing five-item folder debt.
No sibling browser tests or production files are changed by this migration.
Use explicit test selection. Live tests must not execute through ordinary collection.

### Existing source boundaries

- `src/mist/realtime/websocket_streams/catalog/`: real channel fields and dynamic utility discovery.
- `src/mist/realtime/websocket_streams/web/`: real blueprint, template, picker routes, and scripts.
- `src/mist/realtime/websocket_streams/intake/`: checked targets and SDK selector reads.
- `src/mist/realtime/websocket_streams/live/`: runner, transport, subscription, and stop behavior.
- `web_portal/routes/operations.py`: site list and the additional site-statistics read.

These are read-only planning references, not this feature's implementation destinations.

## Phase 0: Research

Completed [research.md](design/research.md).
Read necessary repository source directly.
Use one bounded public-source research task for SDK channel definitions.
Verify selector methods independently against SDK release source.
Resolve environment, inventory, evidence, safety, ownership, and report decisions.

## Phase 1: Design

Completed [data model](design/data-model.md), [contract](design/contracts/audit-contract.md), and [validation guide](design/quickstart.md).

### Bounded work packages for later task generation

These are design packages, not executable `tasks.md` or authorization to implement.

| Package | Prerequisite | Deliverable and stop condition | Requirements |
|---|---|---|---|
| A. Capability record | None | Record URL, revisions, environment, browser, and authentication availability. Stop live work on any blocker. | FR-009, 010, 011, 014, 016 |
| B. Inventory and oracle | A for live inventory, source available for isolated work | Real catalog joined to SDK signatures and runner paths. Record every unknown. Never infer safe behavior. | FR-001, 002, 006, 007 |
| C. Safety boundary | B | Synthetic negative tests prove zero forbidden transmissions at browser and server boundaries. Stop on any policy gap. | FR-006, 007, 008, 009 |
| D. Real form inspection | B and C | Inspect every operation with real assets. Report field, purpose, dependencies, empty states, and cancellation results separately. | FR-002, 003, 004, 005, 011 |
| E. Safe live observation | A, C, D, verified per-operation decision | Run one serial subscription per approved key. Stop within bounds and close only owned sessions. Record output, no-data, denied, or blocked. | FR-005, 006, 010, 011 |
| F. Defect triage | D or E evidence | Deduplicate proven causes. Reuse or create one repair issue per defect in a later authorized phase. Link #3862. | FR-012 |
| G. One repair | F and ownership clearance | Separate SpecKit workflow, failing regression, narrow repair, passing regression, unique release note. | FR-013, 015 |
| H. Release validation | G | Applicable local and required CI checks, current revision, review, template, and authority all pass. Otherwise no merge. | FR-015, SC-008 |

Each package runs serially against live targets.
Parallel work may inspect source or run isolated tests without shared live state.
Package G repeats independently for each linked defect.
No package treats blocked or skipped evidence as a pass.

## Complexity Tracking

| Existing debt or constraint | Treatment | Separate incremental action |
|---|---|---|
| `specs/` exceeds five children | Unique feature process record exception. Nested design files prevent further feature-level violations. | Later process-folder organization proposal with compatibility review. |
| `tests/e2e/websockets_tab/` has six children | No edits or added children. Independent compliant test package. | Later ownership-coordinated terminal-test organization. |
| Constitution release pipeline includes production deployment | No code changes here. Later deployment waits for separate approval. | Release owner records approved branch/base and deployment handoff before release. |
| Python plan setup absent and PowerShell unavailable | Manual feature-path resolution uses existing feature state and the supplied template structure. | Tooling owner may repair setup portability separately. |

## Planning execution record

Repository source revision: `06c92559cd043dff755c665c6934a0d100dc99fd`.
The pre-existing `.specify/feature.json` change is preserved.
The requested Python setup command fails because its file does not exist.
`pwsh` is unavailable. No setup tooling is installed or changed.
The plan uses manually resolved `FEATURE_SPEC`, `IMPL_PLAN`, `FEATURE_DIR`, and the actual Git branch.
No live audit result or proven dialog defect is claimed.

Artifact validation found five generated documents, no broken relative links, and no unresolved template markers.
The feature has four direct children. Its design directory has four direct children.
Protected files have no diff against `HEAD`. The branch is unchanged.

The optional pre-plan and post-plan commit hooks were displayed and skipped as requested.
Ruby's YAML parser successfully read both hook lists after the initial Python parser import failed.
The mandatory `speckit.companion.after-plan` hook was dispatched through the local SpecKit event runner.
It returned `Event command 'speckit.companion.after-plan' not found`.
The artifact resolver also reported the command as unknown.
The event runner exited zero, but that does not indicate hook success.
Companion state was not updated. Hook completion remains blocked by unavailable local tooling.
That historical design-only invocation did not synthesize `.spec-context.json` or install an extension.
Current implementation also does not synthesize companion state after unavailable hook commands.

## Current implementation evidence

The new harness measures real isolated HTML/assets and live GET-only forms.
It visits all four returned sites and every returned map serially.
Family filters and dependent refresh are checked. Unchanged parents do not require new responses.
Responses are cached only in the audit browser context.
Reports retain ordinal scopes and counts, never private identifiers.
Installed SDK/reviewed handlers provide GET evidence; independent deployed-backend attestation is not claimed.

All 72 forms have measured evidence. Target availability passes for 69 operations and blocks three.
Missing Cancel is one shared user-story gap. Four optional client-choice enhancements have SDK/DOM evidence.
These are not executed-operation functional failures or a complete audit pass.
An opt-in exact-key `site.stats.devices` observation lifecycle is implemented.
It admits one exact JSON start, response-issued own-session message reads and one local stop.
Source verification confirms observation SUBSCRIBE and local close, not a remote Mist mutation.
The user's original read-only authorization covers this journey; no whole-server guard or new approval is required.
The parent verifies deployed `2900f56` against the local reviewed base before its live execution.
Generalized permission and defect/repair frameworks remain incomplete.
See `tasks.md` and `design/quickstart.md` for current commands and historical blockers.
