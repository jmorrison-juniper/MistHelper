# Analysis: Portal hardware inventory unlock without the free-form shell

This review compares spec.md, plan.md, and tasks.md with the code on GitHub `main`. Remote check IDs (RC-nnn) point to the table in design/research.md. Unverified claims use the U-nn IDs in the same file.

## 1. Requirement coverage

Each requirement maps to at least one code task and at least one test case. Test cases use the IDs in tasks.md.

| FR | Code tasks | Test cases | Gap |
|----|------------|------------|-----|
| FR-001 | T010, T013, T014 | T002 (a), T005 (a) | None |
| FR-002 | T010, T011, T012, T013 | T002 (b), T003 (b), T004 (b) | None |
| FR-003 | T010, T013 | T002 (c), T004 (a), T005 (c) | None |
| FR-004 | T010 | T002 (d) | None |
| FR-005 | T011, T012, T013, T015 | T003 (a), T004 (d), T006 | None |
| FR-006 | T011, T012, T013 | T004 (c) | None |
| FR-007 | T010, T014, T017 | T002 (e), T007 | None |
| FR-008 | T009 | T001 (a), (b), (c) | None |
| FR-009 | T016, T017 | T007 | None |
| FR-010 | T018, T019, T022 | T008 (1), (2) | T022 is blocked (A-05) |
| FR-011 | T018 | T008 (1) | None |
| FR-012 | T015 | T006 | `batch.py` does not change (RC-078, RC-079) |
| FR-013 | T013 | T005 (b) | None |
| FR-014 | T-PR diff review | T005 (b) | None |
| FR-015 | T021 | T008 (4) | None |
| FR-016 | T020 | T008 (3) | None |

Success criteria map to tests as follows. SC-001: T002 (c), T004 (a), T005 (c). SC-002: T002 (b), T003 (b), T004 (b). SC-003: T002 (a), T005 (a). SC-004: T008. SC-005: T007.

Test count: 24 cases in 8 files (3, 5, 3, 4, 3, 1, 1, 4).

## 2. Directory child counts

| Folder | Children | Limit | Result |
|--------|----------|-------|--------|
| Feature root | spec.md, plan.md, tasks.md, analysis.md, design | 5 | Pass |
| design | research.md, data-model.md, quickstart.md, contracts, checklists | 5 | Pass |
| design/contracts | settings.md, catalog-payload.md, refusals.md | 5 | Pass |
| design/checklists | requirements.md | 5 | Pass |

The route `0/0/1/2/4/2/2/4` equals issue 4939 in base 5, padded to eight digits (computed: 124224 in base 5 equals 4939). Each route maps one issue. The route folder holds only this record.

## 3. Findings

- **A-01 Mistapi pin drift.** `.github/copilot-instructions.md` line 21 says `mistapi>=0.64.0,<0.65` (RC-004, stale). `pyproject.toml` line 29 says `>=0.64.1,<0.65` (RC-032). `requirements.txt` line 129 says `==0.64.1` (RC-033). The installed package is 0.64.1 (RC-034). Action: keep 0.64.1 (D-8). The instruction line is a separate defect for a separate issue.
- **A-02 STE gate scope.** The STE row lists five files (RC-005). It omits `documentation/operator-guide.md`, `documentation/wiki/Web-Portal.md`, and the 4920 contract. The edited documents have no automatic style gate. Action: T008 checks the new text, and the requirements checklist checks style by hand. Separate issue for the gate.
- **A-03 Final tasks use read-only `gh` commands.** The Local gates table has no pull request, CI, or merge step (RC-003). T-PR, T-REMOTE-CI, and T-MERGE use `gh` reads. Auto-merge runs only after orchestrator authorization.
- **A-04 No gate reads `deploy/.env.example`.** The gates table has no row for that file (RC-003). Action: T008 case (2) checks the flag name in the file.
- **A-05 Open PR overlap on `deploy/.env.example`.** Draft PR #4208 changes `deploy/.env.example` (verified file list). A scan of all seven open pull requests found no other overlap. AGENTS.md lines 244 and 245 require a wait or handover (RC-001, RC-002). Action: T022 waits.
- **A-06 PR #4940 changed files in this change map.** PR #4940 merged on 2026-11-26. It changed `documentation/operator-guide.md`, `documentation/wiki/Web-Portal.md`, `tests/guardrails/test_hardware_shell_lock_docs.py`, `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py`, and `changelog.d/issue-4938-hardware-shell-lock.md`. Action: T005, T008, T018, and T019 edit text that main already contains. Line numbers in this record reflect main after PR #4940.
- **A-07 Site query uses the shell kind.** `websockets.js` line 69 sends `kind=shell&key=ex.createShellSession` (RC-105). The lock result for this query with both flags false is unknown (U-4). Action: T007 covers the page with both flags false. Open until the implementation run.
- **A-08 Settings attribute count.** `StreamSettings` holds nine attribute fields on lines 35 to 43 (RC-051). The change adds one field, which makes ten. Action: plan.md Complexity Tracking records the debt. A separate issue groups the lock flags.
- **A-09 Function length at the limit.** `from_environment` spans lines 46 to 69, which is 24 lines (RC-052, RC-054). One added line makes 25. Action: add no second line to that method.
- **A-10 Fake checker signature.** Line 53 of `test_hardware_routing.py` calls `check_batch(body)` (RC-118). After `check_batch` accepts `lock_scope`, the fake must forward it. Action: T006 updates the fake.
- **A-11 Guardrail test pins old text.** `test_hardware_shell_lock_docs.py` defines the refusal helper on line 112 (RC-121) and pins the steps on line 140 (RC-122). Action: T008 updates both. T008 fails until the document tasks finish.
- **A-12 Unknown output format refusal.** Spec edge case: an unknown output format returns HTTP 400. No verified line refuses an unknown format (U-9). `hardware_xml.py` lines 56 to 61 refuse site selections with `bad_request` (RC-072 covers the code mapping). Action: keep the edge case, list it as Unverified, and do not test it in this record.
- **A-13 Source of the Remote shell label.** The label "Remote shell" is in `utility_text.py` line 39 (RC-064). The page file does not contain that text. Action: the spec cites the label source.
- **A-14 Legacy record.** No folder with prefix `4939` exists under the route on main (RC-023). No legacy record applies. `existing_record.found` is false.

## 4. Unresolved items

- D-1 is the only human decision. It is the owner choice of option 1. See research.md.
- U-1 to U-10 are listed in research.md with reasons.
- The final tasks use `gh` reads (A-03).
