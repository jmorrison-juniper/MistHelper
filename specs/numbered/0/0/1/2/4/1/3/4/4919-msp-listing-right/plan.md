# Implementation Plan: MSP organization list skipped without the listing right

**Branch**: `fix/4919-msp-listing-right` (proposed) | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/4/1/3/4/4919-msp-listing-right/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting artifacts sit under `design/`.

## Summary

The cross-org subscription report (menu 308) calls `listMspOrgs` for each profile grant that names an MSP. A grant without MSP scope cannot list that MSP's organizations. The call then fails with HTTP 403 on each run. This plan adds a listing right check before the call. A grant without the right produces a skipped status row and no call. A grant with the right keeps the current behavior.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Source: `pyproject.toml` line 23, `requires-python = ">=3.15"`.
- **Primary Dependencies**: mistapi 0.64.1. Source: `pyproject.toml` line 29, `>=0.64.1,<0.65`, and `requirements.txt` line 129, `==0.64.1`. Installed copy: `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`.
- **Storage**: Existing CSV outputs. The change adds no column and no file.
- **Testing**: pytest with fake sessions in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/`.
- **Target Platform**: Windows 11, macOS, and Linux. The product also runs in a Podman container. This change needs no container.
- **Project Type**: Menu operation 308 in a Python command-line tool.
- **Performance Goals**: One listing call fewer for each skipped source. The issue sets no numeric target.
- **Constraints**: ASCII log text, an inline comment on each new line, the five-item rule, and action logging.
- **Scale/Scope**: One active profile for each run.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass with recorded debt | The `subscription_expiry` directory holds four files. Method `discover_organizations` spans main lines 79 to 106, which is 28 lines. Method `_print_summary` spans main lines 494 to 519, which is 26 lines. Both exceed 25 lines before this change. The change adds at most two lines to `_print_summary` and none to `discover_organizations`. Remediation R-1 tracks both. |
| II. Class-Based Architecture | Pass | New logic sits in methods of `SubscriptionExpiryClient` and `CrossOrgSubscriptionInventoryReport`. |
| III. Safety-First | Pass | The change reads one grant field and prints it. It takes no keyboard input and runs no destructive action. |
| IV. Full Deployment Pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover pipeline steps 1 to 9. Steps 10 to 12 run on the merged revision after T-MERGE. |
| V. Observability and Logging | Pass | New log text uses ASCII only. Info lines come before each action, and debug lines come after it. |
| VI. Inline Comments | Pass | FR-011 and the tasks require an inline comment on each new executable line. |
| VII. Action Logging | Pass | FR-011 requires an info line before and a debug line after each new action. |
| Technology: mistapi only | Pass | The change uses the existing `listMspOrgs` and `getSelf` calls. |
| Technology: test containers | Not applicable | No container runs in this change. |
| Technology: data directory | Pass | Outputs keep the existing report output path under `data/`. |
| Technology: output backends | Pass | The change adds no export call. The report keeps its existing export path. |
| Technology: database keys | Not applicable | The change adds no endpoint and no primary key strategy. |
| Documentation | Pass with note | The cross-org reference changes. `README.md` has no entry for menu 308. A search for `cross-org`, `308`, and `subscription` found no match in `README.md`. |
| Changelog | Pass | The fragment name follows `changelog.d/README.md` line 24. |
| Escalation | Pass | The change touches five files and two classes. This record is the required specification. |
| Multi-agent workflow | Pass | Seven open pull requests were checked. None changes a file in the change map. |
| Security findings | Not applicable | No scanner finding applies to this change. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/3/4/4919-msp-listing-right/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      msp-listing-right.md
      status-rows.md
      console-summary.md
    checklists/
      requirements.md
```

## Architecture

The menu 308 flow runs in this order:

1. `CrossOrgSubscriptionInventoryReport._run_with_client` in `operation.py` calls `discover_organizations`.
2. `SubscriptionExpiryClient.discover_organizations` in `client.py` reads the profile and adds each direct organization.
3. For each MSP grant with the listing right, `_discover_msp` calls `listMspOrgs`, as before.
4. For each MSP id without the listing right, `_skipped_msp_rows` returns one status row. No call runs.
5. `_export_reports` writes the status rows to CSV. `_print_summary` prints the skipped sources.

