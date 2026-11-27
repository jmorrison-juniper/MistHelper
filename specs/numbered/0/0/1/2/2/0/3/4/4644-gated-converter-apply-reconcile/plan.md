# Implementation Plan: Gated Converter Apply and Reconciliation

**Branch**: `feat/4644-gated-converter-apply` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/`. Decimal 4644 equals `122034` in base 5. The route pads it to eight levels, which gives `0/0/1/2/2/0/3/4`. Source: `.specify/scripts/powershell/spec-route.ps1`, line 7 (default width 8) and line 17 (base 5), read from `main`.

## Summary

Add a gated apply path to the converter. The path has one typed approval, one use, one scope lock, a preflight read, a bounded write loop, and a read-back for each object. Every family starts disabled. No write runs in this change. The apply executor depends on issue 4636 for the state records and the private store.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, section Language and environment.
- **Primary Dependencies**: `mistapi==0.64.1` only for Mist calls. Source: `requirements.txt` line 129. The standard library covers the rest.
- **Storage**: Private JSON records under `data/cisco_config_converter/state/`, written by `PrivateStateStore` from issue 4636. Writes stay disabled until owner approval (issue 4636 decision D-3).
- **Testing**: pytest under `tests/integration/web_portal/cisco_config_converter/apply/`. The tests use a recording SDK double and no live request.
- **Target Platform**: Windows 11, macOS, Linux, and the Podman container that runs as UID 1000.
- **Project Type**: Feature code inside the existing web portal interface package.
- **Performance Goals**: One run per scope. Each run has a 10-minute deadline. Each write has a 90-second wait bound.
- **Constraints**: No live Mist call in tests. No new dependency. No new route registration. No change to the shared portal files.
- **Scale/Scope**: Eight families, five reconciliation reads, one executor, one adapter, one classifier, and four test modules.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-item rule, levels | Pass after X-1 | The converter root, `state/`, `state/lifecycle/`, and `apply/` each hold five children or fewer. Issue 4636 must first apply amendment X-1. |
| I. Five-item rule, functions | Pass in design | Each method has five parameters or fewer, five logical blocks or fewer, and 25 lines or fewer. Code review checks each method. |
| I. Five-item rule, classes | Pass in design | Each class holds five members or fewer. |
| II. Class-based architecture | Pass | Each behavior sits in a named class. No wrapper function is planned. |
| III. Safety-first input | Pass | The approval word is checked on the server. Each identifier is generated, and the client never chooses it. |
| III. Destructive operations | Pass with warning | Each write needs a typed `APPLY`, an approval, and a backup. No command-line menu is added. Enablement needs decision D-17. |
| III. Secrets in logs | Pass | FR-023 and tests TST-18 and TST-26 cover this rule. |
| IV. Deployment pipeline | Pass for this record | No code changed in this drafting pass. The pipeline applies to each later change. |
| V. ASCII logs | Pass in design | Planned messages use ASCII only. |
| V. Structured logs | Fail until owner confirms equivalence | The planned logs use standard `logging` with key and value fields. Issue 4636 open item U-2 tracks the same gap. |
| VI. Inline comments | Fail now, pass after implementation | Each new line gets an inline comment in the same change. |
| VII. Action logging | Fail now, pass after T012 | Each action gets an info line before and a debug line after. |
| Technology: Python | Pass | Python 3.15 standard library and the pinned SDK only. |
| Technology: mistapi | Pass | Every Mist call uses a mistapi method with explicit arguments. No direct HTTP request. |
| Technology: owned WebSocket | Not applicable | This record owns no transport. |
| Technology: UV and requirements | Pass | No dependency change. |
| Technology: Podman | Pass | No container starts in this change. |
| Technology: file paths | Pass | The store uses `pathlib.Path` through issue 4636. |
| Technology: operational store | Pass | No declared operational store exists. The store follows issue 4636, which fails closed and verifies each write. |
| Technology: export boundary | Pass | No export is added. |
| Technology: database keys | Pass | Each object uses its natural Mist ID. |
| Technology: data directory | Pass | Private state stays under `data/`, which `.gitignore` line 95 ignores on `main`. |
| Development: documentation | Pass | No operator document changes until the portal integration in T032 registers the route. |
| Escalation | Pass | This change touches more than three files and two classes. This record exists. |
| Multi-agent git: issue first | Pass | Issue 4644 exists and carries the `feature`, `web-portal`, and `needs-human-review` labels. |
| Multi-agent git: overlap | Pass with conditions | PR #4208 owns `web_portal/app.py`. This plan does not touch that file. The `converter.js` file is shared with issue 4647. Boundary D-16 applies. |

## Capacity and Structure Inventory

Counts assume issue 4636 applies amendment X-1 and this record applies its own changes. Each row counts physical children.

| Directory | Children after this change | Limit | Status |
| --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/` | 5: `__init__.py`, `conversion.py`, `routes.py`, `presentation/`, `state/` | 5 | At limit. Unchanged. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Top-level names: `logger`, `ConverterRequest`, `ConverterRoutes`, `ConverterInput` (4) | 5 | One name free. Not used. |
| `ConverterInput` | 5 methods after `apply_action` is added | 5 | At limit. |
| `src/interfaces/portals/cisco_config_converter/state/` | 5: `__init__.py`, `records/`, `lifecycle/`, `storage/`, `execution.py` | 5 | At limit after X-1. |
| `state/records/` | 3: `__init__.py`, `intake.py`, `proposal.py` | 5 | Compliant. |
| `state/lifecycle/` | 5: `__init__.py`, `approval.py`, `backup.py`, `operation.py`, `transitions.py` | 5 | At limit. Gates are added to existing modules. |
| `state/execution.py` | Top-level names: `logger`, `MistWriteAdapter`, `OutcomeClassifier`, `ApplyExecutor`, `ReconciliationReader` (5) | 5 | At limit. |
| `state/storage/` | 5 (issue 4636) | 5 | At limit. Unchanged. |
| `tests/integration/web_portal/cisco_config_converter/` | 4: `__init__.py`, `test_routes.py`, `state/`, `apply/` | 5 | Compliant. |
| `tests/integration/web_portal/cisco_config_converter/apply/` | 5: `__init__.py` and four test modules | 5 | At limit. |
| `tests/contract/` | 17 | 5 | Over limit before this change. Not touched. |

