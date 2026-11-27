# Implementation Plan: MSP Profile Lookup Failure

**Branch**: `fix/4713-msp-profile-lookup-failure` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/3/2/3/4713-msp-profile-lookup-failure/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

A refused profile lookup returns an empty grant list. Menu 13 reads an empty grant list as confirmed absence and calls the single-organization callback. This plan adds a lookup result that separates a failed lookup from confirmed absence. The detector checks the status and the body. Menu 13 makes one live lookup when its grant list is empty. It calls the single-organization callback only after confirmed absence. The change touches two source modules, two test modules, two operator pages, and one changelog fragment.

## Technical Context

**Language/Version**: Python 3.15 or newer (`.github/copilot-instructions.md`, line 19, RC-60 context).

**Primary Dependencies**: mistapi 0.64.1, which satisfies `mistapi>=0.64.0,<0.65` (RC-63, RC-56). No new dependency.

**Storage**: None. The change writes no file.

**Testing**: pytest with mocked SDK responses. The detector test module has an autouse fixture that restores the mistapi modules. The change reuses that fixture.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. The unit tests run on the host. No container starts for this change.

**Project Type**: A bug fix in one menu operation (menu 13) and in its shared detector.

**Performance Goals**: Menu 13 with an empty grant list makes one more profile API call. Other paths make no extra call.

**Constraints**: Functions keep five parameters or fewer, five logical blocks or fewer, and 25 lines or fewer (`AGENTS.md`, Structure, RC-57 context). Each touched line gets an inline comment and action logging (`AGENTS.md`, Inline comments and Action logging). Log text stays ASCII (constitution Principle V).

**Scale/Scope**: Two source modules, two test modules, two operator pages, and one changelog fragment.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Evidence |
| - | - | - |
| I. Five-item rule | No directory gains a child. A touched function meets the 25-line limit. | No new file and no new folder. `detect_msp_privileges` spans 35 lines today (RC-01). After the change it delegates in one statement. |
| II. Class-based, no wrappers | Behavior lives in named units. A delegating function needs a recorded reason. | `detect_msp_privileges` delegates to `lookup_msp_privileges`. Complexity Tracking records the reason. |
| III. Safety first | No new input. No secret in output. | FR-013 and SC-006. The live lookup reads the session that the existing configure call stores (RC-08, RC-09). |
| IV. Full deployment pipeline | Gates run. The change lands through a pull request. | `tasks.md`, tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. |
| V. Observability | ASCII text. Standard levels. No secret in logs. | New messages use `%s` arguments and plain ASCII. |
| VI. Inline comments | Each touched line gets a comment that gives the purpose. | Review gate in T006, T007, and T010. |
| VII. Action logging | Info before and debug after each action. | The live lookup and each detector step log both lines. |
| Mist Cloud, REST | Every REST call uses a working mistapi method. | `mistapi.api.v1.self.self.getSelf` (RC-51, RC-52). |
| Mist Cloud, owned transport | None owned. | Mist Cloud Transport Requirements in `spec.md`. |
| Database keys | Not applicable. No stored data. | None. |
| Data directory | Not applicable. No product output. | None. |
| Hot files | `MistHelper.py` stays unchanged. The #4708 files need a release first. | Gate T001. RC-19 to RC-21 show the MistHelper calls that stay unchanged. Constitution hot-file rule (RC-66). |

Repository structure and generated files:

- The commit subject and the pull request title use `fix(msp): stop menu 13 after a refused profile lookup`, which the title check accepts.
- The change adds one changelog fragment. It adds no direct child to a process folder.
- Test output uses `tmp_path`. No output enters `data/` or `test-artifacts/`.

## Research Summary

`design/research.md` holds decisions D-1 to D-6, the linked work, and the remote evidence. The key facts follow.

