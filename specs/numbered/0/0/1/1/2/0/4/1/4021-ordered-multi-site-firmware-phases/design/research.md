# Research: Ordered Multi-Site Firmware Families

Each decision names the chosen option, the reason, the alternatives, and the risk. Remote evidence appears in section 4. Each row there has one matching object in `META/4021-STATUS.json`.

## 1. Issue Facts

- **Issue**: #4021, `feat(upgrade): enforce ordered multi-site firmware phases`. State: open. Author: `jmorrison-juniper`. Created 2026-10-06. Last update 2026-11-10.
- **Labels**: `feature`, `firmware`, `src`, `severity:high`, `needs-human-review`.
- **Parent**: #3332, child 3 of 4. The parent is closed.
- **Subject**: Submit multi-site firmware children in the canonical family order, and stop later children after a failed family gate.
- **Manifest**: `src/operations/execution/firmware/aggregate_upgrade_service.py` and `tests/unit/firmware/test_aggregate_upgrade_service.py`.
- **Decisions consumed**: Decisions 1, 2, and 3 approved on child #4020 (comment of 2026-10-07T05:17:21Z). The decisions are the phase limit, the upstream proof, and the no-retry rule.
- **Smallest test boundary**: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py`.
- **Comments**: The 2026-10-07 assessment says that a spec is required before code. The 2026-11-10 correction says that #4109 merged and that #4701 changes the manifest files. Both points are checked in section 2.
- **Child #4020 comments**: The 2026-10-07 comment states that `clients` has no firmware plan. The owner decision comment states the submission order gateways, switches, then access points. SSR belongs to the gateway phase.

## 2. Linked Work

`gh pr list --search "4021"` returned no pull request. The linked pull requests named in the issue comments were checked by number.

| Number | Title | State | Merged | Relevance |
| - | - | - | - | - |
| #4109 | feat(upgrade): enforce ordered single-site firmware phases | MERGED | 2026-10-12T22:31:34Z | Closes #4020. Adds `PLAN_FAMILY_ORDER` (row 9) and the single-site submitter (row 14). It changes `driver.py`, `wiring.py`, `upgrade_service.py`, and `signals.py`. It does not change the aggregate module. |
| #4701 | fix(upgrade-portal): keep site locks after uncertain replies | MERGED | 2026-11-13T04:56:25Z | Changes `aggregate_upgrade_service.py` (+76, -11), `upgrade_service.py` (+13, -1), and `tests/unit/firmware/test_aggregate_upgrade_service.py` (+624, -2). The change is the current base of this design. |
| #4075 | Changes `driver.py` lines 10 to 14 | MERGED | Per #4020 comment | Named only. Not re-verified in this session. |
| #4068 | Exporter files | MERGED | Per #4020 comment | Named only. Not re-verified in this session. |

Child #4020 is closed. Child #4022 is open. Issue #4022 owns durable resume. It is not part of this change.

## 3. Existing Record

- The folder search under `specs/` found no folder that starts with `4021-`. The route folder `specs/numbered/0/0/1/1/2/0/4/1/` is absent in the local checkout.
- The draft folder `spec-drafts/4021` was empty before this run.
- No legacy record exists. The reuse steps of section 3, steps 3 and 4, do not apply. The remote checks in section 4 verify the claims of this record directly.
- The sibling record for issue #4020 exists at `specs/numbered/0/0/1/1/2/0/4/0/4020-ordered-single-site-firmware-phases/`. It is context only (row 70).

The route check: 4021 equals `112041` in base 5. The eight-level route `0/0/1/1/2/0/4/1` encodes that value. The reference record route `0/0/1/2/4/1/4/0` encodes 4920 by the same rule (row 69).

## 4. Remote Verification Table

Method:

1. One call fetched the full tree of `main`. The call returned the blob SHA of the first group of cited paths.
2. The `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main` response returns the body and the blob SHA. One script per code file decoded the base64 body, found each cited symbol, and printed its line number. Rows 1-34, 51-63, and 81-84 use this source. Rows 35-50 use the SHA field of the same response.
3. The OpenAPI file exceeds the contents API limit. Its local blob matches the remote blob SHA `b7fc2bfb`, which proves that the local body equals the remote body. Rows 64 to 67 use this source.
4. The SDK rows use the installed package in `.venv\Lib\site-packages\mistapi`. The brief requires the local path for third-party code. The blob SHA is not applicable to the installed package.
5. The local blob SHA of each worktree file equals the `HEAD` blob. `HEAD` equals remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

The row count is 87. The `remote_checks` array in STATUS has 87 objects. The summary repeats the count.

| # | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| 1 | Submit loop continues after one child refusal | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 231 |
| 2 | Build places the AP child first | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 577 |
| 3 | Build appends non-AP children after the AP child | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 578 |
| 4 | An unknown child outcome returns to the submit loop | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 845 |
| 5 | A lock failure stops later destructive writes | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 826 |
| 6 | The claim lease is five minutes | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 41 |
| 7 | No settle gate exists between families | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | absent | 0 |
| 8 | Site locks start empty in the parent record | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 211 |
| 9 | PLAN_FAMILY_ORDER is gateway, switch, AP | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 103 |
| 10 | plan_upgrade orders groups by family rank | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 1247 |
| 11 | Module comment names mistapi 0.63.3 | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | stale | 193 |
| 12 | Site device endpoint name is upgradeSiteDevices | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 47 |
| 13 | Single-site map joins device type to phase | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 115 |
| 14 | Single-site submitter documents a stop at the first refused group | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 962 |
| 15 | Single-site cascade walks PHASE_ORDER after submission | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1736 |
| 16 | Multi-site watch builds a PhaseSettleGate for each phase | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 130 |
| 17 | Multi-site watch walks PHASE_ORDER | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 166 |
| 18 | Multi-site watch calls the gate settle | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 314 |
| 19 | Registry starts one watch thread for each operation | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 342 |
| 20 | The phase limit is 1800 seconds | src/interfaces/portals/upgrade_portal/upgrade/phase_gate.py | 5eadca42f3f6f8d6828ab8c1dc3baa1a45faf1ab | present | 62 |
| 21 | PhaseSettleGate.settle waits for one phase | src/interfaces/portals/upgrade_portal/upgrade/phase_gate.py | 5eadca42f3f6f8d6828ab8c1dc3baa1a45faf1ab | present | 666 |
| 22 | The poll interval is 20 seconds | src/interfaces/portals/upgrade_portal/upgrade/gate.py | 1b366aa6a38087618b0e432be852c9c837fb974d | present | 97 |
| 23 | PHASE_ORDER names gateways, switches, aps, clients | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 58 |
| 24 | The route calls the aggregate send synchronously | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1869 |
| 25 | The route releases operation locks after the send | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1872 |
| 26 | The route starts the phase watch after the send | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1873 |
| 27 | The send function calls aggregate submit in the request | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1912 |
| 28 | The child claim refreshes each site lock | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1739 |
| 29 | The watch lease renews the site locks | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1981 |
| 30 | The partial-submission test asserts continuation after a refusal | tests/unit/firmware/test_aggregate_upgrade_service.py | 323ca22161c07b54c0a39b4e4a5a662745ddceb5 | present | 256 |
| 31 | The assertion expects three non-AP device submissions | tests/unit/firmware/test_aggregate_upgrade_service.py | 323ca22161c07b54c0a39b4e4a5a662745ddceb5 | present | 267 |
| 32 | The lock-loss test assumes the AP child writes first | tests/unit/firmware/test_aggregate_upgrade_service.py | 323ca22161c07b54c0a39b4e4a5a662745ddceb5 | present | 989 |
| 33 | A persisted partial-status integration test exists | tests/integration/test_aggregate_upgrade_flow.py | fd3968a5465fcb67b748bad3a59e1aa75335440f | present | 102 |
| 34 | The single-site test asserts no switch firmware after a refused gateway | tests/unit/upgrade_portal/test_wiring_submitter.py | fc6f500f54f0cb98bf77fff0229d4173403d6110 | present | 492 |
| 35 | Affected route contract file | tests/contract/upgrade_portal/test_org_upgrade_routes.py | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 0 |
| 36 | Affected watch contract file | tests/contract/upgrade_portal/test_org_phase_watch_contract.py | 4906854c4db4dc3785e2aea8742000e81606be4c | present | 0 |
| 37 | Affected walk unit file | tests/unit/upgrade_portal/test_org_cascade_walk.py | a352992e1b27208073ed26c17a36b39575cdac0e | present | 0 |
| 38 | Affected cancel outcome route file | tests/contract/upgrade_portal/test_org_cancel_outcomes_routes.py | 7052b850144150d5116458e58728efb82c4e4ed0 | present | 0 |
| 39 | Affected child controls route file | tests/contract/upgrade_portal/test_org_child_controls_routes.py | 7dc131799d4cb5af8955d1d6acfd1d0f76afb884 | present | 0 |
| 40 | Affected final cancel route file | tests/contract/upgrade_portal/test_org_final_cancel_routes.py | 7a251c69cc46eb03c6d113cd2a52016e675dc222 | present | 0 |
| 41 | Affected advanced options file | tests/contract/upgrade_portal/test_org_advanced_options.py | c6015b6c849d9aca280b9bdcada039e9825d8814 | present | 0 |
| 42 | Affected site records file | tests/contract/upgrade_portal/test_org_site_records_routes.py | 8fa9d329142764464212c55ccf08a596d503d799 | present | 0 |
| 43 | Affected precheck file | tests/contract/upgrade_portal/test_org_precheck_routes.py | 6c42105c2e2f4faabcd3f5f2d4db31c4d8cff7c9 | present | 0 |
| 44 | Affected seam support file | tests/support/org_cascade_seams.py | 48f7c66ba3a52a7b0dc684d4eedb97ee2b61f34f | present | 0 |
| 45 | Affected e2e fixture file | tests/e2e/upgrade_portal/conftest.py | d14fda9f0a4cf69dc3c1ec60efa5adb863b73840 | present | 0 |
| 46 | Affected prod child controls file | tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_child_controls.py | 347b788c657dad4bf3f0808a2728a98391165bb8 | present | 0 |
| 47 | Affected prod final cancel file | tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_final_cancel.py | 10cbe7b9c62578b745b5a6234890c7408bcd27d5 | present | 0 |
| 48 | Affected prod ended child cancel file | tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_ended_child_cancel.py | 8b4f877621df18e60f11d977c4e352c0871e663e | present | 0 |
| 49 | Affected prod mixed cancel file | tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_mixed_cancel_state.py | 31468107c76b0bb42399f6cc85d31e8fe0bf1051 | present | 0 |
| 50 | Affected prod advanced bodies file | tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py | cda412a8a3e55c337b7bf0edaa0375b69e316708 | present | 0 |
| 51 | Writing style section | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 52 | Specifications section | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| 53 | Local gates table | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 54 | Menu 239 starts an upgrade capture portal that drives a firmware upgrade | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 316 |
| 55 | Five-item rule | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 56 | Safety-first rule | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| 57 | Inline comments rule | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| 58 | Action logging rule | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| 59 | Technology constraints section | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| 60 | Operational store rule | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| 61 | MYPY_PATHS value | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 62 | VULTURE_PATHS value | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 63 | Writing gate section | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| 64 | upgradeOrgDevices POST operation | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9260 |
| 65 | upgradeOrgSsrs operation | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20982 |
| 66 | upgradeSiteDevices operation | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 28859 |
| 67 | upgradeDevice operation | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 31351 |
| 68 | mistapi pin is 0.64.1 | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| 69 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| 70 | Issue 4020 record spec contains FR-4020-01 | specs/numbered/0/0/1/1/2/0/4/0/4020-ordered-single-site-firmware-phases/spec.md | 96e0095cd2e60645ec454e3681086caab85aacd2 | present | 44 |
| 71 | Spec template Mist transport section | .specify/templates/spec-template.md | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 102 |
| 72 | Plan template Constitution Check section | .specify/templates/plan-template.md | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 44 |
| 73 | Tasks template format line | .specify/templates/tasks-template.md | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 20 |
| 74 | Checklist template title | .specify/templates/checklist-template.md | 806657da09d1058823923e346a323b633114971a | present | 1 |
| 75 | upgradeSiteDevices definition in the installed package | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | not applicable: installed package | present | 1230 |
| 76 | upgradeDevice definition in the installed package | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | not applicable: installed package | present | 3433 |
| 77 | upgradeOrgDevices definition in the installed package | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | not applicable: installed package | present | 840 |
| 78 | getOrgDeviceUpgrade definition in the installed package | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | not applicable: installed package | present | 871 |
| 79 | upgradeOrgSsrs definition in the installed package | .venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py | not applicable: installed package | present | 114 |
| 80 | mistapi version 0.64.1 in the installed package metadata | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | not applicable: installed package | present | 3 |
| 81 | The compare-and-set helper bounds retries and raises on failure | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 1503 |
| 82 | The status read recovers stale claims before a read | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 1418 |
| 83 | PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 84 | INTERROGATE_PATHS value | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 85 | The phase watch observes and sends no firmware request | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 10 |
| 86 | Operator text for unknown child outcomes in the route | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1930 |
| 87 | The lock release waits for a settled operation | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1803 |

Row 7 records absence. The search used the exact patterns `PhaseSettleGate`, `PhaseGate`, and `settle(`. The search found no match in the module.

Row 11 is stale. The comment names mistapi 0.63.3. The pin is 0.64.1 (row 68).

## 5. Decisions

Each decision has one object in STATUS. None requires a human decision under section 6 of the brief.

### D-1 Family order and SSR mapping

- **Decision**: Use the families gateway, switch, AP. Reuse `upgrade_service.PLAN_FAMILY_ORDER` (row 9). Map each SSR child (device family `ssr`) to the gateway family. Exclude clients.
- **Reason**: The plan order constant already exists and passed review in #4109. The owner decision on #4020 names the same order.
- **Alternatives**: (a) Reuse `PHASE_ORDER` from `runs.py` (row 23). Rejected, because the aggregate module would import the portal runtime. (b) Add a new constant. Rejected, because it duplicates the order.
- **Risk**: The phase names and the family names differ. A contract test maps `gateways` to `gateway`, `switches` to `switch`, and `aps` to `ap`.

### D-2 Portal-neutral gate seam

- **Decision**: The aggregate module defines `FamilySettleGate` and `FamilyGateResult`. The phase watch module defines `OrgFamilyGate`. It wraps `OrgPhaseGates` (row 16) and the existing `PhaseSettleGate` (row 21).
- **Reason**: The issue requires a portal-neutral collaborator (comment on issue #4021, 2026-10-07). The phase limit and the settle rule already exist.
- **Alternatives**: (a) Import `PhaseSettleGate` into the aggregate module. Rejected, because it creates a dependency on the portal. (b) Write a second settle rule. Rejected, because owner decision 1 requires the existing rule.
- **Risk**: The adapter must map every `PhaseOutcome` state. Unknown states map to `unknown` (test 7).

### D-3 Stop scope

- **Decision**: A refusal, an unknown outcome, a failed gate, a lock loss, or a cancellation stops the family and every later family.
- **Reason**: Owner decision 3 on #4020 stops the cascade. The single-site submitter stops at the first refused group (row 14).
- **Alternatives**: (a) Stop only the refused child. Rejected, because a later child of the same family can still write. (b) Continue after refusal with a warning. Rejected, because it repeats the defect in rows 1 and 4.
- **Risk**: A run stops more often. Each stop writes a stop record, so the operator reads one reason.

### D-4 Background run

- **Decision**: The route runs the synchronous check. Then it starts one background run for each operation. The background run sends the families. The route returns the job page.
- **Reason**: A family gate can last 1800 seconds (row 20). A request cannot hold that wait.
- **Alternatives**: (a) Keep the request open. Rejected, because the request times out. (b) Let the phase watch send the later families. Rejected, because the issue requires that the watch observes only. (c) Use an external worker. Rejected, because it adds infrastructure.
- **Risk**: A background error does not reach the HTTP response. The stop record carries the error to the operator.

### D-5 Claim lifecycle

- **Decision**: The parent claim covers one family send. No parent claim covers a gate wait. Each child claim covers one cloud call (row 1).
- **Reason**: The claim lease is five minutes (row 6). A gate wait can last 1800 seconds.
- **Alternatives**: (a) Hold one parent claim for the whole run. Rejected, because the lease expires during a wait. (b) Hold no parent claim. Rejected, because two runs could send one family.
- **Risk**: A second run might claim the next family. The compare-and-set helper (row 81) rejects a stale version.

### D-6 Watch handoff

- **Decision**: The phase watch reads the stored family gate result. It makes no gate call for a family that has a result. After a stop record, it marks later families as not submitted.
- **Reason**: Two gate waits double the cloud reads. Two results confuse the operator.
- **Alternatives**: (a) Keep the watch unchanged. Rejected, because both waits poll the cloud. (b) Remove the watch. Rejected, because the watch serves the status page.
- **Risk**: The watch waits for a result that never arrives. A process-lost stop (D-8) ends that wait.

### D-7 Lock lifecycle

- **Decision**: Keep the release rule (row 87). Renew the site locks during each gate wait with the lease that the route creates (row 29). Release only after a final state.
- **Reason**: The release rule protects sites that still receive writes (row 25).
- **Alternatives**: (a) Release after each family. Rejected, because a site could receive a write from another run. (b) Release at a stop. Rejected, because the stopped run still holds unknown writes.
- **Risk**: A stopped run keeps its locks. The operator reads the run before any action. The Caution in the spec states this.

### D-8 Process loss

- **Decision**: The background run refreshes a wait marker at each poll. A stale marker, older than the claim lease, causes a `process_lost` stop on the next status read (row 82). No child is resent.
- **Reason**: A restart must not repeat a destructive write. Issue #4022 owns resume.
- **Alternatives**: (a) Resume the family after a restart. Rejected, because owner decision 3 forbids an automatic retry. (b) Mark the run failed without a stop record. Rejected, because the operator needs the family and the children.
- **Risk**: A long gate wait without refresh looks like a lost process. The refresh runs every 20 seconds (row 22).

### D-9 Manifest expansion

- **Decision**: Add `org_upgrade.py` and `walk.py` to the manifest. Add the test files in rows 35 to 50 as verification files.
- **Reason**: The route must return before the wait (row 24). The phase watch must read the stored result (row 16).
- **Alternatives**: (a) Keep the two-file manifest. Rejected, because the route and the watch cannot meet FR-015 and FR-016. (b) Move the change to a new module. Rejected, because of D-10.
- **Risk**: The owner must approve the expanded manifest. The pull request states the reason.

### D-10 No new module

- **Decision**: Edit existing modules only. Add the changelog fragment and the record files only.
- **Reason**: The five-item rule forbids a new direct child in a noncompliant folder (row 55). Folder counts appear in section 10.
- **Alternatives**: (a) Add a nested package. Rejected, because it adds a second route to the same code. (b) Add a module to `firmware/`. Rejected, because the rule forbids it.
- **Risk**: Existing modules grow. The Complexity Tracking table names the remediation R-1.

### D-11 Mist calls

- **Decision**: Reuse the existing calls. The access point call uses `OrgUpgradeService.submit` (row 27). The site and SSR calls use `upgrade_service.invoke_upgrade` (rows 75 to 80, 64 to 67).
- **Reason**: The constitution requires mistapi methods for Mist requests (row 59). The calls already passed review.
- **Alternatives**: (a) Send direct HTTP requests. Prohibited by row 59. (b) Add a new endpoint. Rejected, because the change needs no new endpoint.
- **Risk**: The SSR organization call and the site call accept different scope fields. The OpenAPI body schema is unverified (U-4).

### D-12 Operator stop text

- **Decision**: Each stop reason has one sentence. The sentence names the family and the next action. It contains no host, token, or cloud body.
- **Reason**: The issue body of #4022 requires one next action in each stop message. Its operator text rule states this.
- **Alternatives**: (a) Keep the single unknown-outcome text. Rejected, because it names no family. (b) Show the raw cloud reply. Rejected, because the reply can contain secret data.
- **Risk**: A test asserts the old text. Task T021 searches for it.

### D-13 Test strategy

- **Decision**: Rewrite two defect tests (rows 30 to 32). Add 15 tests. Use doubles only.
- **Reason**: The change alters behavior, so each changed rule needs a test. Mocked tests prove the rules without a cloud request.
- **Alternatives**: (a) Run a live test. Prohibited by the brief. (b) Add only smoke tests. Rejected, because they do not prove the stop rules.
- **Risk**: The mocks differ from the live cloud. Unverified item U-3 records that gap.

### D-14 Stale SDK comment

- **Decision**: Do not change the comment in this change. Open a separate issue (R-4).
- **Reason**: The issue scope excludes it. A separate issue keeps one concern for each change.
- **Alternatives**: (a) Fix it here. Rejected, because the change then covers two concerns. (b) Leave it unreported. Rejected, because the drift is a defect (row 11).
- **Risk**: The comment stays stale until R-4 closes.

### D-15 Phase limit

- **Decision**: Use the phase limit of 1800 seconds (row 20). Add no timeout.
- **Reason**: Owner decision 1 on #4020 requires the existing limit.
- **Alternatives**: (a) A shorter family limit. Rejected, because the owner decision forbids an independent timeout. (b) An unlimited wait. Rejected, because it blocks the run forever.
- **Risk**: A slow family stops the run. The operator reads the family and the reason.

## 6. Sources

- Local repository files: each path appears in section 4 with its blob SHA. No local file was used without a matching remote row.
- Local SDK files: `.venv\Lib\site-packages\mistapi`, package version 0.64.1 (rows 75 to 80).
- Local OpenAPI file: `documentation/mist-api-openapi31yaml.yaml` (rows 64 to 67).
- GitHub issue and pull request data: `gh issue view` for #4021, #4020, #4022, and #3332. `gh pr view` for #4109 and #4701. `gh pr list` for open pull requests.
- URLs: none. The research did not call `web_fetch`, because the local sources answered every question.

## 7. Unverified

- **U-1**: The issue says that ten existing tests lock the defect. This review verified two in the aggregate suite (rows 30 to 32). The other eight tests are not enumerated. Task T021 runs the affected files.
- **U-2**: The 13 affected test files (rows 35 to 50) were not run. The brief forbids running tests during this research.
- **U-3**: Live Mist behavior, cloud job duration, and cross-site acceptance of the access point call cannot be verified offline.
- **U-4**: The OpenAPI body schema of the SSR organization call was not compared with the site call. The scope fields may differ.
- **U-5**: The flags of `speckit-task-audit` and `symbol-diff` come from the local gates table (row 53). The flags were not checked.
- **U-6**: The existence of `.ste-linter.toml` and the options of `ste-linter` come from the local gates table. They were not checked.
- **U-7**: The guard file `tests/guardrails/local_test_quality_loop/test_guidance.py` and the `pytest-chunks` commands come from the repository instructions. They were not executed.
- **U-8**: The folder child counts in section 10 come from the local checkout. The remote tree was not counted.
- **U-9**: Existing tests may assert the operator text of row 86. Task T021 searches for the text.

## 8. Overlap Check

- Open pull requests scanned: 7.
- Overlap with the nine manifest paths: none.
- The issue requires a recheck before implementation. The recheck happens in T-PR as well.

## 9. Skills

No local skill was loaded. The change touches no Podman, Juniper device, or Mist SDK behavior beyond the repository evidence in section 4.

## 10. Local Measurements

Each count below comes from a direct child listing of the local checkout at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

- `src/operations/execution/firmware/`: 13 children.
- `src/operations/execution/`: 7 children.
- `src/interfaces/portals/upgrade_portal/app/routes/`: 14 children.
- `src/interfaces/portals/upgrade_portal/upgrade/`: 23 children.
- `specs/numbered/0/0/1/1/2/0/4/`: 2 children today, named `0` and `4`. The new folder `1` makes 3 children.