The nested package guard counts direct Python modules and child directories. The constitution counts every physical child, including `__init__.py` and `presentation/`. This table uses the stricter constitution count.

## Structure Decision

Issue 4636 uses all five slots in `state/`. The apply executor needs one more slot. Amendment X-1 moves `intake.py` and `proposal.py` into `state/records/`. That frees one slot in `state/` for `execution.py`. The executor sits beside the records, the lifecycle, and the store. Route handling stays in the existing `ConverterInput` class, so `routes.py` gains no top-level name. Tests go under the feature-owned `apply/` folder, as decision D-15 explains.

Issue 4646 moves `backup.py` into `state/lifecycle/recovery/`. This record uses `BackupGate` in its current module path, and it follows the move.

## Architecture

The apply flow runs in this order:

1. The route reads the typed word and the approval identifier. It refuses any word other than `APPLY`.
2. `ApprovalGate` checks the operator, expiry, digests, and use. It refuses unless every check passes.
3. `BackupGate` checks each backup manifest for the object families in the change set.
4. `ApplyExecutor` takes the scope lock and consumes the approval under the lock.
5. `ApplyExecutor` reads each target object and compares its digest. Any mismatch refuses the run before the first write.
6. `ApplyExecutor` writes the operation record in phase `executing`. Then it runs each change item in order. Each item gets a re-read, a body build, one SDK call through `MistWriteAdapter`, and one classification through `OutcomeClassifier`.
7. `ReconciliationReader` reads each object back. A verified outcome needs a matching read-back.
8. `ApplyExecutor` sets the final phase. It reports success only after the store verifies the operation record.

## File-by-File Change Map

