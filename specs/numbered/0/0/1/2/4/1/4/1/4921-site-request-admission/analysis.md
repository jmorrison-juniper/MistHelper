# Specification Analysis Report: Site Request Admission by Organization

This report checks the consistency of `spec.md`, `plan.md`, and `tasks.md` against the code on GitHub `main` (`research.md` section 3). It also lists the defects found in existing work.

## Findings

### Defects in existing work

- **F-01 (high). The site rule refuses every site request that has no ledger organization.** `request_admission.py` lines 107 and 108 on `main`. The CLI never sets an organization (`initialize_mist_session.py` line 74). Resolution: T002 and T004.
- **F-02 (medium). The per-run binding writes shared ledger state.** `session.py` lines 50 and 57 (R33 and R34). Two overlapping runs for different organizations can overwrite each other's value. A restore can then put back a stale value. Resolution: T007 and T008.
- **F-03 (medium). The binding reads a private attribute of the SDK session.** `_find_ledger` (line 60 on `main`) reads `_session` with `getattr`. A change to the SDK can break the binding without a test failure. Resolution: T007.
- **F-04 (low). The binding docstring names a context variable that `main` does not define.** `session.py` lines 4 to 7. Main has no context variable in `request_admission.py` (`research.md` section 4). Resolution: T007 removes the docstring.
- **F-05 (medium). The mistapi floor is stated three ways.** `.github/copilot-instructions.md` line 21 says `>=0.64.0,<0.65`. `pyproject.toml` line 29 says `>=0.64.1,<0.65`. `requirements.txt` line 129 pins `==0.64.1`. The constitution line 279 says `0.59+`. The installed SDK is 0.64.1. Disposition: out of scope (`spec.md` NG6). A separate issue should correct the two documents.
- **F-06 (medium). Five local working-copy files overlap this issue.** The files are `request_admission.py`, the subscription-expiry client, two test files, and `logger_utils.py`. The stat line reads 245 insertions and 13 deletions. These edits add a context-variable scope. They are not on `main`, and their owner is unknown. Disposition: excluded. Task T-PR stages by explicit path. The orchestrator must confirm the owner before any branch is cut from that checkout.
- **F-07 (low). The subscription-expiry virtual-chassis read has the same defect on `main`.** The read calls `getSiteDeviceVirtualChassis` (`client.py` line 507). The rule covers it. Task T012 verifies it.
- **F-08 (low). The shell trigger builds its path by hand.** `table.py` line 103 builds the path, and `opening.py` line 57 posts it. mistapi exposes `createSiteDeviceShellSession` (`sites/devices.py` line 2775). The constitution asks for a mistapi method where one exists. Disposition: unchanged (`spec.md` NG7). A follow-up issue should decide the replacement.
- **F-09 (low). `_build_timeout_adapter` exceeds the 25-line limit.** The function holds nested classes below line 77 (`initialize_mist_session.py` on `main`). This change touches it. Disposition: recorded in `plan.md`. A follow-up issue extracts the classes.
- **F-10 (low). The process baseline holds grandfathered entries.** `tests\guardrails\process_folder_baseline.json` lists them from line 10 onward (R13). This change adds none. A follow-up issue retires them.

### Consistency across the record

- **C-01. The symbol gate reports a removal.** The local gates table (R03) expects `no module-level name changed`. The removal of `AdmissionBinding` breaks that expectation by design. `quickstart.md` and task T-PR record the intended result. This is consistent, not a defect.
- **C-02. The patched test lambda breaks on a new argument.** `test_request_admission.py` line 120 patches `connect` with a fixed signature. Task T006 updates it. The change is consistent with FR-004.
- **C-03. The existing fail-closed test stays valid.** `test_site_request_requires_organization_context` (R51) passes with the new rule, because it uses no listing and no session organization. SC-002 records this.
- **C-04. The README is not affected.** `README.md` has no match for admission terms. The constitution asks for a README update on a behavior change. This change alters internal quota attribution only (`plan.md`, Documentation).
- **C-05. The record route is correct.** The base-5 digits of 4921 are 1, 2, 4, 1, 4, 1. Padded to eight levels, they give the route in the issue (`spec-route.ps1` line 17). The reference record for 4920 uses the same pattern (R64).
- **C-06. The shape follows the reference record.** The feature root holds five children. The `design` folder holds five children. The reference record holds the same layout.

