# Implementation Plan: Site Request Admission by Organization

**Branch**: `fix/4921-site-request-admission` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification from `specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission\spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design\`. Each directory holds five children or fewer.

## Summary

`RequestLedger` (`request_admission.py`) refuses a site request when no organization is set. The CLI never sets one, so the batch workers wrap their work in `AdmissionBinding`. This plan makes the ledger resolve the organization of each site itself. It learns the site-to-organization pairs from each successful organization listing. For a site that no listing returned, it uses the cached session organization. When neither applies, it refuses the request as before. The binding and its call sites are removed.

## Technical Context

**Language/Version**: Python 3.15. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: `mistapi` 0.64.1 (`requirements.txt` line 129, installed `mistapi-0.64.1.dist-info` line 3). `requests` (adapter base class), `redis` (store client). No new dependency.

**Storage**: None. The site organization map is in memory. It lives with one `RequestLedger` object.

**Testing**: `pytest`. The new tests use a fake Redis client and invented identifiers. The gates in `design\quickstart.md` apply.

**Target Platform**: Windows 11, macOS, and Linux. The product runs in the Podman image. This change adds no image layer.

**Project Type**: One Python package with a CLI and a web portal.

**Performance Goals**: No added Mist request. Each map read and write holds one lock for one lookup or one page of entries.

**Constraints**: Fail closed for an unknown organization. No prompt inside the transport. Quota numbers stay unchanged. Memory stays bounded at 50,000 map entries.

**Scale/Scope**: One organization per batch run. A multi-organization (MSP) session can list many organizations, so the map can hold up to 50,000 entries.

## Constitution Check

*Gate result: pass. Each rule below has a result and a reason.*

### Structural rules (Principle I)

- **Five-item rule**: Pass. The record path uses the managed root `numbered` (`process_folder_baseline.json` line 7). The route is the fixed base-5 route of 4921 (`spec-route.ps1` line 17). Each directory holds five children or fewer. The change adds one changelog fragment, which is a unique record in an allowed process folder.
- **Function limits**: Pass by design. The new functions take at most five parameters. Each new method holds at most five logical blocks and about 25 lines. Helpers split the learning step.
- **Existing debt**: The grandfathered entries of `tests\guardrails\process_folder_baseline.json` from line 10 onward are existing debt. This change adds none. Remediation action: a separate issue retires the grandfathered entries. The orchestrator files it.
- **Touched violation**: `_build_timeout_adapter` in `initialize_mist_session.py` already spans more than 25 lines (R30). This change adds one import and one keyword argument to it. Remediation action: a separate issue extracts its nested adapter classes.

### Principles II to VII

- **II. Class-based architecture**: Pass. The map is the class `SiteOrganizationMap`. The rule belongs to `RequestLedger` methods. The change adds no wrapper function.
- **III. Safety first**: Pass. The change adds no `input()` call and no destructive operation. The map holds no credential. Logs hold counts only. The change does not alter the menu 309 confirmation.
- **IV. Full deployment pipeline**: Pass as planned. `tasks.md` orders the local gates, the commit, the push, the pull request, the remote CI, and the merge. No task pushes to `main`.
- **V. Observability**: Pass. Each log message uses ASCII text and the message template. The learning step writes counts only.
- **VI. Inline comments**: Pass as planned. Task T012 requires an inline comment on each changed line and each new block.
- **VII. Action logging**: Pass as planned. The learning step writes an info record before the map write and a debug record after it. The fallback writes a debug record with the source name only.

### Technology and compatibility constraints

- **Python 3.15**: Pass. No older syntax is added.
- **mistapi as the sole interface**: Pass. The change adds no HTTP call. The learning step reads the response of an existing mistapi call. The constitution text at line 279 names mistapi 0.59 as the version. That text is stale (`research.md` R06), and this plan does not correct it.
- **Owned WebSocket transport**: Not applicable. The feature owns no transport.
- **Package manager**: Pass. `requirements.txt` and `pyproject.toml` do not change.
- **Container runtime and test containers**: Not applicable to the unit tests. The optional live check uses the existing Redis service. Any ephemeral container takes the name `misthelper-tmp-issue4921-site-request-admission`.
- **File paths**: Pass. The change builds no path string by hand.
- **Output backends and export boundary**: Not applicable. The change writes no export.
- **Operational store**: Not applicable. The map is not an operational coordination record. It holds no transaction, lock across processes, or durable state.
- **Database keys and data directory**: Not applicable. The change writes no product output and no database row.
- **Container security and Zscaler**: Not applicable. The change alters no image.

### Development workflow and documentation

- **Menu operations**: Not applicable. The change adds no operation.
- **README**: Not applicable. `README.md` does not describe request admission. The change alters internal quota attribution only.
- **Release note**: Pass. Task T010 adds one fragment, named `issue-4921-site-request-admission.md`. `changelog.d/README.md` lines 26 and 27 give this rule.
- **Complexity-driven SpecKit escalation**: Pass. The change touches six existing source and test files and two classes. This record is the required specification.
- **Multi-agent git workflow**: Pass as planned. Issue #4921 is open. The branch starts from `main`. The pull request holds one issue. The local working-copy edits stay out of the branch.

### Mist Cloud rules

- **Every REST request uses a working mistapi method**: Pass. No new request is added.
- **Owned WebSocket transport and contract tests**: Not applicable.

## Test Strategy

- **Unit tests** in `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`: the eight new tests in task T005 and the updated adapter test in task T006. Each test uses `FakeRedis` and invented identifiers.
- **Unit tests** in `tests/unit/ex_hardware_inventory/scope/test_hardware_session.py`: the class `TestAdmissionBinding` is removed. The class `TestSdkErrorMute` stays.
- **Integration tests**: `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` runs the menu 309 flow with fake services.
- **Affected reader**: `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` runs the subscription-expiry client.
- **Failure proof**: The learning and batch-thread tests fail on `main` before the fix. The reproduction steps are in `design\quickstart.md`.
- **Secret safety**: The tests assert that the map holds no credential, and that the learning step logs no identifier at info level.
- **Guards**: `tests\guardrails\test_process_folder_structure.py` and `tests\guardrails\test_changelog_fragment_policy.py` run after the record and the fragment exist.

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      site-organization-resolution.md
    checklists\
      requirements.md
      security.md
```

