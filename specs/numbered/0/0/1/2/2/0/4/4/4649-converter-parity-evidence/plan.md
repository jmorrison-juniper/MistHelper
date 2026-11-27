# Implementation Plan: Close Full-Parity Evidence Gaps with Approved Dispositions

**Branch**: `docs/4649-converter-parity-evidence` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/0/4/4/4649-converter-parity-evidence/spec.md`. The route comes from `spec-route.ps1`, base 5, eight segments.

## Summary

Define how parity task T033 closes. The record adds an evidence register, a gate table, a parity task status table, and one nested audit package. This pull request changes Markdown only. Implementation, legal reuse, and cloud use stay blocked.

## Technical Context

**Language/Version**: Markdown for the records. Python 3.15 or newer for the future audit package (`.github/copilot-instructions.md` line 20, R14).

**Primary Dependencies**: The existing pytest runner and `ste-linter`, both in the local gates table. No new dependency.

**Storage**: Repository files only. The register lives in the parity `design/research.md` file.

**Testing**: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`, with 13 planned test functions.

**Target Platform**: Windows 11, macOS, and Linux. The audit reads text files only.

**Project Type**: Spec Kit record and one feature-owned test package.

**Performance Goals**: Not applicable. The audit reads 40 rows, 33 tasks, and six gates.

**Constraints**: No cloud call, no credential, and no write outside the two record folders in this pull request.

**Scale/Scope**: 40 comparison rows, 33 parity tasks, six gates, 13 functional requirements, 16 tasks, and 77 remote checks.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| Five children or fewer per level (constitution line 40, R18) | Pass | The record root holds five children. The `design` folder holds five children. |
| Managed Spec Kit roots and base-5 route (constitution line 57, R18, and `spec-route.ps1` line 17, R22) | Pass | The route is `specs\numbered\0\0\1\2\2\0\4\4`. It matches base 5 of 4649. |
| Feature-owned test placement (Principle I) | Pass with risk | The audit lives in a new `evidence` package under the converter test folder. Finding F-04 records the projected overflow. |
| Class-based design (Principle II) | Pass | The future audit is the class `EvidenceRegisterAuditor`. This pull request adds no function. |
| Safety (Principle III) | Pass | This pull request performs no cloud write and no destructive operation. |
| Deployment pipeline (Principle IV, constitution line 143, R19) | Pass | Local gates and remote checks appear in tasks T-LOCAL-GATES to T-MERGE. |
| ASCII logging (Principle V) | Pass | The future audit writes ASCII output only. The output contract is `design/contracts/audit-report.md`. |
| Inline comments and action logging (Principles VI and VII) | Not applicable | This pull request adds no code. The future audit must satisfy both rules. |
| mistapi as the only Mist REST interface (Technology and Compatibility Constraints section) | Pass | This pull request makes no Mist call. Future writes use only the mistapi methods named in the contract. |
| Secrets (Principle III) | Pass | The register stores no secret, token, or customer data. FR-012 and a test enforce this rule. |
| Changelog fragment (constitution line 409, R19) | Deviation recorded | This pull request adds no fragment. Decision D-14 and finding F-09 explain the choice. |

No implementation gate passes in this pull request.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/4/4/4649-converter-parity-evidence/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      evidence-register.md
      gate-decision.md
      audit-report.md
    checklists/
      requirements.md
      evidence.md
```

### Future Source and Test Layout (not changed in this pull request)

```text
tests/integration/web_portal/cisco_config_converter/
  __init__.py                  existing, R39
  test_routes.py               existing, R32
  evidence/                    new package for T008
    __init__.py
    register_audit.py          new class EvidenceRegisterAuditor
    test_register_audit.py     new file with 13 test functions
```

**Structure Decision**: The audit goes into one nested package under the converter test folder. The feature test folder holds two children today, so the new package makes three. Parity tasks T017 and T031 would add direct children. Finding F-04 requires those tasks to use nested packages.

## Architecture

1. The register lives in the parity `design/research.md` file. Each row has one disposition, one owner decision ID when required, and one remaining task.
2. The gate table lives in the same file. Each gate records its owner, status, decision ID, and evidence.
3. The parity task status table lives in the parity `tasks.md` and `analysis.md` files.
4. `EvidenceRegisterAuditor` reads these files from the working tree. It counts rows, tasks, gates, and links. It returns one result and one exit code.
5. The completion claim is allowed only when the audit result is pass for FR-008.

## Implementation Sequence (after authorization)

1. Resolve gates G1 to G5 and GV with recorded decisions (tasks T001 to T004).
2. Write the audit package and its tests before the register refresh (task T008).
3. Refresh the register, the analysis, and the dispositions (tasks T005 to T007).
4. Run the link audit and the STE gate on every refreshed file (tasks T009 and T010).
5. Write the converter guide only when documentation approval and G1 exist (task T011).
6. Decide the completion claim with the audit result (task T012).

## Approval Gates

| Gate | Blocked work |
| --- | --- |
| G1 Legal | Source reuse and release |
| G2 API | Each unverified mapping and each write |
| G3 Integration owner | Changes to `web_portal/app.py` and `web_portal/templates/base.html` |
| G4 Cloud owner | Apply, restore, delete, unassign, and private storage |
| G5 Operator | Each cloud write |
| GV Visual owner | Visual acceptance of the four journeys |

The research file holds the evidence for each gate. Decisions D-7 to D-10 are human decisions.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| No changelog fragment (constitution line 409) | This change alters no user-visible behavior | A fragment would describe a record, not a product change. Precedent: PR #4596. |

## Rollback Steps

1. Close the pull request without merge if the review rejects the record.
2. Delete the `docs/4649-converter-parity-evidence` branch and its worktree.
3. No product file, data file, or service changes in this pull request. No runtime reversal is needed.
4. If a merge already happened, open a new issue and branch from main to remove the record folder. Do not push to the merged branch.

## Risks and Mitigations

- Completion misread: The closure keyword can close the issue without closing parity T033. Mitigation: a Caution line in the pull request body and the summary (D-11).
- Parity path drift: Finding F-02 shows a missing unit test path. Mitigation: the audit checks each path on main.
- Folder overflow: Findings F-03 and F-04 show projected overflow. Mitigation: nested packages and a structure check before each new child.
- Legal exposure: Source license R49 declares CC BY-NC 4.0. Mitigation: gate G1 blocks reuse (D-8).
- Secret exposure: Findings F-10 and F-11 show weak portal authentication and a random secret fallback. Mitigation: FR-012 test and gate G4 (D-10).
- Stale SDK evidence: A mistapi pin change alters signatures. Mitigation: the SDK checks R66 to R77 and decision D-15.