- The defect sits in `_msp_fetch_user_data`. It reads `response.data` and never checks the status (RC-02, RC-03, RC-04).
- The SDK sets `status_code` and keeps the error body in `data`, so a 403 reaches the detector as a dict (RC-53, RC-54, RC-55). The OpenAPI 403 body has a `detail` string (RC-44, RC-45).
- Menu 13 reads only the grant list. It calls the single-organization callback when the list is empty (RC-10).
- Other readers of the grant list (RC-14 to RC-25) keep their current behavior. Follow-up issues cover them.

## Design

### Detector: `src/foundation/support/refactors/msp_privilege_detection.py`

1. `_msp_fetch_user_data(session)` keeps its name and its return type, `dict | None`. It adds two checks before it returns the body:
   - The status must be an `int` from 200 through 299. Otherwise it logs a warning with the status and returns None.
   - The body must hold a `privileges` list. Otherwise it logs a warning and returns None.
2. `MspPrivilegeLookup` is a frozen dataclass with two fields: `succeeded: bool` and `grants: list[dict[str, Any]]`.
3. `lookup_msp_privileges(session)` returns the lookup result:
   - A missing session logs a warning and returns a failed lookup. It makes no API call.
   - The call to `_msp_fetch_user_data` runs inside a try block. An exception logs the class name only and returns a failed lookup.
   - A None body returns a failed lookup. The fetch already logged the reason.
   - A valid body returns a valid lookup with the grants from `_msp_extract_from_user_data`.
4. `detect_msp_privileges(session)` returns `lookup_msp_privileges(session).grants`. The module docstring and the function docstring name both entry points, so a reader knows when to use each.

### Dispatch: `src/mist/resources/inventory/org_device_inventory_msp.py`

1. Import `lookup_msp_privileges` from `src.foundation.support.refactors.msp_privilege_detection`.
2. Add two constants next to `_NO_MSP_MSG` (RC-07 context): `_LOOKUP_FAILED_MSG` and `_RESTART_FOR_GRANTS_MSG`.
3. Add the private module helper `_confirm_no_msp_access() -> bool`:
   - It logs info before the live lookup.
   - It calls `lookup_msp_privileges(apisession)`. The global `apisession` comes from the facade (RC-12).
   - It logs debug with the outcome.
   - A failed lookup prints `_LOOKUP_FAILED_MSG` and returns False.
   - A valid lookup with grants prints `_RESTART_FOR_GRANTS_MSG` and returns False.
   - A valid lookup with zero grants returns True.
4. `dispatch` keeps its signature. When the grant list is empty, it calls `_confirm_no_msp_access()`. It calls `single_org_fn()` only when the helper returns True. It returns in both cases (RC-10, RC-11).

Operator messages are ASCII and appear in `design/contracts/menu-13-dispatch.md`.

### Documentation

- `documentation/wiki/MSP-Support.md`: add one sentence to the detection bullet at line 116 (RC-35).
- `documentation/operator-guide.md`: add one paragraph after line 594 (RC-36). Change no heading. `tests/guardrails/test_hardware_shell_lock_docs.py` links an anchor in that file (RC-34).
- `changelog.d/issue-4713-msp-profile-lookup-failure.md`: add one fragment with one `###` heading and one `Fixed` bullet that names Issue #4713. The name follows the issue-only rule (RC-72).
- `documentation/menu-api/interactive.md`: no manual change. Commit a regenerated page only when the menu reference generator changes it.

## File Change Map

| Path | Action | Reason |
| - | - | - |
| `src/foundation/support/refactors/msp_privilege_detection.py` | modify | Status and body checks. `MspPrivilegeLookup` and `lookup_msp_privileges`. `detect_msp_privileges` delegates. |
| `src/mist/resources/inventory/org_device_inventory_msp.py` | modify | Live lookup before the empty-grant branch. Two messages. |
| `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py` | modify | Fixtures model status 200. New lookup cases. |
| `tests/unit/inventory/test_org_device_inventory_msp.py` | modify | Dispatch cases for the live lookup. |
| `documentation/wiki/MSP-Support.md` | modify | Detection bullet. |
| `documentation/operator-guide.md` | modify | One paragraph. No heading change. |
| `changelog.d/issue-4713-msp-profile-lookup-failure.md` | add | Release-note fragment. |

