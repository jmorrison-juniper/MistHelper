# Research: Stop VPN Creation When the VPN Inventory Is Unverified

This file holds the decisions, the remote verification table, the sources, and the unverified items. Each decision names its alternatives, the chosen option, the reason, and the risk.

## Method and Truth Order

1. GitHub `main` outranks local files. Each remote claim came from `gh api` on `main`, or on the commit that the claim names.
2. A local file counts as evidence only when its git blob hash equals the remote blob SHA. The check used `git hash-object`, which writes nothing. All repository files cited here passed that check.
3. Installed mistapi files come from `.venv\Lib\site-packages\mistapi`. Their blob column holds the git blob hash of the installed file. Their ref column holds `local`.
4. For commit rows, the blob column holds the commit SHA. For folder rows, the blob column holds `none`.
5. `line` holds the line number that the check cites. A value of `0` means that the check names a file, a folder, a commit, or a count.
6. Legacy claims come from the draft of issue #4792 on commit `8d8f1a63c58cb238d010bcd66cfec614caae4905`. Each legacy claim is a draft to verify, not proof.
7. No build, test, lint, formatter, package install, container, or repository script ran during this research.

## Issue and Linked Work Facts

- Issue #4792 is open. Its title is "[Bug]: WAN VPN builder treats a failed VPN list as empty." Its labels are `bug`, `in-progress`, and `src`. It was created on 2026-11-13 and updated on 2026-11-17. Its author is `jmorrison-juniper`.
- Reproduction steps in the issue body. (1) Mock `listOrgVpns` or its pagination to fail while an existing VPN has a known name. (2) Run `WanVpnBuilder.run()` with that mock. (3) Enter the existing VPN name and the typed confirmation. (4) Observe whether `createOrgVpn` runs after the failed read. The issue requires mocked calls only and no run of menu 164 against a live organization.
- Error text in the issue: `! Error retrieving VPN definitions. Check API connectivity.`
- The issue body names main commit `53ad73cc37dc0821faca093441ecd12268e6a75d` as the static review base. That commit is an ancestor of `main` (RC-40).
- Owner comment of 2026-11-17: the local candidate `8d8f1a63c` is unpublished. An independent review found a pagination gap. `mistapi` 0.64 sets `APIResponse.next` to None, and that value can stay None when pagination headers are incomplete or invalid. The owner adds mocked native-response controls and a fail-closed repair. No live Mist request or VPN action ran. The typed `CREATE` confirmation remains. Human safety review remains required before merge.
- Linked pull requests: `gh pr list --search 4792` returned only PR #4619. Its state is MERGED, merged on 2026-11-13 at 08:54:28 UTC. Its head branch is `jmorrison-juniper-fix-4564-wan-vpn-profile-503`. Its title is "fix(wan-vpn): reject profiles from failed responses." Its body links issue #4564, which is closed. Its body states that menu 164 is destructive. That statement conflicts with RC-17 to RC-20.
- Repository labels relevant to this change: `needs-human-review` ("A human must review this before merge. Touches a destructive operation or a safety path."), `auto-merge`, and `destructive`.
- Legacy draft: commit `8d8f1a63c` holds a record folder `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure`, a changelog fragment `changelog.d/issue-4792-wan-vpn-list-failure.md`, and changes to the builder and the unit test module. Every legacy task is marked as delivered. Section "Remote Verification" records which legacy claims hold on `main`.

## Decisions

### D-1. Menu identity

- **Decision**: The record names menu 147 for the WAN VPN builder. Menu 164 is the gateway template apply operation.
- **Alternatives considered**: (a) Keep the menu number from the issue, which is 164. (b) Use the registration in `MistHelper.py` and the registry, which is 147.
- **Rationale**: `MistHelper.py` registers `WanVpnBuilder.execute` under `"147"` (RC-17, RC-18). The registry lists 147 as interactive (RC-19). Menu 164 registers the gateway template apply operation (RC-20, RC-72).
- **Risk**: The issue text stays wrong until the owner corrects it.

### D-2. Result signal of the reader