The row type `OrganizationScope` in `model.py` stays unchanged.

## File-by-File Change Map

| Path | Action | Change | Requirements |
| - | - | - | - |
| `src/mist/intelligence/reports/subscription_expiry/client.py` | Modify | Add class attribute `MSP_GRANT_SCOPE` with value `msp`. Add static method `_has_msp_listing_right`. Add the right check to the MSP branch in `discover_organizations`. Append the result of `_skipped_msp_rows` to the returned failures. Add methods `_skipped_msp_rows` and `_skipped_msp_row`. | FR-001 to FR-006, FR-009 to FR-011 |
| `src/mist/intelligence/reports/subscription_expiry/operation.py` | Modify | In `_print_summary`, exclude skipped rows from the discovered count, and call `_print_skipped_sources`. Add static methods `_skipped_rows` and `_print_skipped_sources`. | FR-007, FR-008 |
| `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` | Modify | Add six test functions. Tasks T005 lists them. | FR-014 |
| `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py` | Modify | Add two test functions. Task T006 lists them. | FR-014 |
| `documentation/cross-org-subscription-stock.md` | Modify | Add the listing right rule, the `skipped` status, the reason text, and the effect on MSP license evidence. | FR-012 |
| `changelog.d/issue-4919-msp-listing-right.md` | Add | One `###` heading and one `Fixed` bullet that names issue 4919. | FR-013 |
| `src/mist/intelligence/reports/subscription_expiry/model.py` | No change | The change reuses the `request_status` and `error` fields. | FR-010, SC-006 |
| `src/operations/exporting/ex_hardware_inventory/scope/profile.py` | No change | Reference only. Lines 126 and 136 hold the scope rule. | FR-002 |
| `src/foundation/support/refactors/msp_privilege_detection.py` | No change | Out of scope. Analysis item A4 records the same pattern. | Non-goal |

## Method Outline

```text
discover_organizations:
  read the profile
  for each profile grant:
    add the direct organization (unchanged)
    if the grant names an MSP and holds the listing right:
      call _discover_msp (unchanged, including the HTTP failure row)
  return the organizations and failures plus _skipped_msp_rows(grants)

_skipped_msp_rows(grants):
  collect the MSP ids of grants that hold the listing right
  for each grant that names an MSP id outside that collection and not yet recorded:
    record one skipped row with the reason text
```

## Dependencies

- No new package is added.
- No requirement file changes.
- The change uses the installed mistapi 0.64.1 methods only.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| An MSP-scope grant with a role that cannot list still receives HTTP 403. | The run still shows the failure row for that MSP. | FR-009 keeps the failure row. Unverified item U1 tracks the role threshold. |
| Live organization-scope grants never carry an `msp_id`. | The change has no effect on those profiles. | No regression occurs. Unverified item U2 tracks the live check. |
| Merge conflict with the pending warning change in `client.py` and `test_client.py`. | Rebase work. | Keep new tests in new functions. Rebase after the pending change lands (D6). |
| Operators read "Organizations discovered" with a new meaning. | The count changes only when skipped rows exist. | FR-008 and the reference update in FR-012. |
| A skipped MSP has no MSP license evidence. | Fewer purchase rows for that MSP. | The reference documents the effect (FR-012). |

## Rollback Steps

1. Revert the squash commit on `main` through a new pull request. Do not push to `main`.
2. Confirm that `client.py` no longer contains `_has_msp_listing_right`.
3. Run menu 308 again to regenerate the status CSV file.

Caution: A revert does not restore CSV files that an earlier run wrote. Run the report again after the revert.

## Recorded Remediation Actions

- **R-1**: Split `discover_organizations` and `_print_summary` into smaller methods, so each has 25 lines or fewer. Use a separate issue.
- **R-2**: Align `msp_privilege_detection.py` and the other `listMspOrgs` callers with the scope rule. Use a separate issue.
- **R-3**: Correct the MistHelper Notes in `documentation/api/msps/GET_msps_msp_id_orgs.md`. Use a separate issue.
- **R-4**: Align the mistapi pin text in `.github/copilot-instructions.md` line 21 with `pyproject.toml` line 29. Use a separate issue.

## Decisions

Decisions D1 to D8 sit in `design/research.md`. Decision D8 needs a human answer. The other decisions are technical, and the research supports each one.
