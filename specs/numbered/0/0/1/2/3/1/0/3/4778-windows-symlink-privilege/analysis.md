# Specification Analysis Report: Windows Symlink Privilege in the Spec-Route Contract Guard

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, the two contracts, and the remote `main` tree at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only pass. The pass built the requirement map and the task map, then compared each cited line with the remote body. This run executed no test, build, or gate (repository rule 2).

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Defect | HIGH | `tests/guardrails/test_spec_route_contract.py` line 296 | The symlink case creates a symlink at setup. On a host without the symlink privilege, setup raises WinError 1314 before the guard runs. | Fixed by T004 and T005. |
| A2 | Gap | MEDIUM | `documentation/development-setup.md` lines 9-15 and 168-174 | The setup document does not state the PowerShell 7 requirement of the guard (research F-10). | Fixed by T006. |
| A3 | Risk | HIGH | `mklink /J` on a host without the symlink privilege | The FSCTL page states a privilege rule for reparse points. The junction page states none. The junction result is unknown (U-1). | Accepted with a skip path (D-2) and a host check in T-LOCAL-GATES. |
| A4 | Ambiguity | MEDIUM | `tests/guardrails/test_spec_route_contract.py`, top-level names | The module has more than five top-level names before this change (Complexity Tracking). | Accepted. Remediation R-1 splits the module in a separate issue. |
| A5 | Ambiguity | LOW | Issue #4778 body | The issue names a "structural/SDK/output gate" and an "in-progress relocation mapping failure" without commands or identifiers. | Accepted. Non-Goals name both. Unverified items U-5 and U-6 cover them. |
| A6 | Inconsistency | LOW | Brief section 2, item 7 | The brief names `documentation/mist-api-openapi31yaml.json` as a twin. The file is absent locally (U-9). | Accepted. The record makes no Mist claim. |
| A7 | Process | LOW | `tasks.md`, tasks T-REMOTE-CI and T-MERGE | The local gates table lists no remote command. These tasks use the `gh` commands of AGENTS.md. | Accepted. This report records the exception. |
| A8 | Coverage | LOW | `tests/guardrails/test_spec_route_contract.py` | TEST-02 to TEST-04 use monkeypatch on Ubuntu. No real junction runs there. | Accepted. The real junction runs on the Windows host in T-LOCAL-GATES. |
| A9 | Process | LOW | `.github/workflows/ci.yml` line 750 | The CI task audit runs with `|| true`, so the audit cannot fail the run. | Accepted. This record does not use the audit. |
| A10 | Environment | LOW | Local working tree | Five files have unstaged edits that the issue does not name. | Accepted. The record cites only blobs that match `main`. |

## Coverage Summary

| Requirement | Has task | Task IDs | Test | Notes |
|-------------|----------|----------|------|-------|
| FR-001 | Yes | T004, T005 | TEST-01 | Symlink case on Ubuntu. |
| FR-002 | Yes | T003, T004 | TEST-02 | Junction after WinError 1314. |
| FR-003 | Yes | T003, T004 | TEST-03 | Skip with the `mklink` output. |
| FR-004 | Yes | T003, T004 | TEST-04 | Other errors raised again. |
| FR-005 | Yes | T005 | TEST-01 | The three assertions do not change. |
| FR-006 | Yes | T001, T008 | TEST-01 | The red proof removes the reparse-point check. |
| FR-007 | Yes | T008, T-MERGE | TEST-01 and the existing `[outside]` and `[nested]` cases | No case is removed or skipped by default. |
| FR-008 | Yes | T003, T004 | TEST-02 | The test uses `caplog` to check the order of info and debug lines. |
| FR-009 | Yes | T006 | STE gate | The gate checks the prose style. Task T006 checks the content. |
| FR-010 | Yes | T007, T-PR | `tests/guardrails/test_changelog_fragment_policy.py` | The pull request body holds the reason. |
| FR-011 | Yes | T002, T-LOCAL-GATES | TEST-01 run with `--log-cli-level=INFO -rs` | The Windows run prints the link kind. |

## Consistency Review

- The spec, the plan, and the contract `link-fallback.md` describe the same three outcomes: symlink, junction, and skip. The error path raises every other error again in all three.
- The tasks match the file map in `plan.md`. The tasks change three files: the test module, the setup document, and the record.
- The gate map in `plan.md` matches the verification commands of the tasks.
- The remote table in `research.md` has 51 rows. The STATUS file has 51 `remote_checks` entries. The summary states the same count.
- The requirement count is 11. The task count is 12. The planned test count is 4. These counts match in the spec, the plan, the tasks, and the STATUS file.

## Verification Command Coverage

Each local task names one verification command. The local gates table, the Tests gate, or the changelog guard in `ci.yml` line 298 supplies each command. Tasks T-REMOTE-CI and T-MERGE use `gh` commands from AGENTS.md, because the local gates table holds no remote command (A7).

## Unresolved Items

- U-1: The junction privilege. Task T-LOCAL-GATES checks it on the affected host. A failed check keeps the skip path active.
- U-2: Results on the affected host. Task T002 records the baseline, and task T-LOCAL-GATES records the fix.
- U-3 to U-4: Traversal and cleanup of junctions on Python 3.15.2. The safe target rule and the snapshot check cover both.
- U-5 to U-7: The relocation failure, the structural gate, and the 137-count composition. The issue gives no command or identifier, so this record does not change them.
- U-8: PowerShell 7 on the affected host. Task T-LOCAL-GATES checks it with the Windows run.
- U-9: The JSON twin of the Mist OpenAPI file. The record makes no Mist claim.