- **Decision**: `VpnInventoryReader.read` returns None for an unavailable inventory. It returns an empty list only for a verified empty inventory.
- **Alternatives considered**: (a) Raise a typed exception from `read`. (b) Return a pair of a flag and a list. (c) Return a sentinel object.
- **Rationale**: The profile path already returns None for an invalid read (RC-44). `_fetch_existing_vpns` is the only caller of the reader, and the tests cover that caller.
- **Risk**: A future caller that ignores None would treat an unavailable inventory as data. The contract file states the rule.

### D-3. Paging method

- **Decision**: The reader calls `mistapi.get_next` for each later page. It does not call `mistapi.get_all`.
- **Alternatives considered**: (a) Keep `get_all` and check only the first page. (b) Send a direct HTTP request for each page. (c) Patch the pinned mistapi package.
- **Rationale**: `get_all` appends later pages without a status check (RC-56). A direct HTTP request breaks the Mist transport rule in the constitution (RC-28 region). Patching a pinned package changes the supply chain, so it stays out of scope.
- **Risk**: `get_next` returns the response for a failed page. The reader checks each page (FR-002).

### D-4. Completeness proof

- **Decision**: Each page carries three integer headers. A page without a next link is the last page only when the limit times the page is at least the total.
- **Alternatives considered**: (a) Treat a next link of None as complete. (b) Use a short-page rule, which accepts a page with fewer records than the limit. (c) Use the record count from the list response.
- **Rationale**: A next link of None does not prove completeness (RC-57, RC-58). A short-page rule depends on a page size that the server can change. The record does not depend on a page size.
- **Risk**: If Mist omits a header on complete pages, every run stops. T-HEADER-CHECK tests this before merge.

### D-5. Bounded paging

- **Decision**: The reader stops with an unavailable result when a page number exceeds the declared page count, when the limit or the total changes, or when a next link repeats.
- **Alternatives considered**: (a) Check only for a repeated link. (b) Use a fixed page cap constant.
- **Rationale**: The declared page count comes from the first page headers. The rule needs no constant that the repository does not define.
- **Risk**: A change in the total during a read makes the inventory unavailable. The operator runs the menu again.

### D-6. Names

- **Decision**: Each record must be an object with a nonblank string `name`. The reader compares names after trimming and without case.
- **Alternatives considered**: (a) Skip records without a name. (b) Keep `.get("name", "")` and accept a blank name.
- **Rationale**: The `vpn` schema requires `name` and sets `minLength` to 1 (RC-65, RC-66). A record without a usable name cannot be checked for a duplicate, so it can hide a collision.
- **Risk**: An unexpected record shape stops the menu. The stop line tells the operator that no VPN was created.

### D-7. Placement of the new logic

- **Decision**: The logic lives in the new module `src/operations/wan/vpn_inventory.py` in the class `VpnInventoryReader`. `WanVpnBuilder` gains no method.
- **Alternatives considered**: (a) Add private methods to `WanVpnBuilder`. (b) Create a subpackage under `src/operations/wan/`.
- **Rationale**: `WanVpnBuilder` already defines more than five methods (RC-70), and the constitution forbids a new child under a noncompliant parent (RC-27). `src/operations/wan/` has four children (RC-34), so one new module keeps the folder at five, which is the limit. A subpackage would add a child and more files.
- **Risk**: The folder reaches its limit. A later change must place new modules elsewhere.

### D-8. Stop point

- **Decision**: The builder stops before the VPN list display, the name prompt, the profile list display, the preview, the typed confirmation, and the create call.
- **Alternatives considered**: (a) Stop only before the create call. (b) Stop after the name prompt.
- **Rationale**: The operator must not enter a name that the tool cannot check. Option (a) still asks for a name with no duplicate check. Option (b) still asks the operator to type a name.
- **Risk**: None beyond the stop itself.

### D-9. Typed confirmation

