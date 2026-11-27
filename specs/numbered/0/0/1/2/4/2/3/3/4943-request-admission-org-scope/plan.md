# Implementation Plan: Ship the preserved admission scope work

**Branch**: `fix/4943-request-admission-org-scope` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The preservation branch holds a repair for the defect in issue #4921 and two hardening changes. The repair attributes each site request to an organization scope. The hardening changes hide frame locals, remove ANSI escape sequences from non-terminal output, and mute the duplicate SDK error lines of the MSP organization list. This plan ships those changes from the current `main`. It also restructures the branch code into named classes, adds the missing log lines, and replaces one weak assertion.

## Technical Context

**Language/Version**: Python 3.15. `pyproject.toml:23` requires `>=3.15`.

**Primary Dependencies**: mistapi 0.64.1 (`requirements.txt:129`), rich 15.0.0 (`requirements.txt:233`), and structlog 26.1.0 (`requirements.txt:249`). The change adds no dependency.

**Storage**: Redis for the shared admission keys. The Redis connection starts in `RequestLedger.connect` (`request_admission.py:61` on main). The change adds no database schema.

**Testing**: pytest with a fake Redis client and fake SDK doubles. The local gates table starts at `.github/copilot-instructions.md:50`.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. The repository guide names all four platforms.

**Project Type**: Library code in the `src` packages, two unit test modules, one operator guide line, and one changelog fragment.

**Performance Goals**: None. A site request in a scope costs one context-variable set and one reset. An MSP call costs one logger filter attach and one removal.

**Constraints**:

- Five-item rule (constitution Principle I).
- Class-based code (Principle II).
- ASCII log output (Principle V).
- Inline comments (Principle VI).
- Action logging (Principle VII).
- Function limits: 25 lines, five parameters, and five logical blocks.

**Scale/Scope**: Four existing modules, one new module, two test modules, one operator guide line, one changelog fragment, and this record.

## Constitution Check

