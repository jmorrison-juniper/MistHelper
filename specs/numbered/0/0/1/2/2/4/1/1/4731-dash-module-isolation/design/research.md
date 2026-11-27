# Research: Dash module isolation for map callback tests

## Method

- Remote truth comes from `gh api` on `jmorrison-juniper/MistHelper`, branch `main`, head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Local HEAD matches remote main. Each hash-checked repository file has a local HEAD blob and a working blob that match the remote blob SHA. Local line numbers therefore apply to remote main. The reference record files, the PR template, and the preflight test were read only through local views and the remote tree. Unverified item U-9 records that gap.
- Legacy record: none. A search of `specs\` found no folder whose name starts with `4731-`. Both the glob search and the PowerShell search returned zero matches.
- URLs fetched: none. No local source needed a web lookup.
- Skills: none loaded. The issue has no Podman question and no Juniper device question. The debug-live skill does not apply, because the brief forbids running tests.
- Scope of reading: `documentation/container-deployment.md` and `documentation/operator-guide.md` do not apply, because the change adds no container and no operator-visible behavior. `documentation/architecture.md` and `documentation/development-setup.md` were searched for test commands and the maps layout, and this record cites no line from them. The Mist API OpenAPI file and the pinned mistapi package do not apply, because the change does not call any Mist API function.
- Issue and pull request states come from `gh` reads. They are not code claims, so they do not appear in the remote table.

## Issue facts

- Issue 4731 is open. Its labels are `bug`, `tests`, and `in-progress`. It opened on 2026-11-10 and last changed on 2026-11-11.
- The issue body names five files in `tests/maps`. Each file installs a Dash stub during collection, and the fixture saves the stub. The body says it relates to issues 2708 and 4728.
- The issue reports these reproduction results:
  - `Selected callback test: passed`
  - `Real Dash module restored: False`
  - `Subsequent 'from dash import Dash' succeeds: False`
  - `Offline barrier: 7 self-checks passed`
  - `Unexpected live-operation attempts: 0`
- Owner comments reserve one file for each slice. The comment IDs are IC_kwDOQltU8c8AAAABkssyBA (wave A), IC_kwDOQltU8c8AAAABkv34fg (wave B/C), IC_kwDOQltU8c8AAAABkv6ueg (wave E2), and IC_kwDOQltU8c8AAAABkv-ntA (waves D and E1).
- The owner names the wave A and wave E2 assertion candidates from issue 2708 (IC_kwDOQltU8c8AAAABktznpQ for wave E2).
- The owner keeps serial publication holds. The latest comments are IC_kwDOQltU8c8AAAABlH786A and IC_kwDOQltU8c8AAAABlH8J4Q, dated 2026-11-11. They state that held commit `6c50414463ca24e33220046a54b83b5dee6b6d4d` stays unchanged.
- Linked pull request 4735 merged wave E1 on 2026-11-10 (merge commit `ef1434de6b6dcdf90ba5cea66483a37565036b80`). Its body says it closes issue 4733 and relates to issue 4731.
- Related issues: 2708 is open (weak assertion triage). 4728 is open (root logger at DEBUG). 4733 is closed (map clone test). Pull request 4666 is closed (a CI version bump). The owner names 4666 in one comment.

## Remote verification table

Each row is one remote or local check. The table has 67 rows. The `remote_checks` array in `4731-STATUS.json` has the same 67 rows, in the same order.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | Remote main head is commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | refs/heads/main | main | n/a | present | 0 |
| R02 | Wave A holds a module-level dash stub install at line 44 | tests/maps/test_viewer_callbacks_wave_a.py | main | 2f1d3052d95b10edebc6113f9c7e9b49a306a2ab | present | 44 |
| R03 | Wave A fixture snapshots the stub at line 52 | tests/maps/test_viewer_callbacks_wave_a.py | main | 2f1d3052d95b10edebc6113f9c7e9b49a306a2ab | present | 52 |
| R04 | Wave A line 134 uses a non-None check | tests/maps/test_viewer_callbacks_wave_a.py | main | 2f1d3052d95b10edebc6113f9c7e9b49a306a2ab | present | 134 |
| R05 | Wave A line 181 uses a non-None check | tests/maps/test_viewer_callbacks_wave_a.py | main | 2f1d3052d95b10edebc6113f9c7e9b49a306a2ab | present | 181 |
| R06 | Wave B/C holds a module-level dash stub install at line 48 | tests/maps/test_viewer_callbacks_wave_b_c.py | main | 61b0c32fe55e7b129c4e32ddf327d04e25924d05 | present | 48 |
| R07 | Wave B/C fixture snapshots the stub at line 59 | tests/maps/test_viewer_callbacks_wave_b_c.py | main | 61b0c32fe55e7b129c4e32ddf327d04e25924d05 | present | 59 |
| R08 | Wave D holds a module-level dash stub install at line 46 | tests/maps/test_viewer_callbacks_wave_d.py | main | 1639e8ed9d203ded50b91ee39d30ce022d4bdcfe | present | 46 |
| R09 | Wave D fixture snapshots the stub at line 54 | tests/maps/test_viewer_callbacks_wave_d.py | main | 1639e8ed9d203ded50b91ee39d30ce022d4bdcfe | present | 54 |
| R10 | Wave E2 holds a module-level dash stub install at line 45 | tests/maps/test_viewer_callbacks_wave_e2.py | main | 7f666fae76e434af46570c962c04187f10b3b610 | present | 45 |
| R11 | Wave E2 fixture snapshots the stub at line 53 | tests/maps/test_viewer_callbacks_wave_e2.py | main | 7f666fae76e434af46570c962c04187f10b3b610 | present | 53 |
| R12 | Wave E2 line 174 uses a non-None serializer check | tests/maps/test_viewer_callbacks_wave_e2.py | main | 7f666fae76e434af46570c962c04187f10b3b610 | present | 174 |
| R13 | Wave E2 line 178 uses a non-None figure builder check | tests/maps/test_viewer_callbacks_wave_e2.py | main | 7f666fae76e434af46570c962c04187f10b3b610 | present | 178 |
| R14 | Wave E1 helper records dash_was_present at line 50 | tests/maps/test_viewer_callbacks_wave_e1.py | main | 88f93f1d30c2690f69b57f5781bc0610e94c9c98 | present | 50 |
| R15 | Wave E1 module-level with-block at line 62 restores around the import | tests/maps/test_viewer_callbacks_wave_e1.py | main | 88f93f1d30c2690f69b57f5781bc0610e94c9c98 | present | 62 |
| R16 | Pull request 4735 merge commit ef1434de is the latest main commit for wave E1 | tests/maps/test_viewer_callbacks_wave_e1.py | ef1434de6b6dcdf90ba5cea66483a37565036b80 | 88f93f1d30c2690f69b57f5781bc0610e94c9c98 | present | 0 |
| R17 | Baseline holds wave A weak_is_not_none entries at line 940 | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 940 |
| R18 | Baseline holds wave E2 weak_is_not_none entries at line 962 | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 962 |
| R19 | Candidate commit 6c50414 exists on GitHub, diverges from main, and holds the wave B/C candidate blob | tests/maps/test_viewer_callbacks_wave_b_c.py | 6c50414463ca24e33220046a54b83b5dee6b6d4d | b557559d1cd0e28237e6d1ac47aa20437ac32043 | present | 0 |
| R20 | Candidate commit f88ad2ea exists on GitHub, diverges from main, and holds the wave D candidate blob | tests/maps/test_viewer_callbacks_wave_d.py | f88ad2ea5e4fe61cbe3aed9f5a483dc77bb31a25 | 83a192075e4b39373af0bf501099ef68e2ad611f | present | 0 |
| R21 | Candidate commit 2238c75f exists on GitHub, diverges from main, and holds the wave E2 candidate blob | tests/maps/test_viewer_callbacks_wave_e2.py | 2238c75f9c1a84ce67c9190ba180a12c724190d8 | 8385ed828332c7338271d35bf10573eae720785b | present | 0 |
| R22 | Local candidate commit b9d88a4d for wave E1 is absent on GitHub | tests/maps/test_viewer_callbacks_wave_e1.py | b9d88a4d915e23a0165b30dd0aa34035af08f12f | n/a | absent | 0 |
| R23 | Launcher viewer_callbacks imports dash inside a method at line 378 | src/interfaces/visualization/maps/launcher/viewer_callbacks.py | main | 87f2cd60c76ec9bb0af52462b02ce6bd2bd95cdf | present | 378 |
| R24 | Launcher display click handler imports dash html inside a method at line 287 | src/interfaces/visualization/maps/launcher/_viewer_ui.py | main | 06c40965150251307fa15a2f62019f8422fa8825 | present | 287 |
| R25 | Maps manager probes dash with find_spec at line 99 | src/interfaces/visualization/maps/maps_manager.py | main | b3d4f9251221fbdf7bbddbb2ca833fc29b607b8c | present | 99 |
| R26 | Maps package init file has no import of dash | src/interfaces/visualization/maps/__init__.py | main | 9e3df534eebb5b7f2bee09b2a18c592e5ee18078 | present | 0 |
| R27 | Installed dash package exports Dash, html, and callback_context | .venv\Lib\site-packages\dash\__init__.py | local working tree | n/a | present | 38 |
| R28 | Test-quality baseline key includes line_number | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py | local working tree | n/a | present | 6 |
| R29 | symbol-diff reports lost and added module-level names as changes | .venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py | local working tree | n/a | present | 120 |
| R30 | CI root-and-contracts shard runs tests/maps | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| R31 | CI path variables name src and root modules, not tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R32 | Container build path filter does not name tests | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| R33 | Local gates table lists lint, format, test, symbol, and quality commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R34 | Test quality ratchet procedure and preflight command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| R35 | Preflight guard test file exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| R36 | AGENTS tests section requires failing tests and repair of shared-state tests | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| R37 | AGENTS pull request rule requires Closes in the body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R38 | AGENTS requires the auto-merge label only after each check shows green | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| R39 | Constitution Principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R40 | Constitution requires the eight-level base-5 route for numeric records | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 59 |
| R41 | Constitution Principle IV deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R42 | Constitution Principle VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R43 | Constitution Principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R44 | Constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R45 | Governance section says the constitution supersedes other practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 526 |
| R46 | Quality gates document says write-baseline removes entries that match no finding | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 36 |
| R47 | Spec route script writes numeric records under specs/numbered | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 51 |
| R48 | Feature name helper lowercases and hyphenates names | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 73 |
| R49 | Copilot instructions limit changelog fragments to user-visible changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R50 | Copilot instructions list labels by type, scope, and status | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 431 |
| R51 | pyproject Ruff rules select E, F, W, I, UP, B, G, PLW1514, and RUF100 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 209 |
| R52 | pyproject E402 ignores name only listed files, not tests/maps | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 260 |
| R53 | Spec template heading layout | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| R54 | Plan template heading layout and Complexity Tracking table | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| R55 | Tasks template heading layout | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| R56 | Checklist template heading layout | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R57 | Reference record spec.md has a Requirements section | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 161 |
| R58 | Reference record plan.md has a Constitution Check section | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 37 |
| R59 | Pull request template file exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 1 |
| R60 | Constitution Principle II class-based architecture and no wrapper functions | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R61 | Constitution Principle III safety-first rules for inputs and secrets | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R62 | Constitution Principle V ASCII-only logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R63 | Constitution technology constraints: Python version, mistapi only for Mist REST calls, and path rules | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| R64 | Constitution Testing section requires a py_compile check before each commit | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 361 |
| R65 | Constitution security findings rule forbids suppression as a shortcut | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 373 |
| R66 | Constitution complexity-driven escalation requires a specification for changes that touch three or more files | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| R67 | Constitution branch naming uses fix, feat, and chore prefixes with the issue number | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 476 |

Notes on the table:

- Rows R02 to R11 confirm the defect in each slice file. They also confirm that each file exists on main.
- Rows R14 to R16 confirm that wave E1 merged and that its file matches the reviewed candidate.
- Rows R19 to R22 confirm that the held candidate commits exist on GitHub. Row R22 confirms that the local E1 commit does not.
- Rows R23 to R26 confirm the import chain. Row R27 confirms the installed dash exports.
- Rows R28 and R29 confirm the two local gate rules that drive the design.
- Row R35 confirms that the preflight test file exists on main. The preflight run itself is not executed (U-8).

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human answer, because each one falls outside the categories in section 6 of the brief.

### D-1 Fixture-only restore with no import-time install

- Alternatives: (a) Copy the wave E1 helper into each slice. (b) Keep the import-time install inside a module-level try and finally block. (c) Move the stub to a shared conftest or helper module.
- Chosen: Remove the import-time install. The autouse fixture records the prior entry and restores it exactly.
- Reason: Options (a) and (b) add module-level names, which the symbol gate counts (R29). Option (c) adds a shared file that the owner did not approve for this issue, and it forces serial merges across slices. The launcher chain does not import dash at module load (R23, R24, R25, R26), so the import-time install is not needed.
- Risk: Runtime proof is pending (U-1). QS-15 must confirm the result before publication.

### D-2 Do not reuse the held candidate commits

- Alternatives: (a) Reuse commits 6c50414, f88ad2ea, and 2238c75 as they are. (b) Rebase the candidates after the owner releases the hold.
- Chosen: Build new slice branches from main, using D-1. Leave the held commits unchanged (FR-027).
- Reason: The candidates add module-level names. They add an import of `contextmanager` and module-level helpers or sentinels, for example `_DASH_MODULE_MISSING`, `_MISSING_DASH_MODULE`, and `_restore_dash_module` (R19, R20, R21). Those names fail the symbol gate (R29). The candidates also repeat regression cases across four files, which breaks the rule to write each case once.
- Risk: The owner may prefer the candidates. The owner can still choose them after this record, and the owner decides the disposition of the held commits.

### D-3 No permanent guard and no regression case in this issue

- Alternatives: (a) Add a subprocess guard in a new file under `tests/guardrails`. (b) Add one regression case to each slice file. (c) Defer a guard to a follow-up issue.
- Chosen: Option (c). The probes in quickstart QS-02 to QS-07 serve as the regression evidence for this issue.
- Reason: A new file under `tests/guardrails` adds a direct child to an existing folder. Principle I (R39) limits direct children, so the owner must approve that child. The owner named five files for this issue, and a regression case in each slice file duplicates the case across four files.
- Risk: The defect class can return in a future file. Recommend a follow-up issue for a collection guard after slice S4 merges. Until then, CI runs the `tests/maps` files together in one shard (R30).

### D-4 Fix both weak checks in wave A

- Alternatives: (a) Fix only line 181, which the owner named. (b) Fix line 181 and keep the line count above line 134 unchanged.
- Chosen: Fix line 134 and line 181 (FR-007 and FR-008).
- Reason: The baseline key includes the line number (R28). The fixture edit moves line 134. A moved finding counts as new, and the gate fails. The owner forbids a baseline change. Option (b) depends on exact line counts and breaks easily.
- Risk: The owner did not name line 134. The owner can reject this scope. If the owner rejects it, the slice must keep the line count above line 134 unchanged.

### D-5 Fix both weak checks in wave E2

- Alternatives: (a) Fix only the serializer check at line 174. (b) Fix both checks at lines 174 and 178.
- Chosen: Fix both checks (FR-010).
- Reason: The owner names the wave E2 assertion gap from issue 2708. Both lines carry baseline entries (R18). Fixing both removes all findings in that file.
- Risk: The stale baseline entries remain until a later prune. The gate treats them as advisory (R46).

### D-6 Publish four slice pull requests in serial order

- Alternatives: (a) One pull request for all four files. (b) Four pull requests in parallel. (c) Four pull requests in serial order.
- Chosen: Option (c), in this order: wave A, wave B/C, wave D, and wave E2 (FR-024, FR-025).
- Reason: The owner reserves one file per slice and holds serial publication. AGENTS says one pull request holds one change (R36 gives the testing rule and R37 gives the pull request rule).
- Risk: Serial publication takes longer. Each slice waits for the previous merge.

### D-7 Use Refs for three pull requests and Closes for the final pull request

- Alternatives: (a) Use Closes in every pull request, as the generic brief states. (b) Use Refs in every pull request and close the issue by hand. (c) Use Refs in the first three and Closes in the last.
- Chosen: Option (c) (FR-026).
- Reason: The owner says to keep issue 4731 open until all five callback slices merge. The body of pull request 4735 states this. Option (a) would close the issue after the first slice merges. AGENTS asks for Closes in the body (R37), so the final pull request keeps it.
- Risk: The deviation from the generic brief rule is visible in the record. The reviewer must confirm the final pull request body before merge.

### D-8 Add one changelog fragment for each pull request

- Alternatives: (a) Add no fragment, because the change is not user-visible (copilot rule, R49). (b) Add one fragment for each pull request (constitution rule, R44).
- Chosen: Option (b) (FR-022). The constitution governs, because the governance section says it supersedes other practice documents (R45).
- Reason: The constitution says each change adds one fragment. The copilot rule covers user-visible changes only, so the two rules conflict. The constitution wins.
- Risk: The fragment adds a file to `changelog.d`. The change then touches one more file. The owner may reject the fragment, and the record would then need a new decision.

### D-9 Logging uses a function-local import and runs only in fixtures

- Alternatives: (a) Add a module-level `logging` import. (b) Add a module-level logger. (c) Add a function-local import inside each changed fixture.
- Chosen: Option (c). Logs run only in the changed fixture. Test assertions get no logs.
- Reason: Options (a) and (b) add a module-level name (R29). The ruff selection does not include PLC0415, so a function-local import passes lint (R51). Principle VII targets actions, and a fixture that changes `sys.modules` is an action. An assertion is not an action.
- Risk: A reviewer may expect logs in test bodies. The plan states the scope reading in the constitution check.

### D-10 Principle IV steps 10 to 12 do not run

- Alternatives: (a) Dispatch the container build by hand after the final merge. (b) Record a documented exception.
- Chosen: Option (b). The owner decides on a manual dispatch later (U-1).
- Reason: The container build watches product paths only (R32). A test-only change creates no image. A dispatch would build the same image again.
- Risk: The constitution says no step may be skipped. The exception stays visible in analysis.md as an unresolved item.

### D-11 Branch names, commit subject, labels, and PR template

- Alternatives: (a) Use one branch for all slices. (b) Use one branch for each slice.
- Chosen: Option (b). Names are `fix/4731-wave-a-dash-restore`, `fix/4731-wave-b-c-dash-restore`, `fix/4731-wave-d-dash-restore`, and `fix/4731-wave-e2-dash-restore`. Commit subjects and PR titles start with `fix(maps):`. PR labels are `bug` and `tests`. The body follows the PR template (R59).
- Reason: Each slice is one change (R36, R37). The branch prefix comes from the constitution (R67). The `fix` type matches the bug label (R50). The Conventional Commits types in Principle IV step 4 accept the `fix` type (R41).
- Risk: The issue label list is already complete, so no issue label changes.

### D-12 Record slug and route

- Alternatives: (a) Use a different slug. (b) Use the issue number only.
- Chosen: The slug is `dash-module-isolation`. The record folder is `specs\numbered\0\0\1\2\2\4\1\1\4731-dash-module-isolation`.
- Reason: The slug follows the lowercase and hyphen rule (R48). The route equals the base-5 value of 4731, which is 122411 and pads to 00122411 (computed locally with PowerShell, rule R40). The numeric record folder follows the spec route script (R47).
- Risk: None known.

### D-13 The owner keeps the publication hold

- Alternatives: (a) Lift the hold in this record. (b) Keep the hold and record it as a precondition.
- Chosen: Option (b) (FR-023).
- Reason: The owner set the hold in the issue comments. This record does not change the owner's decision. The hold is a process precondition, not one of the human-decision categories in section 6 of the brief.
- Risk: Publication cannot start until the owner releases the hold.

### D-14 Wave E1 stays as merged

- Alternatives: (a) Change wave E1 to the fixture-only design. (b) Add logs to wave E1. (c) Leave wave E1 unchanged.
- Chosen: Option (c) (FR-029).
- Reason: Wave E1 merged through PR 4735 (R14 to R16). The owner reserved the file for another repair. One issue holds one concern.
- Risk: Wave E1 keeps a different design and lacks action logging. Analysis item F-05 records this as debt for a follow-up.

## Sources

Local sources (path and line, all matched to remote blobs in the table):

- `AGENTS.md` (rows R36, R37, R38)
- `.github/copilot-instructions.md` (rows R33, R34, R49, R50)
- `.github/workflows/ci.yml` (rows R30, R31)
- `.github/workflows/container-build.yml` (row R32)
- `.github/test-quality-baseline.json` (rows R17, R18)
- `.github/PULL_REQUEST_TEMPLATE.md` (row R59)
- `.github/workflows` and `pyproject.toml` (rows R51, R52)
- `.specify/memory/constitution.md` (rows R39 to R45 and R60 to R67)
- `.specify/templates/` (rows R53 to R56)
- `.specify/scripts/powershell/spec-route.ps1` (row R47)
- `.specify/scripts/powershell/create-new-feature.ps1` (row R48)
- `documentation/quality-gates.md` (row R46)
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (rows R57, R58)
- `src/interfaces/visualization/maps/` launcher files, `maps_manager.py`, and `maps/__init__.py` (rows R23 to R26)
- `tests/maps/test_viewer_callbacks_wave_a.py`, `_wave_b_c.py`, `_wave_d.py`, `_wave_e1.py`, and `_wave_e2.py` (rows R02 to R16)
- `tests/guardrails/local_test_quality_loop/test_guidance.py` (row R35)
- `.venv\Lib\site-packages\dash\__init__.py` (row R27)
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py` (row R28)
- `.venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py` (row R29)

