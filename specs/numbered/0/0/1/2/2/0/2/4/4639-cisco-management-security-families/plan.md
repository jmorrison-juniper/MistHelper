# Implementation Plan: Review management and security configuration families

**Branch**: `docs/4639-cisco-management-security-families` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record route `specs/numbered/0/0/1/2/2/0/2/4/4639-cisco-management-security-families/`. The route is free on main (R16).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place the supporting artifacts under `design/`. The feature root holds five children.

## Summary

Add a review data contract for 14 management and security families to `conversion.py`. Map four fields only after verified evidence. Keep eleven families display-only. Keep the DNS conversion output unchanged. Add no portal change and no write.

## Technical Context

**Language/Version**: Python, as the repository requires. The local gates table names the commands (R04).

**Primary Dependencies**: mistapi 0.64.1 (R39, R67). This issue adds no dependency.

**Storage**: None. The review keeps no state and writes no file.

**Testing**: pytest, through the local gates table (R04). One new test file sits in the converter integration folder.

**Target Platform**: The same host as the existing converter. The change adds no platform-specific code.

**Project Type**: One module change inside the existing converter package, plus one new test folder.

**Performance Goals**: The review reads each source line once. This issue sets no timing target.

**Constraints**: No network access in review. No write. No secret in output or logs. ASCII-only log text.

**Scale/Scope**: 14 families. 15 requirements. 17 planned test functions. Four mapped fields after evidence: syslog host, SNMP location, SNMP contact, and cellular APN.

## Constitution Check

The table lists each rule that applies to this change. Row IDs refer to the remote verification table in `design/research.md`.

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-item rule (R07) | Pass | The change adds no child to `src/interfaces/portals/cisco_config_converter/` (R38) or to `tests/contract/` (R35). It adds one child, `management/`, under the converter integration folder. |
| I. Function limits (R03) | Pass | Each new method takes at most five parameters and keeps its body within five blocks. T007 checks the complexity gate. |
| II. Class-based architecture (R10) | Pass | The review logic lives in two named classes. No wrapper function delegates to a method. |
| III. Safety-first input (R02) | Pass | The review accepts text that `SourceConfiguration` already validated. It reads no keyboard input. |
| III. Secrets never in outputs (R08) | Pass | Secret values are omitted at the review boundary. Tests T003 and T006 prove the omission. |
| V. Logging (R09) | Pass | Log lines hold counts and family IDs only. No secret value enters a log line. |
| VI. Inline comments | Pass by plan | T007 adds an inline comment to each executable line. The implementation review checks this rule. |
| VII. Action logging | Pass by plan | T007 adds an info line before and a debug line after each review action. |
| Technology: mistapi is the sole Mist interface | Pass | This issue sends no request. The pin is `mistapi==0.64.1` (R39). |
| Output backends | Not applicable | This issue exports no data. Issue 4641 owns the proposal export. |
| Operational store | Not applicable | This issue writes no coordination record. |
| Data directory | Pass | The review writes no file under `data/`. |
| Database keys | Not applicable | This issue adds no Mist endpoint operation. |
| Spec Kit route (R06) | Pass | The route is free (R16). The record uses the managed numbered root. |
| STE writing rules (R01, R05) | Pass by plan | T-LOCAL-GATES runs the STE gate on every record file. |
| Local gates (R04) | Pass by plan | T-LOCAL-GATES runs each gate that applies to the changed files. |
| Security findings | Pass | The plan adds no suppression comment. |
| Existing structure debt (R35) | Pass | The change leaves `tests/contract/` unchanged. Its 17 children remain existing debt. |
| Release notes (R82) | Pass | The change set adds one fragment under `changelog.d/`. `CHANGELOG.md` stays unchanged. |
| Deployment pipeline, principle IV (R85) | Pass by plan | Local gates, pull request, CI, and merge run through T-LOCAL-GATES to T-MERGE. Post-merge build and deployment need orchestrator authorization. |

## Architecture

Data flow in one review call:

- Source text passes through `SourceConfiguration`, which already validates it.
- `IOSDnsConverter.convert` builds the DNS proposal. Its output does not change.
- `ManagementFamilyReview.review` builds one observation for each matched family line.
- Issue 4637 displays the observations. Issue 4641 places them in the proposal.

The review classifies top-level lines with an allow-list of keyword phrases. Child lines inherit the family of their parent. Banner bodies are skipped with the same delimiter rule that the DNS converter uses. A secret keyword overrides every mapping. A mapping exists only when its evidence row is verified.

Module children after the change: the logger constant, `IOSDnsConverter`, `ManagementObservation`, and `ManagementFamilyReview`. That is four children, below the limit of five.