- **Decision**: The word `CREATE` (RC-08) and the `safe_input` prompt stay unchanged.
- **Alternatives considered**: (a) Change the word. (b) Remove the prompt from the create path.
- **Rationale**: The constitution requires a typed confirmation for changes to the Mist cloud (RC-28). This change does not alter that confirmation.
- **Risk**: None.

### D-10. Test approach

- **Decision**: The tests wrap `requests.Response` objects in mistapi `APIResponse` objects. They do not call a live organization.
- **Alternatives considered**: (a) Use `SimpleNamespace` objects, as the current tests do. (b) Make a live read-only request in a test.
- **Rationale**: The status, header, and next-link rules belong to mistapi `APIResponse` (RC-57 to RC-59). A `SimpleNamespace` object does not reproduce those rules. The issue requires mocked calls only. The helper `_native_response` (RC-15) gives the pattern.
- **Risk**: The tests depend on requests and mistapi internals. The pinned version (RC-52, RC-69) limits that risk.

### D-11. The candidate commit

- **Decision**: The fix starts from `main` on a new branch. The candidate commit `8d8f1a63c` is not rebased, merged, or cherry-picked.
- **Alternatives considered**: (a) Rebase the candidate branch. (b) Cherry-pick the candidate test and the candidate code.
- **Rationale**: The candidate is 42 commits behind `main` and 2 commits ahead (RC-43). It treats a next link of None as complete (A5 in `analysis.md`). It adds three methods to `WanVpnBuilder` (RC-70). The Conflicts section of `AGENTS.md` requires a fresh start from `main` when a conflict covers more than 20 lines.
- **Risk**: Work on the candidate branch is set aside. The record cites it as a design reference.

### D-12. Generated documentation

- **Decision**: Run both generators after T003. Commit only the files that change. Run the menu API check a second time and confirm that it changes no file.
- **Alternatives considered**: (a) Edit the generated pages by hand. (b) Leave the generated pages stale.
- **Rationale**: The menu reference gate reports stale generated pages (`documentation/quality-gates.md` table, row `menu_reference_drift`). Hand edits drift from the generator output.
- **Risk**: The regeneration may change more lines than this change. T005 checks the second run.

### D-13. Merge gate

- **Decision**: The pull request carries no `auto-merge` label. A human owner reviews the change before merge.
- **Alternatives considered**: (a) Enable auto-merge after CI, as the brief default allows. (b) Merge without owner review.
- **Rationale**: The owner comment on issue #4792, dated 2026-11-17, states that human safety review remains required before merge. `AGENTS.md` (RC-24) keeps the stricter rule for destructive operations, and the rule for destructive operations applies here as a stricter gate.
- **Risk**: The merge waits for the owner review.

### D-14. Labels

- **Decision**: Add `needs-human-review`. Keep `bug`, `src`, and `in-progress`. Do not add `destructive`.
- **Alternatives considered**: (a) Add `destructive`. (b) Add no label.
- **Rationale**: The label `needs-human-review` has the description "A human must review this before merge. Touches a destructive operation or a safety path." The registry places menu 147 in the `interactive` category and sets `destructive=False` (RC-19, RC-71). Adding `destructive` would contradict the registry.
- **Risk**: A reader may expect the `destructive` label. The record states the reason.

### D-15. Changelog file name

- **Decision**: The fragment is `changelog.d/issue-4792-wan-vpn-list-failure.md`.
- **Alternatives considered**: (a) Use `pr-<number>.md`, which needs an open pull request. (b) Use a date name.
- **Rationale**: `changelog.d/README.md` names the issue form when the issue exists and the pull request does not.
- **Risk**: The file name stays the same after the pull request opens. Renaming would create a delete and an add.

### D-16. Record route and slug

- **Decision**: The record folder is `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure`. The slug matches the legacy draft.
- **Alternatives considered**: (a) Use a new slug. (b) Use a route from another method.
- **Rationale**: `.specify/scripts/powershell/spec-route.ps1` converts the number 4792 to base 5 with eight digits (RC-33). The result is 00123132, which gives the route 0/0/1/2/3/1/3/2. The slug keeps the name of the legacy draft.
- **Risk**: None. The route folder is absent on `main` (RC-38), so the change creates it.