The feature root holds five children. The `design` folder holds five children. The `contracts` folder holds one file. The `checklists` folder holds two files.

### Source code (changed paths only)

```text
src\interfaces\wan_performance\collection\request_admission.py
src\foundation\support\refactors\initialize_mist_session.py
src\operations\exporting\ex_hardware_inventory\scope\session.py
src\operations\exporting\ex_hardware_inventory\run\batch.py
tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py
tests\unit\ex_hardware_inventory\scope\test_hardware_session.py
changelog.d\issue-4921-site-request-admission.md
```

**Structure Decision**: Keep the code in the existing modules. Add one class to `request_admission.py`. The new code belongs beside the adapter that uses it. No new package or directory is created.

## Architecture

The attribution path for each request on the shared adapter:

```text
Caller (batch preview, batch run, status check, shell trigger, subscription read)
  -> existing mistapi call on the session
     -> AdmittedAdapter.send
          -> RequestLedger.admit
               -> RequestLedger._organization
                    organization path     -> path organization
                    site path             -> SiteOrganizationMap
                                             -> ledger organization
                                             -> session organization (callable)
                                             -> refuse (existing message)
          -> HTTP send (existing)
          -> HTTP 429 check (existing)
          -> RequestLedger.learn_site_organizations (new, listing responses only)
```

Each site request passes through the same resolution. The map is shared by every thread that uses the session.

## File-by-File Change Map

