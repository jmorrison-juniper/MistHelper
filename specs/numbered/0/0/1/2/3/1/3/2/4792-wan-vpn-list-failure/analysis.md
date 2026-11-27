# Specification Analysis Report: Stop VPN Creation When the VPN Inventory Is Unverified

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the design files, and the code of GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only review. Each remote claim came from `gh api` on `main` or on the cited commit. Each local file used as evidence has a git blob hash that equals the remote blob SHA, except the installed mistapi files, which come from `.venv`. The review ran no build, test, or gate.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Inconsistency | HIGH | Issue #4792 body, PR #4619 body, test module line 1 | The issue names menu 164 for the builder. On `main`, the builder is menu 147 (RC-17, RC-18, RC-19). Menu 164 is the gateway template apply operation (RC-20, RC-21). | This record uses menu 147. The owner corrects the issue text. This is an owner action. |
| A2 | Defect | HIGH | `src/operations/wan/wan_vpn_builder.py` lines 390 to 406 | `_fetch_existing_vpns` returns an empty list after an exception (RC-02). It never checks the status of the list response (RC-03). A failed read looks like an empty inventory. | Fixed by FR-001 to FR-004, T002, and T003. |
| A3 | Defect | HIGH | `wan_vpn_builder.py` line 394 (RC-04), and mistapi `__pagination.py` lines 33 to 36 and 62 (RC-55, RC-56) | `mistapi.get_all` appends later pages without a status check. It stops silently when the next link is empty. A later failure can return a partial inventory. | Fixed by FR-009 and FR-011. The reader calls `mistapi.get_next` and checks each page. |
| A4 | Defect | HIGH | mistapi `__api_response.py` lines 41 and 84 (RC-57, RC-58) | `APIResponse.next` starts as None. It is set only when the headers show more pages. Missing or invalid headers leave `next` as None, so a partial page looks complete. | Fixed by FR-005 to FR-007. Missing headers make the inventory unavailable. The header assumption stays open (A11). |
| A5 | Defect in existing work | HIGH | Commit `8d8f1a63c` (RC-42, RC-43) | The candidate treats a None next link as a complete inventory. The owner review says that gap remains. The candidate adds three methods to `WanVpnBuilder`, which breaks Principle I (RC-70). The branch is 42 commits behind `main`. | Not reused. Decision D-11 starts a fresh branch from `main`. |
| A6 | Test defect | MEDIUM | Test module lines 322 to 333 (RC-13, RC-14) | The existing test asserts an empty list after an API error. The test encodes the defect. A second test patches `mistapi.get_all`. | Replaced by T001. |
| A7 | Operator-visible defect | MEDIUM | `wan_vpn_builder.py` line 432 (RC-07) | After a failed read, the display prints "No existing VPN definitions in this organization." | Fixed by FR-012. The display does not run after an unavailable read. |
| A8 | Gap | MEDIUM | `wan_vpn_builder.py` lines 134 and 137 (RC-06) | The name prompt runs after a failed read. No branch stops the flow. | Fixed by FR-012. |
| A9 | Gap | MEDIUM | `wan_vpn_builder.py` line 554 (RC-10) | The duplicate check compares the entered name with stored names. The stored names keep any surrounding spaces. | Fixed by FR-014. Names are stripped and compared without case. |
| A10 | Same defect class | MEDIUM | `src/operations/wan/wan_hub_group_manager.py` lines 170 to 185 (RC-12) | The hub group manager returns `[], []` after an exception and uses `get_all`. | Out of scope (decision D-17). The owner files a separate issue. |
| A11 | Unverified assumption | MEDIUM | `documentation/mist-api-openapi31yaml.yaml` (RC-67). Upstream fetch failed. | The local OpenAPI file does not document the `X-Page-*` headers. The upstream Mist page for `listOrgVpns` could not be fetched. | Open. T-HEADER-CHECK runs before merge. `plan.md` gives the rollback if the headers are absent. |
| A12 | Mist API coverage | LOW | OpenAPI lines 23529 to 23540 (RC-63) | The OpenAPI file lists responses 400, 401, 403, 404, and 429 for `listOrgVpns`. It lists no 5xx response. | Accepted. FR-002 covers each status outside 200 through 299. |
| A13 | Version mismatch | LOW | `pyproject.toml` line 29 (RC-68), and `requirements.txt` line 129 (RC-69) | The brief states `mistapi>=0.64.0,<0.65`. `pyproject.toml` requires `>=0.64.1,<0.65`. The installed version 0.64.1 satisfies both. | Recorded. The plan follows `pyproject.toml`. The owner aligns the brief and the instructions. This is an owner action. |
| A14 | Gate risk | HIGH | `tests/integration/test_wan_vpn_builder_live.py` lines 48 and 139 (RC-16) | The live test deletes and creates VPNs in a live organization. It needs `MIST_APITOKEN` from `.env`. The full shards collect it. | Fixed by decision D-18. Local runs skip the shards, and CI runs them. Whether CI exposes the token is Unverified (`research.md`). |
| A15 | Documentation drift | LOW | `documentation/architecture.md` line 260 | The architecture page names `src/wan_*.py`, an old path. The builder lives under `src/operations/wan/`. | Not changed. The change does not alter the architecture. A separate documentation issue covers it. |
| A16 | Legacy record | MEDIUM | Commit `8d8f1a63c`: record folder (RC-51), changelog (RC-49), helper names (RC-50), and the task list that marks each task as delivered | Four legacy claims are absent on `main` (RC-47, RC-48, RC-49, RC-50). One legacy claim is partial (RC-51). Three legacy claims match `main` (RC-44, RC-45, RC-46). | This record replaces the legacy draft. The counts are in `STATUS.json` and `research.md`. |
| A17 | Generated documentation | LOW | `documentation/menu-api/interactive.md` line 582 (RC-23) | The generated map names `WanVpnBuilder._fetch_existing_vpns` as the call site for `listOrgVpns`. | Fixed by T005 after T003. |
| A18 | Gate risk | MEDIUM | `symbol-diff` gate | The new import adds a module-level name. The gate may report the addition. | Accepted. The pull request explains that the import adds a name and removes none. |
| A19 | Stale documentation text | LOW | Builder module line 1 and test module line 1 | Both docstrings say "Menu 164". | Not changed in this change. The owner files a separate issue. |
| A20 | Existing folder debt | LOW | `changelog.d/` (RC-37) and `specs/` (RC-45) | Both folders hold more children than the five-item rule allows. | Recorded in `plan.md` Complexity Tracking. The change adds only its own unique records. |
| A21 | Gate ambiguity | MEDIUM | `pytest-chunks` shards (`copilot-instructions.md` local gates) | The local shards collect the live integration test. The gate table lists the shards as a local gate. | Decision D-18 moves the shards to CI. The pull request records the reason. |

