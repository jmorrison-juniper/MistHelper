# Specification Analysis Report

## Result

The record covers the 14 families, the evidence gates, the implementation split, and the final gates. Two external issues block implementation: issue 4634 must record the evidence rows, and issue 4638 must publish the supported model table.

This record does not authorize a Mist write. It does not authorize a portal change or a release.

## Inputs Examined

- Issue 4639 facts, read with `gh issue view`. The issue is open. It has no comments.
- PR 4596, the full-parity task map. It merged on 2026-11-13. Its files were read from the remote `main` branch (R17 to R25).
- The governing files: `AGENTS.md`, `.github/copilot-instructions.md`, the constitution, and the four Spec Kit templates (R01 to R15, R82, and R85).
- The current converter files on `main`: `conversion.py`, `models.py`, `routes.py`, and their tests (R26 to R38).
- The OpenAPI YAML file, the installed mistapi 0.64.1 signatures, and the source mapping document (R42 to R81).
- Sibling drafts for issues 4636 and 4649, read from the local draft folder. These drafts are not on `main`.

## Consistency Review

| Check | Result | Evidence |
| --- | --- | --- |
| Each FR maps to a task and a test | Pass | Tasks T003 to T008 and tests TM-01 to TM-17 (`tasks.md`, Test Plan Map). |
| Each mapped field has evidence | Pass with condition | Four fields depend on E-01, E-03, and E-04. Each has a pending row until issue 4634 verifies it. |
| Each task names exact paths | Pass | Every task lists repository paths. |
| Parent test path fits the repository structure | Fail in parent, corrected here | R34 is absent. R35 shows that `tests/contract/` is overfull (D-1). |
| Parent dependency table covers shared edits | Fail in parent, corrected here | R19 omits issue 4640 task T014. R20 forbids parallel edits to shared files. The edge is added (D-16). |
| Research test path is current | Fail in parent, corrected here | R23 names a path that is absent. R31 and R32 hold the current DNS tests. |
| Line citations use a usable OpenAPI file | Partial | R25 records that the JSON twin is one line. This record cites the YAML file. T001 compares both files. |
| Role model supports Branch and Hub | Fail, depends on issue 4638 | R30 limits the source kind to standalone and spoke. Syslog placement waits for issue 4638. |
| DNS output stays unchanged | Pass by design | The review returns a separate list. R31 and R32 keep the DNS assertions. TM-17 adds a baseline check. |
| Secrets stay out of output and logs | Pass by design | R08 and R09 set the rule. The redaction contract and TM-03, TM-16 enforce it. |
| Source claims resolved before mapping | Pass | Decisions D-7, D-8, and D-9 resolve the conflicting syslog, host-out, and SNMP claims. |

## Defects in Existing Work

| ID | Location | Defect | Disposition |
| --- | --- | --- | --- |
| A-1 | Parent task T015 (R17) | The management test path adds a child to `tests/contract/`, which already has 17 children (R35). | Moved to the converter integration folder (D-1). The parent record needs a later correction. |
| A-2 | Parent dependency row for T016 (R19) | The row omits task T014, although both tasks edit `conversion.py`. | Edge added (D-16). The parent record needs the edge. |
| A-3 | Parent research line 59 (R23) | The unit test path is absent on `main`. The current path is under `tests/unit/marvis/`. | Corrected here (R31). The parent record needs a correction. |
| A-4 | Parent contract line 5 (R25) | The contract names the JSON OpenAPI file as its authority. That file is one line of 3.6 MB. | The YAML file gives line citations. T001 checks both twins. |
| A-5 | `IOSDnsConverter._label` and its generic label (R28) | Every unsupported line receives one generic label. Reviewers cannot see the family. | Family labels are added in the new review. The DNS label keeps its output (D-3). |
| A-6 | Source kind check (R30) | The converter accepts only standalone and spoke roles. The parent task list requires Branch, Hub, and Standalone. | Issue 4638 must extend the role check. Syslog mapping waits for it. |
| A-7 | Source syslog and SNMP claims (R72, R73, R75, R78) | Source lines disagree about Hub syslog and SNMP community placement. The OpenAPI does not match one source statement (R45, R49). | Resolved by the evidence rows and decisions D-7 and D-9. |

## Unresolved Items

| ID | Item | Owner | Reference |
| --- | --- | --- | --- |
| U-1 | The JSON and YAML twins agree for each pointer | Issue 4634 | T001 |
| U-2 | LTE support for each model and the port identifiers | Issue 4638 | T008 |
| U-3 | Enumerations for syslog severity, facility, and protocol | Issue 4634 | Research U-3 |
| U-4 | The TACACS secret field name in the switch schema | Issue 4634 | Research U-4 |
| U-5 | The length bound for SNMP location and contact text | Issue 4634 | T001 |
| U-6 | Live gateway behavior for the Hub schema absence | Owner review, no live test in this issue | Research U-6 |
| U-7 | Cisco command forms in the fixtures | Issue 4634 | T003 |
| U-8 | Reuse rights for the source document | Issue 4635 | Decision D-16 and research |
| U-9 | Device-side context from the Juniper skills | None. No mapping depends on it. | Research U-9 |

## Validation Performed

- Read-only remote checks: 85 rows in `design/research.md`. Each row cites a path, a reference, a blob SHA or an absence marker, a result, and a line where one applies.
- Local HEAD and remote `main` both point to commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- The remote tree of `main` lists 11,404 entries. The remote listing is not truncated.
- The structure counts are: feature root 5, `design/` 5, `design/contracts/` 3, `design/checklists/` 2.
- No repository gate ran. Brief rule 2 forbids builds, tests, and linters during this drafting pass.

## Next Actions

1. Issue 4634 records evidence rows E-01 to E-08 in its contract file.
2. Issue 4636 confirms that the converter module stays in place.
3. Issue 4638 publishes the supported model table and the role values.
4. Issue 4640 finishes task T014 before task T007 starts.
5. The owner reviews the eleven display-only dispositions in decision D-14.
