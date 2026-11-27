# Implementation Plan: Compliant Converter Package and State Model

**Branch**: `feat/4636-converter-state-model` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model/`. The route follows the base-5 rule in `.specify/scripts/powershell/spec-route.ps1`. Decimal 4636 equals `122021` in base 5. Padded to eight levels, it gives `0/0/1/2/2/0/2/1`.

## Summary

Replace the converter `models.py` module with a compliant `state/` package. Add six private record types, a transition table, and a private file store. The store writes each record with a seal, a lock, and a read-back. The change stays offline. It adds no cloud call, no route, and no shared portal edit.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, line 20.
- **Primary Dependencies**: Standard library only. The plan uses `hashlib`, `hmac`, `json`, `os`, `datetime`, `uuid`, `enum`, `dataclasses`, and `multiprocessing`. Native locks use `msvcrt` on Windows and `fcntl` on POSIX. No dependency changes.
- **Storage**: Private JSON files under `data/cisco_config_converter/state/`. Production writes stay disabled until owner approval. Decision D-3.
- **Testing**: pytest in `tests/integration/web_portal/cisco_config_converter/state/`. Existing converter tests stay in place.
- **Target Platform**: Windows 11, macOS, Linux, and the Podman container that runs as UID 1000.
- **Project Type**: Feature package inside the existing web portal interface package.
- **Performance Goals**: None. Each request handles one approval or one record. No latency target exists.
- **Constraints**: No cloud call. No route change. No shared file change. No compatibility shim. Synthetic data only.
- **Scale/Scope**: Six record types, one transition table, one store, one lock class, and five test modules.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule, levels | Pass | The converter root keeps five children after `models.py` becomes `state/`. |
| I. Five-Item Rule, functions | Pass | Each planned method has five parameters or fewer. T012 runs the complexity gate with maximum 10. |
| II. Class-based architecture | Pass | Each behavior sits in a named class. No wrapper function is planned. |
| III. Safety-first input | Pass | `SourceConfiguration` validation stays. Identifiers are generated, not taken from clients. |
| III. Destructive operations | Pass | No destructive operation is added. Cloud writes stay blocked. |
| III. Secrets in logs | Pass | `SecretRedaction` and the logging test cover logs and public views. |
| IV. Deployment pipeline | Pass for this record | No code changed in this drafting pass. The pipeline applies to each later change, from T-LOCAL-GATES to T-MERGE. |
| V. ASCII logs | Pass | Planned messages use ASCII only. |
| V. Structured logs | Fail until U-2 closes | Planned logs use standard `logging` with key=value fields. The constitution asks for structlog or an equivalent. The owner must confirm equivalence. |
| VI. Inline comments | Fail now, pass after T004 and T012 | `routes.py` and `conversion.py` have zero `#` comments. `models.py` has one. Each touched or new line gets a comment. |
| VII. Action logging | Fail now, pass after T010 | `models.py` has zero logger calls. The store logs before and after each action. |
| Technology: Python | Pass | Python 3.15 standard library only. |
| Technology: mistapi | Pass | No Mist call is made. |
| Technology: owned WebSocket | Pass | Not applicable. |
| Technology: UV and requirements | Pass | No dependency change. |
| Technology: Podman | Pass | No container change. |
| Technology: test containers | Pass | No container is started. |
| Technology: file paths | Pass | The store uses `pathlib.Path`. No separator is hard-coded. |
| Technology: operational store | Pass | No declared operational store exists (U-3). The plan defines fail-closed behavior, read-back, retention, and backup. Production stays gated by G4. |
| Technology: export boundary | Pass | No export is added. |
| Technology: database keys | Pass | No Mist entity row is written. |
| Technology: data directory | Pass | Private state stays under `data/`. `.gitignore` line 95 ignores that directory. |
| Technology: container security | Pass | No ownership change. Production needs UID 1000 write access. |
| Technology: Zscaler | Pass | Not applicable. |
| Development: menu operations | Pass | Not applicable. No menu changes. |
| Development: testing skip list | Pass | Not applicable. |
| Development: documentation | Pass | No README or user-facing change. No changelog fragment is required. |
| Escalation | Pass | The change touches more than three files and two classes. This record exists. |
| Multi-agent git: issue first | Pass | Issue 4636 exists and carries the `feature` and `web-portal` labels. |
| Multi-agent git: branch | Pass | The branch is `feat/4636-converter-state-model`, from `main`. |
| Multi-agent git: overlap | Pass | Seven open PRs were scanned. Only PR #4208 touches `web_portal/app.py` and `web_portal/templates/base.html`. This plan edits neither file. |