## Coverage Summary

| Requirement | Tests | Tasks | Notes |
|-------------|-------|-------|-------|
| FR-001 | Case 3 | T001, T002 | Exception from `listOrgVpns`. |
| FR-002 | Cases 4 and 5 | T001, T002 | Non-2xx on the first page and on a later page. |
| FR-003 | Case 6 | T001, T002 | Data that is not a list. |
| FR-004 | Case 7 | T001, T002 | Seven invalid record and name shapes. |
| FR-005 | Case 8 | T001, T002, T-HEADER-CHECK | Missing pagination headers. |
| FR-006 | Case 9 | T001, T002 | Headers show more records but no next link. |
| FR-007 | Case 10 | T001, T002 | Repeated next link. |
| FR-008 | Cases 11 and 12 | T001, T002 | Page beyond the declared count and changed total. |
| FR-009 | Case 5 (second case) | T001, T002 | `get_next` returns no response. |
| FR-010 | Case 2 | T001, T002 | Verified empty inventory. |
| FR-011 | Case 1 | T001, T002 | Asserts that `get_all` is not called. |
| FR-012 | Case 13 | T001, T003 | No prompt and no create call. |
| FR-013 | Cases 3 and 13 | T001, T003 | Message text and stop line. |
| FR-014 | Cases 14 and 15 | T001, T003 | Duplicate on page 2, and case and space variants. |
| FR-015 | Existing `test_api_failure_skips_profile_update` | T003 | The `CREATE` prompt stays unchanged. |
| FR-016 | Method count check (SC-006) | T003 | `WanVpnBuilder` gains no method. |
| FR-017 | Case 1 (log assertions) | T001, T002 | Info and debug lines for each call. |
| FR-018 | Guard test `tests/guardrails/test_changelog_fragment_policy.py` (T-LOCAL-GATES item 6) | T004, T005, T006 | Changelog, menu regeneration, and record copy. |

## Unresolved Items

1. **Pagination headers (A11)**: Mist must send the three headers on each 2xx page. T-HEADER-CHECK tests this before merge.
2. **Menu number in the issue (A1)**: The owner corrects the issue text. This record does not edit GitHub.
3. **Hub group manager (A10)**: The owner files a separate issue.
4. **Human review before merge**: The owner comment on issue #4792, dated 2026-11-17, says that human safety review remains required before merge. T-MERGE records this gate.
5. **CI token exposure**: Whether CI exposes `MIST_APITOKEN` to the integration shard is Unverified. The CI workflow was not read for secrets.
6. **Stale text (A15, A19)**: The architecture page and two docstrings name old paths or menu 164. The owner files a separate documentation issue.

## Remote Verification Summary

The remote table in `design/research.md` holds 73 checks. Of these, 63 are present, 8 are absent, and 2 are partial. Eight checks are legacy claims. Of the legacy claims, 3 are verified, 1 is stale, and 4 are absent.