Checked by reading and not changed:

- `MistHelper.py`, `src/foundation/support/refactors/main_entrypoint.py`, and `src/foundation/runtime/config/source_dependency_resolver.py`. The startup and context code stays as is (RC-19 to RC-23).
- `src/mist/resources/inventory/org_device_inventory_summary_facade.py`. The facade already passes the session and the grant list (RC-12, RC-13).
- `src/operations/exporting/export/msp_inventory_exporter.py` (issue #4762), `src/mist/access/auth/interactive/login_orchestrator.py`, and `src/foundation/support/refactors/initialize_mist_session_interactive.py`. They call the list view (RC-14 to RC-18).
- `src/operations/exporting/export/org_config_exporter.py` and `src/operations/execution/firmware/firmware_manager.py`. Out of scope (RC-24, RC-25).
- `documentation/mist-api-openapi31yaml.yaml` and the installed mistapi package. Read only.

## Dependencies

- **File hold**: Issue #4708 (in progress) owns `org_device_inventory_msp.py` and its test module (RC-07, RC-29). Gate T001 requires its release before T005 and T007.
- **Open pull requests**: A scan of the seven open pull requests on 2026-11-26 found no overlap with the change map. PR #4208 touches `src/foundation/support/refactors/initialize_mist_session.py`, which this change does not edit.
- **Related record**: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` avoids the detector for this defect (RC-83). This change does not alter that record.
- **Tools**: The local gates in `.github/copilot-instructions.md` (RC-60). No new tool.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| Menu 13 makes one more API call for organization-only accounts. | Low. One call per run. | The live lookup runs only when the grant list is empty. The rate-limit rule in `AGENTS.md` applies. |
| Operators see a failure message while Mist refuses the lookup. | Medium. Menu 13 does not run. | The message names the cause. The next run repeats the lookup. Caution: a failed lookup blocks only the run that failed. |
| #4708 changes the same orchestrator file. | Medium. Merge conflict. | Gate T001. Rebase onto `main` before push (`AGENTS.md`, Branch). |
| Callers outside menu 13 still read a failure as no access. | High for those paths. | Out of scope. Follow-up issue (T011). The operator guide paragraph (T008) explains the warning. |
| A 2xx body without `privileges` becomes a failed lookup. | Low. Blocks menu 13 on schema drift. | Contract tests pin the rule. The warning names the cause. |
| Existing fixtures omit the status code and then fail. | Low. Test work only. | T004 updates the fixtures before the implementation. |
| The safe sweep runs menu 13 without a token. | Low. The menu prints a new message. | T-LOCAL-GATES runs the sweep and records the menu 13 line. |

## Rollback

1. Revert the squash commit with a new pull request. No data changes.
2. Remove the changelog fragment in the same revert.
3. No persistent state changes, so no data repair runs.

## Complexity Tracking

| Violation or exception | Why it is needed | Simpler alternative rejected because |
| - | - | - |
| `detect_msp_privileges` delegates to `lookup_msp_privileges` (Principle II). | Seven callers keep the list contract. One of them sits in `MistHelper.py`, which hot-file rules protect (RC-19, RC-20). | Changing every caller touches `MistHelper.py` and the exporter. Both have an owner in progress or a hot-file rule. |
| The dispatch helper is a module function, not a class method. | The orchestrator module uses module helpers and constants throughout (RC-07, RC-08). | A new class adds one method and no state. |
| `detect_msp_privileges` exceeds 25 lines today (RC-01). | This change moves its logic out. | Not a new violation. The change removes it. |
| Existing debt in `MistHelper.py` (8,373 lines, RC-19 context) and `org_device_inventory_msp.py` (551 lines, RC-07 context). | Existing debt, not part of this change. | Not changed here. Separate remediation issue. |