## Capacity and Structure Inventory (T004)

The inventory uses `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read on 2026-11-26. Remote listings and blob SHAs appear in `design/research.md`, section R4.

| Directory | Physical children | Guard count | Limit | Status |
| --- | --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/` | 5: `__init__.py`, `conversion.py`, `models.py`, `presentation/`, `routes.py` | 3 | 5 | At limit. `models.py` is replaced. |
| `src/interfaces/portals/cisco_config_converter/models.py` | 5 top-level classes at lines 13, 21, 29, 38, and 84 | Not applicable | 5 | At limit. Replaced by `state/`. |
| `src/interfaces/portals/` | 6: `__init__.py`, `cisco_config_converter/`, `guest_authorizations.py`, `licensing_comparison/`, `upgrade_portal/`, `wan_dashboard/` | 5 | 5 | Over limit. Not touched. |
| `tests/contract/` | 17 | Not measured | 5 | Over limit. Not touched. No child added. |
| `tests/contract/web_portal/` | 1 | Not measured | 5 | Not used. |
| `tests/e2e/` | 5 | Not measured | 5 | At limit. Not touched. |
| `tests/e2e/web_portal/` | 32 | Not measured | 5 | Over limit. Not touched. |
| `tests/integration/web_portal/` | 4 | Not measured | 5 | Compliant. Not touched. |
| `tests/integration/web_portal/cisco_config_converter/` | 2: `__init__.py`, `test_routes.py` | Not measured | 5 | Becomes 3 with `state/`. |
| `tests/unit/marvis/mist/resources/gateway/overrides/` | 5 | Not measured | 5 | At limit. One import line changes. No child added. |

The nested package guard counts direct Python modules, except `__init__.py`, plus directories that hold tracked Python files. The constitution counts every physical child, including `__init__.py` and `presentation/`. Both counts appear in this record. Source: `tests/guardrails/test_nested_package_structure.py`, lines 89, 106, and 117.

## Replacement Layout (T004)

```text
src/interfaces/portals/cisco_config_converter/
  __init__.py                  unchanged
  conversion.py                import lines change, no logic change
  routes.py                    import line changes, Blueprint paths unchanged
  presentation/                unchanged
  state/                       new package that replaces models.py
    __init__.py                docstring only
    intake.py                  REVIEW_LIFETIME, SourceConfiguration, ReviewState, SourceRecord, ReviewRecord
    proposal.py                GatewayTemplate, UnsupportedItem, ConversionProposal, ProposalRecord
    lifecycle/
      __init__.py
      approval.py              ApprovalRecord
      operation.py             OperationPhase, OperationRecord
      backup.py                BackupManifest
      transitions.py           StateRefused, TransitionTable
    storage/
      __init__.py
      store.py                 PrivateStateStore, PersistenceUnavailable
      integrity.py             CanonicalDigest, RecordSeal
      redaction.py             SecretRedaction
      locks.py                 NativeFileLock

tests/integration/web_portal/cisco_config_converter/
  __init__.py                  unchanged
  test_routes.py               unchanged
  state/                       new test package
    __init__.py
    test_state_records.py
    test_state_transitions.py
    test_state_store.py
    test_state_multiworker.py
```