### D-17. Scope

- **Decision**: `WanHubGroupNumberManager` (`src/operations/wan/wan_hub_group_manager.py`, lines 170 to 185) is out of scope. The owner files a separate issue.
- **Alternatives considered**: (a) Fix both operations in one pull request. (b) Leave the hub group manager unmentioned.
- **Rationale**: One issue holds one subject (`AGENTS.md`, Issue first). The hub group manager returns an empty tuple after an exception (RC-12).
- **Risk**: Menu 146 keeps the defect until the separate issue lands.

### D-18. Gates

- **Decision**: Run every applicable local gate except the two `pytest-chunks` shards. CI runs the shards and the coverage run.
- **Alternatives considered**: (a) Run the shards locally. (b) Run no gate locally and rely on CI.
- **Rationale**: `tests/integration` holds the live test (RC-16). The test deletes VPNs and needs `MIST_APITOKEN` from `.env`. A local shard run can reach a live organization. The file has no token-based skip marker (see Unverified item 5).
- **Risk**: The shard result appears only in CI.

### D-19. Owner check before merge

- **Decision**: The owner runs one read-only `listOrgVpns` request before merge and records the header names. The result decides whether the merge continues.
- **Alternatives considered**: (a) Merge without the check. (b) Add a live test to the repository.
- **Rationale**: Decision D-4 depends on the presence of the headers, which the local OpenAPI file does not document (RC-67). A live test breaks the rule that tests use mocks only.
- **Risk**: The merge waits for the owner. A missing header stops the merge and triggers the rollback in `plan.md`.

## Remote Verification