| Path | Action | Content |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/state/records/proposal.py` | Modify | Add `ChangeSet`. Issue 4636 creates the file. X-1 moves it. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/approval.py` | Modify | Add `ApprovalGate` beside `ApprovalRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py` | Modify | Add `BackupGate` beside `BackupManifest`. |
| `src/interfaces/portals/cisco_config_converter/state/execution.py` | Add | Add `MistWriteAdapter` with the family registry as a class attribute, `OutcomeClassifier`, `ApplyExecutor`, and `ReconciliationReader`. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | Add `ConverterInput.apply_action`. Add one `add_url_rule` line for `/apply` in `ConverterRoutes.blueprint`. |
| `tests/integration/web_portal/cisco_config_converter/apply/__init__.py` | Add | Package marker. |
| `tests/integration/web_portal/cisco_config_converter/apply/test_apply_gates.py` | Add | Tests TST-01 to TST-08 and TST-27. |
| `tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py` | Add | Tests TST-09 to TST-19. |
| `tests/integration/web_portal/cisco_config_converter/apply/test_apply_reconcile.py` | Add | Tests TST-20 to TST-23. |
| `tests/integration/web_portal/cisco_config_converter/apply/test_apply_routes.py` | Add | Tests TST-24 to TST-26. |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Modify | Update the import line after X-1. |

Unchanged paths: `presentation/converter.html`, `presentation/converter.js` (owned by issue 4647), `web_portal/app.py`, `web_portal/templates/base.html`, `web_portal/services/config.py`, `requirements.txt`, `.gitignore`, `compose.yml`, and `documentation/`.

Amendments in other draft records, applied before this record starts code work:

- X-1 in issue 4636: move `intake.py` and `proposal.py` under `state/records/`.
- X-2 in issue 4636: add the outcome `not-applied` to the operation outcomes.
- X-3 in issue 4636: add the transition `approved` to `reviewed` for cancel.
- X-4 in issue 4636: include the change-set digest in the scope digest.
- X-5 in issue 4646: reuse `ReconciliationReader` and `OutcomeClassifier`. Remove its own `OutcomeReconciler`.
- X-7 in issue 4648: group its two test files under a `portal/` folder. The converter test root would otherwise hold seven children.
- X-9 in issue 4646: follow this record for the location of `BackupGate`.

## Dependencies

- No package is added and no pin changes. `mistapi==0.64.1` stays in `requirements.txt` line 129.
- The executor depends on the issue 4636 store, locks, and record types.
- The executor depends on the issue 4642 reads and the issue 4643 backup manifests.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| The SDK repeats a write after HTTP 429. | A create can run twice. | The executor counts one attempt for each write. A final 429 is indeterminate. Test TST-14 counts the SDK attempts with a mocked transport. Decision D-7 governs this risk. |
| The SDK sets no timeout on writes. | A call can hang and hold the scope lock. | Each write runs under a bounded wait. A missed wait is indeterminate. Test TST-16 proves the bound. |
| Mist offers no compare-and-set. | A change between the re-read and the write goes undetected. | The executor re-reads before each write. The residual risk is recorded in `analysis.md` and in the spec edge cases. |
| Mist PUT semantics are unverified. | Omitted fields can be removed. | The executor sends the complete body. Each read-back compares unrelated fields. Unverified item U-1 tracks this claim. |
| The converter root and `state/` have no free slot. | A new module breaks the five-item rule. | Amendment X-1 frees one slot. The capacity table shows each count. |
| Two drafts edit the same files. | Merge conflicts or lost work. | Decision D-16 sets the file owners. The hot-file rule applies to `converter.js`. |
| The apply path runs before issue 4636 lands. | A missing type causes an import error. | Task T002 blocks the code tasks. |

## Rollback Steps

1. Revert the squash commit that adds the apply code, through a pull request on `main`.
2. Confirm that `state/execution.py` is gone and that `ConverterInput` has four methods.
3. Run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`. It must pass.
4. Remove `data/cisco_config_converter/state/operation/` only when a test or a manual run created it.

Caution: Removing an operation record can hide the outcome of a write that already ran. Check the outcome in Mist before removing the record.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `tests/contract/` holds 17 children. | Grandfathered, not touched | Predates this change. | Parent T021 path is not used. See decision D-15. |
| `src/interfaces/portals/` holds six children. | Grandfathered, not touched | Predates this change. | None in this record. |
| `state/` holds five children after X-1. | New design, at limit | Required for `execution.py`. | Verified by the capacity table. |

This change adds no new violation.