*Gate: passes before research. The check passes after the repairs in T008 to T011. The preservation branch fails rules I, II, VI, VII, and the test quality ratchet until those tasks finish.*

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-item rule, module names | Pass after repair. Fail on the branch. | The branch gives `request_admission.py` seven top-level names and `client.py` nine. The repair gives four and five. |
| I. Five-item rule, package children | Pass. | The package `subscription_expiry` holds four tracked children. The new module makes five. |
| I. Five-item rule, record folders | Pass. | The record root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`. The `design` folder holds five children. Each other folder holds fewer. |
| I. Existing function violations | Recorded. | On main, `_discover_msp` spans 59 lines and `_expand_virtual_chassis_members` spans 32 lines. `RequestLedger.admit` spans 28 lines. The branch changes these to 61, 33, and 25 lines. Remediation action RA-1 owns the two long methods. |
| II. Class-based code | Fail on the branch. Pass after repair. | The branch adds the module-level functions `organization_scope`, `_credential_fingerprint`, `_authentication_header`, and `_sdk_error_lines_muted`. The repair moves them into `OrganizationScope`, `RequestLedger`, and `SdkErrorLineMute`. |
| III. Safety first | Pass. | The fingerprint stays. The repair adds an empty identifier refusal (FR-008). No credential reaches a log line or a rendered frame local. |
| IV. Full deployment pipeline | Pass with tasks. | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. T-MERGE covers the main build and the image revision check (steps 10 and 11). Step 12, deploy and health check, needs the orchestrator. |
| V. Logging | Pass. | The new warning text uses ASCII only. The change adds no Unicode output. |
| VI. Inline comments | Fail on the branch. Pass after the audit. | Some continuation lines on the branch have no comment, for example the arguments of the `ContextVar(` call in `request_admission.py`. T008, T010, and T011 add a comment to each changed line. |
| VII. Action logging | Fail on the branch. Pass after T008. | The MSP organization list call has no info line before it and no debug line after it. T011 adds both lines in `_fetch_msp_listing`. |
| Mist transport | Pass. | Both calls use existing mistapi methods. The change adds no HTTP request. The section Mist Cloud Transport Requirements in `spec.md` names both methods. |
| Output backends | Not applicable. | The change writes no export file. |
| Operational store | Not applicable. | The change adds no coordination record. |
| Database keys | Not applicable. | The change adds no endpoint and no table. The shared admission key names stay unchanged. |
| Data directory | Not applicable. | The change writes no product output. |
| Container and proxy rules | Not applicable. | The change builds no container and starts no test container. |
| Menu operations | Not applicable. | Menu 308 exists. The change adds no menu and no registry row. |
| Testing | Pass after T005 and T006. | Twelve test functions cover FR-004 to FR-020. The red run in T007 proves the repairs. |
| Security findings | Pass. | The change adds no suppression comment. |
| Release notes | Pass after T013. | One fragment follows the naming rule in `changelog.d/README.md:19-26`. |
| Audience standard | Pass. | The warning text uses plain words for a junior operator. |
| Complexity escalation | Pass. | The change touches more than three files, so this record exists. |
| Multi-agent git | Fail until T002 passes. | PR #4208 is an open draft that changes `request_admission.py` and the admission test. AGENTS forbids two open pull requests on one file. |
| Test quality ratchet | Fail on the branch. Pass after T009. | The branch adds one new finding. It is `weak_is_not_none` at `test_request_admission.py:141`. The issue comment reports it. |

For repository structure and generated files:

- The first commit of the ship branch adds only the record (FR-029).
- The commit subject and the pull request title use Conventional Commits, for example `fix(request-admission): attribute site reads to their organization`.
- The changelog fragment is one file under `changelog.d/` (FR-027).
- The change writes no product output under `data/`.

For a feature that uses Juniper Mist Cloud:

- Each REST call uses a working mistapi method (FR-025).
- The change adds no owned WebSocket transport.
- Contract tests: `tests/integration/test_mistapi_sdk_compatibility.py`, which exists on main at blob `cab2d602113012729f6c392dff43197d05913a38`, and the fake SDK test `test_virtual_chassis_read_is_admitted_under_its_organization`.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      admission-scope.md
      operator-messages.md
      mist-calls.md
    checklists/
      requirements.md
      security.md
      gates.md
```

### Source Code (repository root)

```text
src/
  foundation/support/utils/logger_utils.py                        (modify)
  interfaces/wan_performance/collection/request_admission.py      (modify)
  mist/intelligence/reports/subscription_expiry/
    client.py                                                      (modify)
    sdk_error_lines.py                                             (add)
tests/
  unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py  (modify)
  unit/wan_dashboard/wan_performance/collection/test_request_admission.py                    (modify)
documentation/operator-guide.md                                    (modify)
changelog.d/issue-4943-request-admission-org-scope.md              (add)
```

**Structure Decision**: The change modifies four existing source and test modules and adds one module. The new module `sdk_error_lines.py` sits in the existing `subscription_expiry` package. The package then holds five tracked children, which is the limit.

## Change Map

| Path | Action | Change |
|------|--------|--------|
| `src/interfaces/wan_performance/collection/request_admission.py` | Modify | Replace the module-level context variable, `organization_scope`, `_credential_fingerprint`, and `_authentication_header` with `class OrganizationScope`. The class holds the context variable as a class attribute. Its static method `block(org_id)` is the context manager, and its static method `current()` returns the active value. Move the two credential helpers into `RequestLedger` as private static methods. Refuse an empty identifier in `block`. Keep the attribution rules of `_organization` (FR-004, FR-005, FR-009). Top-level names after the change: `logger`, `OrganizationScope`, `RequestLedger`, `AdmittedAdapter`. |
| `src/foundation/support/utils/logger_utils.py` | Modify | In `console_formatter()`, pass `color_system="truecolor" if supports_color else None` to `structlog.dev.RichTracebackFormatter`. Keep `show_locals=False` (FR-012, FR-013). |
| `src/mist/intelligence/reports/subscription_expiry/sdk_error_lines.py` | Add | Add the class `SdkErrorLineMute` with the constant `SDK_LOGGER_NAME = "mistapi"`, a nested filter class that drops records at ERROR level or above, and the static method `muted()`. The method attaches the filter, yields, and removes the filter in a `finally` block (FR-016, FR-017). |
| `src/mist/intelligence/reports/subscription_expiry/client.py` | Modify | Move `HTTP_FORBIDDEN` into `SubscriptionExpiryClient` as a class attribute. Remove `_SkipSdkErrorRecords` and `_sdk_error_lines_muted`. Add `_fetch_msp_listing(msp_id)`, which holds the mute, the info line, the SDK call, and the debug line. Keep `_warn_msp_list_failed` and the failure row (FR-015, FR-019). Wrap the VC read in `OrganizationScope.block` (FR-014). Top-level names after the change: `logger`, `HTTP_BAD_REQUEST`, `JsiAccountNotLinkedError`, `SubscriptionExpiryClientError`, `SubscriptionExpiryClient`. |
| `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` | Modify | Import `OrganizationScope` in place of `organization_scope`. Replace the assertion at line 141 with a type check (FR-022). Add `test_nested_organization_scope_restores_outer_value`, `test_organization_scope_resets_after_exception`, `test_organization_scope_rejects_empty_identifier`, and `test_console_renderer_output_has_no_ansi_on_non_terminal` (FR-006, FR-007, FR-008, FR-013). |
| `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` | Modify | Add `test_transport_failure_keeps_the_client_error_line` and `test_msp_listing_logs_info_before_and_debug_after` (FR-018, FR-020). Keep the existing branch tests (FR-014 to FR-017, FR-019). |
| `documentation/operator-guide.md` | Modify | At line 502, replace "uses one organization" with "continues with direct organizations" (FR-026). |
| `changelog.d/issue-4943-request-admission-org-scope.md` | Add | Add one `###` heading. Add one bullet each for `Fixed` and `Security`. Name issues #4921 and #4943 in the bullets (FR-027). |
| `specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/` | Add | Copy the record from the draft folder into the repository in the first commit (FR-029). |

## Design

### Organization scope

`OrganizationScope.block(org_id)` refuses an empty identifier. It saves the current value, sets the new value, yields, and restores the saved token in a `finally` block. Nested blocks restore the outer value because each block keeps its own token. `OrganizationScope.current()` returns the active value or `None`.

### Shared admission attribution

One rule changes. A site request with no ledger organization takes its organization from `OrganizationScope.current()`. When that value is `None`, the ledger raises the existing message. Organization paths and ledger organizations keep their attribution.

### Traceback rendering

The console formatter keeps `show_locals=False`. It adds an explicit `color_system`. A terminal stream gets `truecolor`, and any other stream gets `None`. The structlog default switches to a monochrome formatter when `colors` is false. A custom formatter bypasses that switch (`.venv\Lib\site-packages\structlog\dev.py:713-714`). Rich writes style codes whenever its color system holds a value (`.venv\Lib\site-packages\rich\console.py:2136-2144`).

### MSP organization list

`_fetch_msp_listing(msp_id)` holds the info line, the mute, the SDK call, and the debug line. `_discover_msp` calls that method and keeps the failure handling. The change keeps every method at or below the length of its main version, except for the two methods in RA-1.

### Mute scope

The mute attaches one filter to the `mistapi` logger object for one call. The filter drops ERROR records only. The `finally` block removes the filter. Records from other loggers pass unchanged, because the client logs transport failures on its own logger (`client.py:40-57` on main).

## Dependencies

- PR #4208 must land or release `request_admission.py` and its admission test first (FR-002). Its head at commit `843be63bc837513b4442dae69da9f0db922e0ed1` holds the file at blob `4cf92ab977bb667ef0fe4e72de68994a80f1ffea`.
- The mistapi pin stays at 0.64.1.
- The change adds no package.

## Risks and Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R-1 | PR #4208 changes `request_admission.py` by 193 insertions and 75 deletions, and it moves the admission test to `tests/unit/wan_performance/test_request_admission.py`. A cherry-pick conflicts. | High | High | Start from the post-#4208 main. Apply the design by hand in T005. Do not cherry-pick. |
| R-2 | The admission test path `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` no longer exists after PR #4208 lands. | High | Medium | Move the four new tests and the type check to the new path in T005 and T008. Record the path move in the pull request body. |
| R-3 | The explicit color system changes terminal output. | Low | Low | The terminal path keeps `truecolor`. Terminal output keeps its colors. |
| R-4 | A new import path breaks a caller. | Low | Medium | T-LOCAL-GATES runs the pytest modules that import each changed module, and the full test run follows. |
| R-5 | The SDK error line filter drops another thread's SDK error line during the MSP call. | Low | Low | No report path starts a thread (`design/research.md`, section Method). The filter lives for one call. `sdk_error_lines.py` documents the process-wide effect. |
| R-6 | The `mist` package imports from `interfaces`. | Certain | Low | Precedent exists in `src/mist/intelligence/troubleshooting/synthetic_test_trigger/operation.py:16` and `src/mist/resources/device/client_session_control/handler.py:12`. Decision D-3 accepts the import. |
| R-7 | The red run cannot show failures for the repair tests, because the branch already holds part of the repair. | Medium | Low | T007 runs before T008 to T011. It expects failures for `test_organization_scope_rejects_empty_identifier`, `test_console_renderer_output_has_no_ansi_on_non_terminal`, and `test_msp_listing_logs_info_before_and_debug_after`. Regression guards pass. |
| R-8 | A live run of menu 308 differs from the unit doubles. | Medium | Medium | Run the live check after the merge (decision D-13). The warning text stays fixed. |

## Remediation Actions

- **RA-1**: Split `_discover_msp` and `_expand_virtual_chassis_members` into methods of 25 lines or fewer. Open a separate issue after the merge. The issue names the two methods and their main lengths.
- **RA-2**: Move `RequestLedger` into its own module, because `request_admission.py` also holds the adapter. Open a separate issue after the merge.
- **RA-3**: Remove the menu 309 `AdmissionBinding` workaround in `src/operations/exporting/ex_hardware_inventory/scope/session.py:25` and its use in `run/batch.py:199` and `run/batch.py:223`. Open a follow-up issue (decision D-5).
- **RA-4**: Correct the layout list in `documentation/architecture.md:202-207`. The list names `api/`, and `src/api/` does not exist on main. Open a documentation issue.
- **RA-5**: Correct the mistapi lower bound in `pyproject.toml:29` or the repository guide, because the two sources disagree (`.github/copilot-instructions.md`, section Language and environment).

## Rollback

1. Before the merge, close the pull request and keep the preservation branch. The branch keeps the five files.
2. After the squash merge, open a pull request on `main` that reverts the squash commit. The revert restores the previous admission behavior in one commit.
3. To restore the preserved state later, create a new branch from `main` and apply commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f`.
4. The revert pull request keeps the changelog fragment. The release coordinator removes the fragment with the release.

## Complexity Tracking

| Kind | Violation | Why needed | Simpler alternative rejected because |
|------|-----------|------------|--------------------------------------|
| Grandfathered, touched | `_discover_msp` spans 59 lines on main and 61 on the branch. The change keeps it near its main length. | The method holds the MSP call, the failure row, and the page loop. | Splitting it in this change adds a second concern. RA-1 owns the split. |
| Grandfathered, touched | `_expand_virtual_chassis_members` spans 32 lines on main and 33 on the branch. | The method holds the VC loop, and the change adds one scope line. | Splitting the loop in this change adds a second concern. RA-1 owns the split. |
| New design | The scope primitive stays in `interfaces` and `mist` imports it. | Shared admission already lives in `interfaces` on main. | Moving the primitive to `foundation` touches four more files and creates a module. Decision D-3 rejects that move. |