Each directory holds five children or fewer. The `state/` package holds five children. The `lifecycle/` and `storage/` packages each hold five children. The converter test folder holds three children, and the new `state/` test folder holds five.

Each module holds five top-level names or fewer. `intake.py` holds five names, which is the limit. `proposal.py` holds four. Every other module holds one or two.

## Symbol Map (T004)

The symbol gate treats `models.py` as removed. Every name keeps its spelling and its class body. Only the module path changes. The change record documents this move.

| Name | Old location | New location |
| --- | --- | --- |
| `GatewayTemplate` | `models.py` line 13 | `state/proposal.py` |
| `UnsupportedItem` | `models.py` line 21 | `state/proposal.py` |
| `ConversionProposal` | `models.py` line 29 | `state/proposal.py` |
| `SourceConfiguration` | `models.py` line 38 | `state/intake.py` |
| `ReviewState` | `models.py` line 84 | `state/intake.py` |

Class `__module__` values change for the five moved names. The repository move rules require this record of the change. Source: `.github/copilot-instructions.md`, section Move a module, line 261.

## Import Updates (T004)

| File | Current line | New line |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | line 6: `from .models import ConversionProposal, GatewayTemplate, SourceConfiguration, UnsupportedItem` | `from .state.intake import SourceConfiguration` and `from .state.proposal import ConversionProposal, GatewayTemplate, UnsupportedItem` |
| `src/interfaces/portals/cisco_config_converter/routes.py` | line 12: `from .models import ReviewState, SourceConfiguration` | `from .state.intake import ReviewState, SourceConfiguration` |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | line 6: `from src.interfaces.portals.cisco_config_converter.models import SourceConfiguration` | `from src.interfaces.portals.cisco_config_converter.state.intake import SourceConfiguration` |

No module keeps `models.py` as a re-export. The old-path search must return no match after the change.

## Architecture

The flow runs in this order. Each step writes one record and passes the identifier forward.

1. The browser sends one source. `SourceConfiguration` validates it in memory. `SourceRecord` stores only the digest, size, suffix, and owner.
2. `ConversionProposal` is produced by the existing DNS converter. `ProposalRecord` stores its digest and version.
3. `ReviewRecord` binds one source and one proposal digest. It expires 15 minutes after creation.
4. `ApprovalRecord` binds one verified operator, one proposal digest, one scope digest, and one use. It expires with the same 15-minute lifetime.
5. `OperationRecord` moves through the `TransitionTable`. Execution needs an unexpired, unconsumed approval and a verified `BackupManifest`.
6. `PrivateStateStore` writes every record. It uses a native lock, an HMAC-SHA256 seal, a temporary file, an atomic replace, and a read-back. It reports success only after the read-back passes.

The store does not sit behind the portal yet. Routes do not call it in this change.

## File-by-File Change Map

| Path | Action | Content |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/models.py` | Delete | Replaced by `state/`. |
| `src/interfaces/portals/cisco_config_converter/state/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/state/intake.py` | Add | Moved `SourceConfiguration` and `ReviewState`. New `SourceRecord` and `ReviewRecord`. `REVIEW_LIFETIME`. |
| `src/interfaces/portals/cisco_config_converter/state/proposal.py` | Add | Moved `GatewayTemplate`, `UnsupportedItem`, and `ConversionProposal`. New `ProposalRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/approval.py` | Add | New `ApprovalRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/operation.py` | Add | New `OperationPhase` and `OperationRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py` | Add | New `BackupManifest`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/transitions.py` | Add | New `StateRefused` and `TransitionTable`. |
| `src/interfaces/portals/cisco_config_converter/state/storage/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/state/storage/store.py` | Add | New `PrivateStateStore` and `PersistenceUnavailable`. |
| `src/interfaces/portals/cisco_config_converter/state/storage/integrity.py` | Add | New `CanonicalDigest` and `RecordSeal`. |
| `src/interfaces/portals/cisco_config_converter/state/storage/redaction.py` | Add | New `SecretRedaction`. |
| `src/interfaces/portals/cisco_config_converter/state/storage/locks.py` | Add | New `NativeFileLock`. |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Modify | Import lines only. Inline comments on each touched line. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | Import line only. Inline comments on each touched line. |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Modify | Import line only. |
| `tests/integration/web_portal/cisco_config_converter/state/__init__.py` | Add | Package marker. |
| `tests/integration/web_portal/cisco_config_converter/state/test_state_records.py` | Add | Eleven record tests, including the structure test. |
| `tests/integration/web_portal/cisco_config_converter/state/test_state_transitions.py` | Add | Four transition tests. |
| `tests/integration/web_portal/cisco_config_converter/state/test_state_store.py` | Add | Eight store tests. |
| `tests/integration/web_portal/cisco_config_converter/state/test_state_multiworker.py` | Add | Two process tests. |