| Path | Change | Purpose | Requirements |
| --- | --- | --- | --- |
| `src\interfaces\wan_performance\collection\request_admission.py` | Modify | Add class `SiteOrganizationMap`. Add the session organization argument to `RequestLedger.__init__` and `connect`. Add `learn_site_organizations` and `_site_organization`. Change `_organization` for site paths. Call the learning step in `AdmittedAdapter.send` after the 429 check. | FR-001 to FR-006, FR-008, FR-009, FR-010 |
| `src\foundation\support\refactors\initialize_mist_session.py` | Modify | Pass `session_organization=ConfigUtils.get_cached_org_id` to `RequestLedger.connect` at line 74. Import `ConfigUtils` inside the function, as the function already imports the ledger classes. | FR-004 |
| `src\operations\exporting\ex_hardware_inventory\scope\session.py` | Modify | Delete `AdmissionBinding`, `_find_ledger`, `MIST_URL`, and each import that only they use. Keep `SdkErrorMute`. Rewrite the module docstring without the issue reference. | FR-007, FR-010 |
| `src\operations\exporting\ex_hardware_inventory\run\batch.py` | Modify | Delete the import at line 38. Unwrap the bodies of the two `with AdmissionBinding` blocks at lines 199 and 223. Keep each statement and its comment. | FR-007 |
| `tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py` | Modify | Add eight tests. Update the patched `connect` lambda at line 120 to accept the new argument. | FR-001 to FR-006, SC-001, SC-002, SC-003, SC-005 |
| `tests\unit\ex_hardware_inventory\scope\test_hardware_session.py` | Modify | Delete the class `TestAdmissionBinding` at lines 28 to 86, and the imports that only it uses. Keep the class `TestSdkErrorMute`. | FR-007, SC-004 |
| `changelog.d\issue-4921-site-request-admission.md` | Add | One `### Fixed` heading with one bullet that names issue 4921. | FR-010 |
| `specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission\` | Add | This record. The record step commits it with the implementation pull request. | Record |

## Dependencies

No new package. The pinned versions stay: `mistapi==0.64.1`, `requests`, and `redis`. The change imports `threading`, `collections.OrderedDict`, and `collections.abc.Callable`. Each is in the standard library.

## Implementation Outline

1. Add `SiteOrganizationMap` with a lock, an ordered dictionary, a bound, and two methods: `remember` and `organization`.
2. Add the session organization argument, the learning method, the listing-shape check, and the site resolution to `RequestLedger`.
3. Call the learning step in `AdmittedAdapter.send` after the 429 check.
4. Pass `ConfigUtils.get_cached_org_id` through `_build_timeout_adapter`.
5. Add the eight new unit tests and update the patched `connect` lambda.
6. Remove `AdmissionBinding`, its two call sites, and its test class. Keep `SdkErrorMute`.
7. Add the changelog fragment.
8. Run the gates in `design\quickstart.md`, then open the pull request.

## Risks and Mitigations

- **R-1. Wrong fallback attribution in an MSP session.** The map runs first, so only unlisted sites reach the fallback. The fallback writes a debug record. A follow-up issue can add an exact lookup if the risk proves material (`spec.md` NG2).
- **R-2. Memory growth.** The bound is 50,000 entries. Test SC-005 proves the bound.
- **R-3. Stale mapping after a site moves between organizations.** The map lives for one process. A restart clears it. The risk is recorded (`research.md` U-2).
- **R-4. Symbol gate reports the removal.** The removal is intended. The pull request body records it. SC-004 proves that no reference remains in `src` or `tests`.
- **R-5. Patched test breaks on the new argument.** Task T006 updates the lambda. The test module imports `MistSessionConfigurator`, so an import cycle fails that module.
- **R-6. Race between a listing and a site read.** The lock covers each read and each write. Test T005 covers concurrent use.
- **R-7. Learning cost on a large listing.** Each page is one pass over its records. The cost is not measured (`research.md` U-5).
- **R-8. Overlap with the local working copy.** The branch starts from `main`. The pull request stages files by explicit path. The five local edits stay unstaged.
- **R-9. Function size and complexity.** Helpers keep each function under the limits. The radon gate in `design\quickstart.md` checks the complexity.

## Rollback Steps

1. Open a revert pull request from `main`. Do not force-push.
2. Revert the squash commit. The revert restores `AdmissionBinding` and its call sites, because the commit removed them.
3. No data changes. The map is in memory, and the Redis key format is unchanged.
4. After the revert, run the commands in `design\quickstart.md` for tasks T013 and T014, and check the menu 309 preview.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| `_build_timeout_adapter` exceeds 25 lines (existing, touched) | The change adds one argument to an existing function | Extracting the nested classes in this change widens the diff. A separate issue handles the extraction. |