Each row is one check. The row count equals the count in `STATUS.json` `remote_checks`. Result values are `present`, `absent`, `partial`, and `stale`. Rows RC-44 to RC-51 are legacy claims.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RC-01 | The builder module defines the class `WanVpnBuilder`. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 57 |
| RC-02 | `_fetch_existing_vpns` returns an empty list after an exception. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 406 |
| RC-03 | The list response is used without a status check. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 393 |
| RC-04 | The VPN fetch uses `mistapi.get_all` for pagination. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 394 |
| RC-05 | The operator error text is in the VPN fetch failure path. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 404 |
| RC-06 | The name flow calls the VPN fetch and has no unavailable branch. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 134 |
| RC-07 | The display prints a placeholder for an empty VPN list. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 432 |
| RC-08 | The typed confirmation constant `CONFIRM_TOKEN` equals `CREATE`. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 41 |
| RC-09 | `createOrgVpn` is called inside `_create_vpn`. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 411 |
| RC-10 | The duplicate check compares lowercase names. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 554 |
| RC-11 | The profile pagination helper calls `mistapi.get_next`. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 364 |
| RC-12 | The hub group manager returns empty lists after an exception. | src/operations/wan/wan_hub_group_manager.py | main | 5b6d5c9a393ef0b051c5905df9c8aca69b9035a2 | present | 185 |
| RC-13 | The existing unit test asserts an empty list after an API error. | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | present | 333 |
| RC-14 | The existing unit test patches `mistapi.get_all` for the VPN fetch. | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | present | 322 |
| RC-15 | The native-response helper exists in the profile refusal tests. | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | present | 604 |
| RC-16 | The live integration test calls `deleteOrgVpn`. | tests/integration/test_wan_vpn_builder_live.py | main | 7c6f0999275a33ccc013db8b773e368417419b45 | present | 48 |
| RC-17 | Menu 147 registers the WAN VPN builder. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6170 |
| RC-18 | The menu 147 handler calls `WanVpnBuilder.execute`. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6172 |
| RC-19 | The registry lists menu 147 in the `interactive` category. | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 256 |
| RC-20 | The registry lists menu 164 in the `destructive` category for gateway template apply. | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 199 |
| RC-21 | The operator guide states that menu 164 applies gateway templates. | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 118 |
| RC-22 | The menu reference lists menu 147 as WAN Hub-Spoke VPN Builder. | documentation/menu_reference.md | main | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 184 |
| RC-23 | The interactive API map lists the builder call site for `listOrgVpns`. | documentation/menu-api/interactive.md | main | ec5402f333e691cb9a490177932603df1b38bc7d | present | 582 |
| RC-24 | `AGENTS.md` keeps auto-merge away from pull requests that change a destructive operation. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 231 |
| RC-25 | `.github/copilot-instructions.md` holds the local gates table. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 55 |
| RC-26 | `.github/copilot-instructions.md` names the managed spec roots. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| RC-27 | Constitution Principle I forbids a direct child under a noncompliant parent. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 |
| RC-28 | Constitution Principle III requires typed confirmation for changes to the Mist cloud. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 120 |
| RC-29 | The CI mypy scope is `MYPY_PATHS`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-30 | The CI vulture scope is `VULTURE_PATHS`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-31 | The CI pydocstyle scope is `PYDOCSTYLE_PATHS`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-32 | The CI interrogate scope is `INTERROGATE_PATHS`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-33 | The route function uses base 5 with eight digits. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-34 | The folder `src/operations/wan/` has four direct children before the change. | src/operations/wan/ | main | none | present | 0 |
| RC-35 | The folder `src/operations/` has five direct children. | src/operations/ | main | none | present | 0 |
| RC-36 | The folder `specs/numbered/0/0/1/2/3/1/` has three direct children. | specs/numbered/0/0/1/2/3/1/ | main | none | present | 0 |
| RC-37 | The folder `changelog.d/` holds 335 direct children. | changelog.d/ | main | none | present | 0 |
| RC-38 | The route folder `specs/numbered/0/0/1/2/3/1/3/2/` is absent. | specs/numbered/0/0/1/2/3/1/3/2/ | main | none | absent | 0 |
| RC-39 | No path on `main` contains the digits 4792. | git tree of main | main | none | absent | 0 |
| RC-40 | The base commit `53ad73cc` is an ancestor of `main`. | commit 53ad73cc37dc0821faca093441ecd12268e6a75d | main | 53ad73cc37dc0821faca093441ecd12268e6a75d | present | 0 |
| RC-41 | The PR #4619 squash commit `d50172f3` is on `main`. | commit d50172f33f8fdbae14b769851e4f34a4a812de6c | main | d50172f33f8fdbae14b769851e4f34a4a812de6c | present | 0 |
| RC-42 | The commits API returns the candidate commit `8d8f1a63`. | commit 8d8f1a63c58cb238d010bcd66cfec614caae4905 | 8d8f1a63c58cb238d010bcd66cfec614caae4905 | 8d8f1a63c58cb238d010bcd66cfec614caae4905 | present | 0 |
| RC-43 | The candidate commit `8d8f1a63` is not an ancestor of `main` (diverged, ahead 2, behind 42). | commit 8d8f1a63c58cb238d010bcd66cfec614caae4905 | main | 8d8f1a63c58cb238d010bcd66cfec614caae4905 | partial | 0 |
| RC-44 | Legacy: the gateway profile pagination pattern exists on `main`. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 352 |
| RC-45 | Legacy: the `specs/` root holds 795 direct children. | specs/ | main | none | present | 0 |
| RC-46 | Legacy: the `get_all` alternative matches the current VPN fetch. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 394 |
| RC-47 | Legacy: the builder stops before the name prompt when the inventory fails. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | absent | 137 |
| RC-48 | Legacy: a pagination failure test exists in the unit test module. | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | absent | 319 |
| RC-49 | Legacy: the changelog fragment `issue-4792-wan-vpn-list-failure.md` exists on `main`. | changelog.d/issue-4792-wan-vpn-list-failure.md | main | none | absent | 0 |
| RC-50 | Legacy: the helpers `_validated_vpn_page` and `_fetch_next_vpn_page` exist. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | absent | 390 |
| RC-51 | Legacy: the record folder with `spec.md` exists on the candidate commit only. | specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/spec.md | 8d8f1a63c58cb238d010bcd66cfec614caae4905 | d9ecc9bf1a02ffd2752b587e97f467d273111142 | partial | 0 |
| RC-52 | mistapi 0.64.1 is installed. | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 0 |
| RC-53 | `listOrgVpns(mist_session, org_id, limit, page)` is defined. | .venv\Lib\site-packages\mistapi\api\v1\orgs\vpns.py | local | fb72b5dadf4a5e46578b3c0c381a2884d61320ad | present | 17 |
| RC-54 | `createOrgVpn(mist_session, org_id, body)` is defined. | .venv\Lib\site-packages\mistapi\api\v1\orgs\vpns.py | local | fb72b5dadf4a5e46578b3c0c381a2884d61320ad | present | 58 |
| RC-55 | `get_next` returns None when the response has no next link. | .venv\Lib\site-packages\mistapi\__pagination.py | local | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 33 |
| RC-56 | `get_all` appends later pages without a status check. | .venv\Lib\site-packages\mistapi\__pagination.py | local | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 62 |
| RC-57 | `APIResponse.next` starts as None. | .venv\Lib\site-packages\mistapi\__api_response.py | local | 2d878d79295fec79e6409f6243132c53280f15ab | present | 41 |
| RC-58 | The header-based next link requires limit times page below the total. | .venv\Lib\site-packages\mistapi\__api_response.py | local | 2d878d79295fec79e6409f6243132c53280f15ab | present | 84 |
| RC-59 | The request wrapper returns an `APIResponse` after an HTTP error. | .venv\Lib\site-packages\mistapi\__api_request.py | local | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 258 |
| RC-60 | The mistapi package exports `get_next`. | .venv\Lib\site-packages\mistapi\__init__.py | local | f6fca30f4088d763e76f3072d02a3095d46852b9 | present | 16 |
| RC-61 | The OpenAPI file defines the `listOrgVpns` operation. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 23524 |
| RC-62 | The OpenAPI operation for `listOrgVpns` lists the `limit` and `page` parameters. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 23526 |
| RC-63 | The OpenAPI operation for `listOrgVpns` lists an HTTP 5xx response. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 23540 |
| RC-64 | The OpenAPI file defines the `createOrgVpn` operation. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 23548 |
| RC-65 | The OpenAPI `vpn` schema requires `name`. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 117807 |
| RC-66 | The OpenAPI `vpn` name property has `minLength` 1. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 117790 |
| RC-67 | The OpenAPI file documents the `X-Page-*` pagination headers. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| RC-68 | `pyproject.toml` requires mistapi `>=0.64.1,<0.65`. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-69 | `requirements.txt` pins mistapi `0.64.1`. | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-70 | `WanVpnBuilder` defines more than five methods. | src/operations/wan/wan_vpn_builder.py | main | 1c407072e93fb771e90da5ef367a2e14e1346b3d | present | 65 |
| RC-71 | The menu 147 entry sets `destructive=False`. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6177 |
| RC-72 | The menu 164 entry registers the gateway template apply operation. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5106 |
| RC-73 | The test module docstring names menu 164. | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | present | 1 |