Unchanged paths: `web_portal/app.py`, `web_portal/templates/base.html`, `web_portal/services/config.py`, `compose.yml`, `.gitignore`, `requirements.txt`, and `documentation/`.

## Dependencies

- No package is added. No pin changes. `requirements.txt` stays unchanged.
- The store depends on the standard library only.
- The store reads `PORTAL_SECRET_KEY` from the environment. It does not change the shared fallback in `web_portal/services/config.py`, line 113.
- The store reuses the review digest form from `ReviewState.digest`. The two implementations must return the same value.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| The symbol gate reports `models.py` as removed. | The gate fails. | The symbol map above documents each name and its new path. The pull request body records the move. |
| A moved class keeps an old import somewhere. | An import error at run time. | The old-path search and the move guard run in T013. |
| Native lock behavior differs between Windows and POSIX. | A lock can block or leak. | The lock follows the firmware ownership pattern at `web_portal/routes/firmware_policy/jobs/ownership/__init__.py`, lines 35 to 68. Tests run on Windows and in CI. |
| Multiprocess tests are slow or flaky. | CI time grows or fails at random. | Each test uses `tmp_path`, a bounded lock timeout, and a fixed process count of two. SC-005 runs twenty times. |
| The shared secret fallback creates a random key. | Records become unreadable after a restart. | The store refuses writes when `PORTAL_SECRET_KEY` is unset. Decision D-15 governs the shared fallback. |
| Someone registers the blueprint without a handover. | Shared portal behavior changes. | FR-018 and the offline journey test check that no route registration exists. Integration needs issue 4633 handover. |
| Expired records accumulate on disk. | Disk use grows. | Each record is small. Decision D-9 defers any purge to an owner-approved task. |
| The digest form drifts from the review digest. | Existing review checks fail. | The first record test compares the new digest with `ReviewState.digest`. |

## Rollback Steps

1. Revert the squash commit with `git revert <commit>` on `main` through a pull request.
2. Confirm that `models.py` returns and that `state/` is gone.
3. Confirm that `tests/integration/web_portal/cisco_config_converter/test_routes.py` passes.
4. Remove `data/cisco_config_converter/state/` only if a test or a manual run created it. The store creates no file when production writes stay disabled.

Rollback is safe because no production record exists. The store stays disabled until owner approval.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `src/interfaces/portals/` has six physical children. | Grandfathered, not touched | Predates this change. | Remediation action R-1 in `analysis.md`. |
| `tests/contract/` has 17 children. | Grandfathered, not touched | Predates this change. | The tests use the integration tree instead (decision D-2). Remediation action R-2 in `analysis.md`. |
| `tests/e2e/web_portal/` has 32 children. | Grandfathered, not touched | Predates this change. | Task T029 owner must choose a compliant path. Remediation action R-3 in `analysis.md`. |
| `models.py` holds five top-level classes. | Grandfathered, removed | The file reaches the limit. | Replaced by `state/` in this change. |
| `state/` package | New design | Compliant with five children. | None. |

This change adds no violation. It removes the five-class `models.py` module from the at-limit list.