## Coverage Summary

| Requirement | Tasks | Tests or checks |
| --- | --- | --- |
| FR-001 Learn from listings | T002, T003 | `test_listed_site_uses_the_listing_organization`, `test_listing_learning_adds_no_transport_call` |
| FR-002 Bound and eviction | T001 | `test_site_map_evicts_the_oldest_entry_at_the_bound` |
| FR-003 Resolution order | T002 | `test_listed_site_uses_the_listing_organization`, `test_unlisted_site_uses_the_session_organization`, `test_unlisted_site_fails_closed_after_other_sites_are_listed`, `test_site_request_requires_organization_context` (existing, R51) |
| FR-004 Session organization | T002, T004, T006 | `test_unlisted_site_uses_the_session_organization`, `test_adapter_counts_429_and_initializer_selects_shared_adapter` (updated) |
| FR-005 Learning never raises | T002, T003 | `test_failed_or_malformed_listing_learns_nothing` |
| FR-006 Thread safety | T001, T002 | `test_worker_thread_admits_a_listed_site_without_a_binding`, `test_concurrent_listing_and_site_reads_stay_consistent` |
| FR-007 Binding removed | T007, T008, T009 | SC-004 search, `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` (T008) |
| FR-008 No added request | T003 | `test_listing_learning_adds_no_transport_call`, SC-003 |
| FR-009 Other attribution kept | T002 | `test_ledger_hashes_auth_and_counts_org` (existing) |
| FR-010 Changelog and docs | T007, T010, T011 | `test_changelog_fragment_policy.py` (T010), `pydocstyle` (T011) |
| SC-001 New tests pass | T005 | Eight tests in `test_request_admission.py` |
| SC-002 Existing refusal holds | T002 | `test_site_request_requires_organization_context` |
| SC-005 Bound holds | T001 | `test_site_map_evicts_the_oldest_entry_at_the_bound` |
| SC-006 Local gates pass | T-LOCAL-GATES | `quickstart.md` table |

## Constitution Alignment

- **Five-item rule (I)**: Aligned. The route, the managed root, and the child counts follow `plan.md`.
- **Class-based architecture (II)**: Aligned. The new behavior belongs to `SiteOrganizationMap` and `RequestLedger`.
- **Safety first (III)**: Aligned. No secret enters the map or the logs.
- **Full pipeline (IV)**: Aligned. The delivery tasks follow the order in the constitution.
- **Observability and action logging (V and VII)**: Aligned as planned. Task T011 requires the records.
- **Inline comments (VI)**: Aligned as planned. Task T011 requires the comments.
- **mistapi as the sole interface**: Aligned. No direct HTTP call is added (F-08 notes an existing exception).

## Unmapped Tasks

None. Each task maps to at least one requirement or to Principle IV of the constitution. The delivery tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE map to SC-006 and Principle IV.

## Metrics

- Functional requirements: 10 (FR-001 to FR-010).
- Success criteria: 6 (SC-001 to SC-006).
- Tasks: 17 (T001 to T013, and four delivery tasks).
- New unit tests: 8. Updated unit tests: 1. Removed test methods: 6 (the class `TestAdmissionBinding`).
- Remote verification rows: 72. Stale: 2. Absent: 2.
- Decisions: 10. Human decisions: 0.
- Open tasks at the time of writing: 2 (T012 and T013). Tasks with status absent: 12. Tasks with status partial: 3 (T007, T008, and T009).

## Unresolved Items

- **U-1. Owner of the local working-copy edits (F-06).** The orchestrator must confirm the owner before any branch uses that checkout.
- **U-2. Correction of the mistapi floor text (F-05).** A separate issue is needed.
- **U-3. Live validation.** No token was used. The optional live check in `quickstart.md` runs only after the change exists.
- **U-4. Draft validator.** The read-only draft validator in `META_DIR` was not run. Brief rule 2 forbids script runs in this task, so the orchestrator runs that validator in its verification step.

## Convergence After Implementation

After the pull request merges, the remote rows R23 to R55 no longer hold their line numbers. The orchestrator must rerun the remote check for those rows. The rows R01, R02, R05, R07 to R22, and R56 to R72 keep their results unless the same files change.