Result counts: 63 present, 8 absent (RC-38, RC-39, RC-47, RC-48, RC-49, RC-50, RC-63, RC-67), and 2 partial (RC-43, RC-51). Legacy results: RC-44, RC-45, and RC-46 are present. RC-47, RC-48, RC-49, and RC-50 are absent. RC-51 is partial.

## Sources

Local repository files (blob hash equal to the remote blob):

- `AGENTS.md` (lines 48, 231, and the Git flow and Issue first sections).
- `.github/copilot-instructions.md` (Local gates table, Spec Kit layout, Required labels, Changelog section).
- `.specify/memory/constitution.md` (Principles I, III, and VII, and Technology constraints).
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The record follows their headings.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (reference record). The record copies its shape, not its content.
- `documentation/quality-gates.md` (sections "Run a gate on your own machine" and "The writing gate").
- `documentation/operator-guide.md` (line 118).
- `documentation/menu_reference.md` (line 184).
- `documentation/menu-api/interactive.md` (lines 555, 582, and 583).
- `documentation/MIST_API_GET_ENDPOINTS.md` (line 980) and `documentation/MIST_API_MISSING_ENDPOINTS.md` (line 927). These list `listOrgVpns` at `/api/v1/orgs/{org_id}/vpns` with the mistapi module path. They say nothing about pagination headers.
- `documentation/architecture.md` (lines 247 and 260) and `documentation/development-setup.md` (lines 40, 268, 272, 281, 308, and 370), read by search. No decision depends on them.
- `documentation/container-deployment.md`. Its headings include "Test and debug containers" at line 141. The change runs no container, so the section does not apply.
- `documentation/mist-api-openapi31yaml.yaml` (RC-61 to RC-67).
- `.specify/scripts/powershell/spec-route.ps1` (RC-33).
- `src/operations/wan/wan_vpn_builder.py`, `wan_hub_group_manager.py`, and `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`, read through the remote contents API on `main`.
- `tests/integration/test_wan_vpn_builder_live.py` (RC-16), read by search.
- `pyproject.toml` (RC-68) and `requirements.txt` (RC-69).
- Skills: no skill was loaded. The issue concerns Python control flow in a menu operation and the mistapi SDK. It does not concern Podman or Juniper device behavior.