Remote sources (GitHub, read through `gh`):

- Git objects for the candidate commits and their file blobs (rows R19 to R22).
- Pull request 4735 (merge commit `ef1434de6b6dcdf90ba5cea66483a37565036b80`).
- The issue 4731 comments named in the Issue facts section.

URLs: none.

## Unverified

- U-1: Importing the launcher package leaves the dash entry absent. The evidence is static only (rows R23 to R26). Quickstart QS-15 must run before the first publication. Either result keeps the design valid.
- U-2: Other `tests/maps` files behave the same under the real Dash package. The files are `test_phase1_integration.py`, `test_plotly_map_callback_manager.py`, and `test_plotly_map_templates.py`. Their dash references are names, a patch target, and a helper call. The patch target `src.interfaces.visualization.maps.maps_manager.Dash` in `test_phase1_integration.py` line 193 has an unverified dependency on the maps manager namespace. Quickstart QS-13 must run before publication.
- U-3: The test-quality analyzer reports zero new findings for the four edited files. The baseline key is confirmed (row R28), but the analyzer did not run.
- U-4: The symbol gate accepts the function-local import and the removed statement. The comparator is confirmed (row R29), but the gate did not run.
- U-5: The branch that holds each held candidate commit. Rows R19 to R21 confirm the commits exist on GitHub. A search of the owner-prefixed branches (15 branches) found no wave branch. The owner can name the branch.
- U-6: The current CI status of main. No CI run was read.
- U-7: Ruff and black accept the planned line lengths and styles. The gates did not run (quickstart QS-08 and QS-09).
- U-8: The preflight test passes on main. The test file exists (row R35), but it did not run (quickstart QS-11).
- U-9: Local hash checks did not run for rows R35, R57, R58, and R59. Their remote blob SHAs come from the remote tree. Their line numbers come from local reads of the same files.