## File Change Map

| Path | Action | Task | Reason |
| --- | --- | --- | --- |
| `tests/integration/web_portal/cisco_config_converter/management/__init__.py` | Add | T003 | Package marker for the new test folder. The file holds no executable line. |
| `tests/integration/web_portal/cisco_config_converter/management/test_management.py` | Add | T003 to T006 | Holds the 17 planned test functions (R33 shows the parent folder). |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Modify | T007, T008 | Adds `ManagementObservation`, `ManagementFamilyReview`, and a public `banner_delimiter` method. The DNS method keeps its output. |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | No change | T006 | Regression baseline for the DNS output (R31, R32). |
| `tests/integration/web_portal/cisco_config_converter/test_routes.py` | No change | T006 | Regression baseline for the portal routes (R33). |
| `src/interfaces/portals/cisco_config_converter/models.py` | No change | None | Issue 4636 owns this file (R30 shows the source kind limit). |
| `src/interfaces/portals/cisco_config_converter/routes.py` | No change | None | Issues 4637 and 4641 own the route changes. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | No change | None | Issue 4637 owns the presentation. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | No change | None | Issue 4637 owns the presentation. |
| `web_portal/app.py` | No change | T009 | Shared portal host (R37). This issue has no portal change. |
| `web_portal/templates/base.html` | No change | T009 | Shared portal navigation. The issue body excludes navigation changes. |
| `documentation/` | No change | T011 | Issue 4649 owns the converter guide. |
| `changelog.d/` | Add | T011 | One fragment for this change set (D-15). |

## Dependencies

| Dependency | Type | Needed by | Source |
| --- | --- | --- | --- |
| Issue 4634 records evidence rows E-01 to E-08 | External | T001, T008 | Parent task T003 |
| Issue 4636 keeps `conversion.py` in place | External | T002 | Parent task T006 |
| Issue 4637 owns the review display | External | Display only, after this change | Parent task T010 |
| Issue 4638 publishes the supported model table | External | T008 | Parent task T012 |
| Issue 4640 finishes task T014 | External | T007 | Shared file `conversion.py` (D-16) |
| T002 before T003 and T005 | Internal | Test writing | Ownership gate |
| T003 before T004, T004 before T005, T005 before T006 | Internal | Test order | Shared test file |
| T006 and T014 of issue 4640 before T007 | Internal and external | Implementation | Shared file |
| T001 and T007 before T008 | Internal | Mapping entries | Evidence gate |

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Hub syslog stays display-only | Hub sites receive no syslog mapping | Keep the family limit visible. Report the gap to the owner in issue 4649 (D-14). |
| Schema drift changes a pointer | A mapping points to a removed field | T001 checks each pointer before T008. T008 tests assert each pointer. |
| The JSON and YAML twins differ | A line citation points to the wrong schema | T001 compares each pointer in both twins. Research R25 records the single-line JSON limit. |
| Shared file conflict with issue 4640 | Merge conflict in `conversion.py` | Serialize T014 before T007 (D-16). |
| A secret reaches a log line | Credential exposure | Log counts only. TM-16 scans captured logs for the synthetic secret. |
| A role model lacks Branch or Hub | Syslog placement cannot be selected | Syslog mapping waits for issue 4638 (R30 shows the current two-role limit). |
| `conversion.py` grows large | Review becomes hard to read | Keep the two classes small. Add no module child. Run the complexity gate. |
| Accidental organization-scope write | Warning: gateway behavior changes at every site. | This issue writes nothing. Issue 4644 must review organization scope before any write. |

## Rollback Steps

1. Revert the commit that changes `conversion.py`. The DNS behavior returns to the earlier output.
2. Delete the `management/` test folder by its exact name. Its tests then no longer run.
3. Run `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter/test_routes.py` to confirm the DNS baseline.

No data changes. No record rewrite. No Mist state changes.

## Complexity Tracking

This change adds no violation to the grandfathered debt listed below.

| Type | Violation or debt | Why it stays | Simpler alternative rejected because |
| --- | --- | --- | --- |
| Grandfathered debt | `tests/contract/` has 17 direct children (R35) | Existing debt. This change does not touch it. | A management folder there would add a child to an overfull parent. |
| Grandfathered debt | `models.py` holds the proposal types and is owned by issue 4636 (R30 shows the source kind limit) | This change must not edit it | Adding proposal fields here would conflict with the state-package work in issue 4636. |
| New design | `conversion.py` gains two classes | The review needs its own classes, and the DNS module owns the converter | A new module would add a sixth child to the converter package root (R38). |