Installed mistapi source (local path, blob equals the git blob hash of the file):

- `.venv\Lib\site-packages\mistapi\api\v1\orgs\vpns.py` (RC-53, RC-54).
- `.venv\Lib\site-packages\mistapi\__pagination.py` (RC-55, RC-56).
- `.venv\Lib\site-packages\mistapi\__api_response.py` (RC-57, RC-58).
- `.venv\Lib\site-packages\mistapi\__api_request.py` (RC-59).
- `.venv\Lib\site-packages\mistapi\__init__.py` (RC-60).
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` (RC-52).

GitHub API reads (read-only): issue #4792, PR #4619, the commits `53ad73cc`, `8d8f1a63c`, and `d50172f33`, the compare API for `main` against `8d8f1a63c` and for `53ad73cc` against `main`, the git trees for `main` and the candidate commit, and the contents of the files above.

Web fetch: one attempt to read `https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/vpns/list-org-vpns`. The URL is linked from `documentation/menu-api/interactive.md` lines 555 and 582. The fetch failed. The address redirected to `networkingdocs.hpe.com`, and the fetch tool blocked that address as private. No upstream content is cited.

## Unverified

1. **Mist pagination headers**: Mist may not send `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` on every 2xx page of `listOrgVpns`. Reason: the local OpenAPI file does not document them (RC-67), and the upstream page could not be fetched. Mitigation: T-HEADER-CHECK (D-19).
2. **Status for a failed list request**: Mist may return a 5xx status for `listOrgVpns` when the service fails. Reason: the OpenAPI file lists no 5xx response (RC-63). The decision does not depend on the answer, because FR-002 treats each status outside 200 through 299 as a refusal.
3. **CI token exposure**: CI may expose `MIST_APITOKEN` to the integration shard. Reason: the CI workflow was not read for secrets. Mitigation: local shards are skipped (D-18), and the CI result is reviewed in T-REMOTE-CI.
4. **Runtime behavior for a 503 with a list body**: The behavior of the current code was not executed. Reason: the brief forbids test runs during research. Source evidence is RC-56 and RC-59. Mitigation: T001 tests the case with native response objects.
5. **Skip behavior of the live test**: The live test may fail, rather than skip, without a token. Reason: the file has `pytest.skip` calls only for empty data (search lines 96, 112, and 217). It states that it requires `MIST_APITOKEN` and `MIST_ORG_ID` from `.env`.
6. **Deletion scope of the live test**: The live test deletes a VPN at line 48. Reason: the fixture that calls the delete was not read in full. The spec treats the deletion as a warning.
7. **Gate outputs**: The outputs of `symbol-diff`, the menu generators, the test-quality analyzer, and the safe sweep are not known. Reason: the brief forbids gate runs during research. T-LOCAL-GATES records the actual results.
