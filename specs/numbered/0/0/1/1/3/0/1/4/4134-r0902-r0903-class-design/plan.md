# Implementation Plan: R0902 and R0903 class design

**Branch**: `chore/4134-r0902-r0903-class-design` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\1\3\0\1\4\4134-r0902-r0903-class-design\spec.md`

**Input**: Numeric specification from `specs\numbered\0\0\1\1\3\0\1\4\4134-r0902-r0903-class-design\spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design\`. No contract folder applies (see Contracts below).

## Summary

Resolve six R0903 findings by adding six public methods. Each method names logic that its class already performs. Record the other 19 findings in an exception register with one reason each. The change touches four source modules, four test modules, and one release-note fragment. It makes no behavior change.

## Technical Context

**Language/Version**: Python 3.15 or newer. The repository file `.github\copilot-instructions.md` states this (research row RC-33).

**Primary Dependencies**: None added. Installed in `.venv`: pylint 4.1.4 (research rows RC-57 to RC-59) and mistapi 0.64.1 (research row RC-56).

**Storage**: No storage change. `PersonalDataRetention` keeps its existing output folder and file names.

**Testing**: pytest through `python -m pytest <file>`, as the Tests row of the Local gates table states (research row RC-33).

**Target Platform**: Windows 11, macOS, and Linux, as `.github\copilot-instructions.md` states (research row RC-33).

**Project Type**: Single Python project with `src/`, `web_portal/`, and `tests/`.

**Performance Goals**: None set. Each new method adds one function call on an existing path. No measurable change is expected.

**Constraints**: No behavior change. Five-item rule. No new module or directory. No pylint pragma.

**Scale/Scope**: Four source files, four test modules, and one fragment.

## Constitution Check

*Gate: must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | No directory or module is added. Each change adds one method to an existing class. |
| I. Existing violations recorded | Pass | The register in `design\research.md` records the 19 remaining findings. Analysis records three follow-ups. |
| II. Class-based architecture | Pass | Each new method lives in an existing class. No wrapper function is added. |
| III. Safety-first | Pass | The change does not alter input handling, destructive confirmations, or secrets. The retention cutoff keeps its arithmetic. |
| IV. Full deployment pipeline | Pending | Gates run in T-LOCAL-GATES. Pull request, CI, and merge run in T-PR, T-REMOTE-CI, and T-MERGE. |
| V. Observability | Pass | Added log text is ASCII. No secret value appears in a log line. |
| VI. Inline comments | Pass as planned | Each new executable line carries a same-line comment that gives the reason. |
| VII. Action logging | Pass as planned | `to_tickets` logs before and after its work. Pure checks and arithmetic log nothing. |
| Mist SDK rule | Pass | No REST call changes. `listOrgTickets` stays the SDK call (research row RC-56). |
| File paths | Pass | No new path is built. Each module keeps its current path handling. |
| Output backends | Not applicable | The export writer is not changed. |
| Test containers | Not applicable | No container starts for this change. |
| Security findings | Pass | No suppression is added. No security finding is touched. |
| Release notes | Pass | One fragment is added (decision D-11). The conflict with changelog README rule 4 is recorded. |
| Menu operations | Not applicable | No menu row, menu entry, or registry entry changes. |
| Multi-agent git | Pass as planned | Branch `chore/4134-r0902-r0903-class-design`. Label `in-progress`. The changed-file list is checked before push. |

## Architecture

No directory is added. Four modules gain one method each. Each method is a named step that the existing code already performs inside `load`, `refusal_message`, `acquire`, `authorization_header`, `purge`, or `read`.

The register of 19 recorded exceptions stays in `design\research.md`. Each row names its file, class, finding, count, decision, and reason.

## Method Designs

| Class | New public method | Behavior | Existing caller |
| - | - | - | - |
| `JuniperSettingsLoader` | `missing_names(self, needs_contact_email: bool = True) -> list[str]` | Return the required names that hold no value, in the required order. | `load` |
| `JuniperLiveCallGuard` | `is_automated_run(cls, argv: list[str] | None = None) -> bool` | Return True when a test flag is in argv or runtime test mode is set. | `refusal_message` |
| `RequestRateLimiter` | `refill(self) -> float` | Add the tokens earned since the last refill, cap the level at 1.0, and return the level. | `acquire` |
| `JuniperTokenProvider` | `is_fresh(self) -> bool` | Return True when a token is cached and the clock is before the expiry time. | `authorization_header` |
| `PersonalDataRetention` | `cutoff(self, now: float | None = None) -> float` | Return the epoch time before which exports are expired. | `purge` |
| `MistTicketReader` | `to_tickets(self, rows: list[Any]) -> list[MistTicket]` | Convert object rows to tickets in order and drop other items. | `read` |

`load` keeps its log lines and its error text. `refusal_message` keeps the environment opt-in check. `acquire` keeps its wait logic. `authorization_header` uses the condition `force_refresh or not self.is_fresh()`, which equals the current condition. `purge` keeps its file loop and its log lines. `read` keeps its SDK call and its debug line.

## Logging Decision

`to_tickets` is a data transform. It logs an info line before the conversion and a debug line after it, with counts only. The other new methods are pure checks or arithmetic, so they log nothing. This follows AGENTS.md action logging (research row RC-37).

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `src/operations/exporting/juniper_rma/settings.py` | Modify | Add `JuniperSettingsLoader.missing_names` and `JuniperLiveCallGuard.is_automated_run`. Update `load` and `refusal_message` to call them. |
| `src/operations/exporting/juniper_rma/api/gateway.py` | Modify | Add `RequestRateLimiter.refill` and `JuniperTokenProvider.is_fresh`. Update `acquire` and `authorization_header` to call them. |
| `src/operations/exporting/juniper_rma/model/export_rows.py` | Modify | Add `PersonalDataRetention.cutoff`. Update `purge` to call it. |
| `src/operations/exporting/juniper_rma/workflows/correlation.py` | Modify | Add `MistTicketReader.to_tickets`. Update `read` to call it. |
| `tests/unit/juniper_rma/api/test_settings.py` | Modify | Add TS-01 to TS-06. |
| `tests/unit/juniper_rma/api/test_gateway.py` | Modify | Add TS-07 to TS-11. |
| `tests/unit/juniper_rma/model/test_export_rows.py` | Modify | Add TS-12 and TS-13. |
| `tests/unit/juniper_rma/workflows/test_correlation.py` | Modify | Add TS-14 and TS-15. |
| `changelog.d/issue-4134-r0902-r0903-class-design.md` | Add | One fragment for the change. |
| `MistHelper.py` | No change | Recorded exceptions only. |
| `web_portal/services/operation.py` | No change | Recorded exception only. |
| Other files in the register | No change | Recorded exceptions only. |
| Menu wiring and generated documentation | No change | No menu text changes. |

No file is deleted.

## Contracts

No contract folder applies. The new methods are in-process Python methods. The change alters no menu, CLI output, export column, API request, or API response shape.

## Data Model

Not applicable. See `design\data-model.md`.

## Dependencies

- Order of work: test-first tasks, then implementation tasks, then the fragment, then the register check, then the final tasks.
- File-level order: `settings.py` (T002 then T004), `gateway.py` (T007 then T008), `export_rows.py` (T010), and `correlation.py` (T012).
- External dependency: the changelog guard test (research row RC-50) must pass.
- No new package. No change to `requirements.txt` or `requirements-dev.txt`.

## Risks and Mitigations

- **R1**: Caution: a changed token boundary can send a request too early or too late. A 401 reply forces a token refresh (`gateway.py` comment at line 88), so the error is recoverable. Mitigation: TS-09 to TS-11 pin the boundary.
- **R2**: Caution: a changed refill can exceed the configured request rate. The API can then throttle the run. Mitigation: TS-07 and TS-08 pin the arithmetic and the cap.
- **R3**: Warning: a wrong cutoff deletes exports that the retention window keeps. Deleted files cannot be restored. Mitigation: TS-12 and TS-13 pin the arithmetic, and `purge` calls the same method.
- **R4**: Caution: a changed settings check can let a missing name reach the loader. `load` still raises before any network call. Mitigation: TS-01 to TS-03.
- **R5**: Caution: the register can drift when `main` moves. Mitigation: T014 repeats the scan, and TS-16 compares the output with the register.
- **R6**: Caution: the new debug and info lines in `to_tickets` change the log output. The log lines carry counts only and no secret. Mitigation: the lines are ASCII.

## Rollback

Revert the squash commit on `main`. The change writes no data, changes no configuration, and generates no file. The revert removes the fragment with it.

## Complexity Tracking

| Item | Grandfathered or new | Why kept | Remediation |
| - | - | - | - |
| Register rows 1 to 19 | Grandfathered debt | Recorded exception, with the reason in `design\research.md` | Follow-ups F-1, F-2, and F-3 cover four rows: 1 (F-1), 2 and 3 (F-2), and 17 (F-3). The other rows keep their reasons. |
| New design | None | Not applicable | Not applicable |

## Unresolved Items

- Follow-ups F-1, F-2, and F-3 are proposed in `analysis.md`. The orchestrator files them.
