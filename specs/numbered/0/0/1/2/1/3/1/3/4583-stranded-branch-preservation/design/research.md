# Research: Stranded Branch Preservation

**Issue**: #4583, "chore(git): a branch holds work with no pull request".

**Snapshot**: GitHub state read on 2026-11-26. Local git reads used the `main` commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Summary**: The issue body lists 52 branches, but the emulated live report rule finds 543 branches. This record preserves each in-scope branch with a closed draft pull request. It holds branches that share a changed file with an open pull request.

## Decisions

### D-1 Preservation method

- **Options**: (a) Keep one draft pull request open for each branch. (b) Push a recovery tag for each branch. (c) Open a draft pull request and close it without merge in the same step.
- **Decision**: Option (c).
- **Reason**: The report protects a branch only through a pull request head, as R38 and R39 show. A tag does not clear the report. Open drafts would share changed files with each other.
- **Risk**: Each branch adds two writes. Pacing and backoff limit the rate. A reopen restores any closed pull request.

### D-2 Overlap hold

- **Options**: (a) Ignore the overlap. (b) Hold the branch until the blocking pull request closes or merges. (c) Close the blocking pull request.
- **Decision**: Option (b).
- **Reason**: AGENTS.md line 245 says one file cannot carry two open pull requests. Option (c) changes a pull request that this record does not own.
- **Risk**: 102 branches wait. 62 of them wait on draft pull request #4208.

### D-3 Scope source and rule

- **Options**: (a) The 52 names in the issue body. (b) The workflow output of 2026-11-23, which lists 505 rows. (c) A read-only emulation of the report rule on 2026-11-26, which finds 543 rows.
- **Decision**: Option (c). Command Q-2 reruns the emulation before each batch.
- **Reason**: The body is stale, and it still names three branches that moved. The report closes its issue only when no branch is stranded. The emulation covers all 505 names of the 2026-11-23 report.
- **Risk**: The emulation does not run the report command itself. The section "Report Comparison" in `data-model.md` lists the one difference.

### D-4 Renamed heads

- **Options**: (a) Rename each archive branch back to its body name. (b) Process each archive branch under its current name.
- **Decision**: Option (b).
- **Reason**: The archive name holds the same head SHA as the body name, as R49 to R54 show. A rename writes a new ref and gains no preservation.
- **Risk**: The issue body and the report use different names for three branches until the body refreshes.

### D-5 Quiet period and prefixes

- **Options**: (a) Preserve every branch now. (b) Follow the report rule of seven days and three prefixes.
- **Decision**: Option (b).
- **Reason**: The report defines the work list, as R36 and R37 show. Recent branches can still receive commits.
- **Risk**: 28 younger branches enter scope later. Command Q-5 finds them before the record merges.

### D-6 No deletion

- **Options**: (a) Delete each branch after its preservation pull request closes. (b) Keep every branch.
- **Decision**: Option (b).
- **Reason**: The report clears without any deletion. A deletion needs its own decision and its own issue.
- **Risk**: The branch list stays long after this record completes.

### D-7 Record pull request keyword and gate

- **Options**: (a) Use `Refs #4583`. (b) Use `Closes #4583` and merge at once. (c) Use `Closes #4583` and merge after the final scope check.
- **Decision**: Option (c).
- **Reason**: AGENTS.md requires `Closes #<issue>` in a pull request body. A merge before the scope check closes issue #4583 while branches stay stranded.
- **Risk**: The record pull request waits until every hold releases.

### D-8 Duplicate report issues

- **Options**: (a) Close the four duplicate report issues inside this issue. (b) File a separate defect issue.
- **Decision**: Option (b).
- **Reason**: AGENTS.md says one issue holds one subject. R41 and R42 show the search and the create call. Five open issues with the same title show that each weekly run created a new issue.
- **Risk**: Five report issues stay open until the defect issue completes.

### D-9 Serial pacing and backoff

- **Options**: (a) Run batches in parallel. (b) Run one step at a time, with a wait of five seconds between rows and bounded backoff.
- **Decision**: Option (b). Backoff on HTTP 403 or 429 follows FR-010.
- **Reason**: One open preservation pull request at a time is required by FR-004. Rate limits are a known constraint.
- **Risk**: The full run takes many hours. Batches let the operator pause between them.

### D-10 Read-only evidence

- **Options**: (a) Run a checkout of each branch to inspect it. (b) Read commits and paths with `git log` and `git diff` only.
- **Decision**: Option (b).
- **Reason**: The record rules forbid checkout of a stranded branch. AGENTS.md forbids checkout in a checkout that another session uses.
- **Risk**: The record does not review branch content. Content review is outside this issue.

### D-11 Human decisions

- **Options**: (a) Ask the owner about each branch. (b) Decide each item by the record rules and list no human decision.
- **Decision**: Option (b).
- **Reason**: The human decision categories are licensing or legal text, destruction of production data, credential policy, and product priority. None applies to this record. The owner acts on each hold by closing its blocking pull request.
- **Risk**: The owner may want to review the closures. Each closure reverses with a reopen.

## Issue Facts and Linked Work

- **Issue #4583**: Title `chore(git): a branch holds work with no pull request`. Labels `ci` and `chore`. Author `app/github-actions`. Created 2026-11-02. Last updated 2026-11-11. State `OPEN`.
- **Body**: A report of 52 branches with commits above `main` and no pull request. It asks the reader to open a pull request for each branch before any cleanup.
- **Comments**: 205 comments, all by `jmorrison-juniper`. The first comments record branch assessments. The last comments record serial publication slots.
- **Linked pull requests**: `gh pr list --state all --search 4583` returns no pull request at the snapshot.
- **Report runs**: The workflow ran on each Monday from 2026-10-19 to 2026-11-23. Each run succeeded.

## Branch Evidence for the Issue Body

The table lists each of the 52 names in the issue body. Ahead and behind counts come from the GitHub compare API for rows 1 to 49 and from local git for rows 50 to 52. The commit subjects come from `git log` on the local objects. Each row lists one subject for each commit that the ahead count reports.

| # | Body name | Live name | Head SHA | Ahead | Behind | Files | Lane | Commit subjects |
| - | - | - | - | - | - | - | - | - |
| 1 | `fix/3158-wip-controls` | same | 0f6b375e71 | 1 | 688 | 7 | ready | chore(web-portal): keep the uncommitted draft of #3158 [skip ci] |
| 2 | `fix/3168-structured-signals` | same | 69d19411fb | 1 | 688 | 4 | ready | chore(web-portal): keep the uncommitted draft of #3168 [skip ci] |
| 3 | `fix/3183-status-fallback` | same | 0c46332ad0 | 1 | 688 | 10 | ready | chore(web-portal): keep the uncommitted draft of #3183 [skip ci] |
| 4 | `fix/3222-confirm-details` | same | 18138f9b28 | 1 | 579 | 7 | ready | fix(upgrade-portal): show complete confirmation plan |
| 5 | `jmorrison-jnpr-snmp-fallback-delivery` | same | 73a1edaa97 | 1 | 562 | 3 | ready | fix(snmp): align the container base OID fallback |
| 6 | `fix/3506-site-lock-logs` | same | 8c8fc28d45 | 1 | 562 | 3 | ready | fix(upgrade-portal): record site lock actions and refusals |
| 7 | `recovery/2863-handoff-20261004` | same | 188956f937 | 1 | 531 | 8 | ready | fix(api): refuse invalid tenant request identifiers |
| 8 | `recovery/2711-handoff-20261004` | same | 9e943bfe30 | 1 | 530 | 1 | ready | test(export): require the error record for template failures |
| 9 | `recovery/3575-handoff-20261004` | same | 5746418f8c | 2 | 532 | 39 | ready | test(websockets): prove failed capture response bodies / feat(websockets): support long packet captures |
| 10 | `recovery/3700-handoff-20261004` | same | f253dd3b55 | 1 | 530 | 13 | ready | fix(export): reject native Cradlepoint HTTP refusals |
| 11 | `recovery/3701-handoff-20261004` | same | d2d2421da6 | 1 | 528 | 10 | ready | fix(bootstrap): preserve macOS interpreter library paths |
| 12 | `recovery/2752-handoff-20261004` | same | 024d42ff7f | 1 | 527 | 9 | ready | fix(api): preserve HTTP status in retry diagnostics |
| 13 | `recovery/2861-handoff-20261004` | same | 6cea98a979 | 1 | 525 | 11 | ready | fix(mist-session): reject unusable required tokens |
| 14 | `recovery/2977-handoff-20261004` | same | d6e8eb8672 | 1 | 532 | 24 | ready | fix(juniper-docs): prevent duplicate corpus payload writes |
| 15 | `recovery/3213-handoff-20261004` | same | 8090bc7d19 | 1 | 512 | 13 | held #4208 | fix(upgrade-portal): document the stable capture session signing key |
| 16 | `recovery/3326-handoff-20261004` | same | fa25a39cd3 | 1 | 509 | 16 | ready | fix(upgrade-portal): hide the failure percentage for Big bang |
| 17 | `recovery/3329-handoff-20261004` | same | 7332749c6c | 1 | 509 | 8 | ready | fix(upgrade-portal): count targets of known refused children |
| 18 | `recovery/3295-handoff-20261004` | same | b1fe853fb2 | 1 | 509 | 16 | ready | fix(upgrade-portal): repair the sign-in credential layout |
| 19 | `recovery/3728-handoff-20261004` | same | 533ced9692 | 1 | 508 | 2 | ready | test(web-portal): skip Maps title collection when Playwright is absent |
| 20 | `recovery/3436-handoff-20261004` | same | 0a032e83ab | 2 | 509 | 27 | ready | fix(upgrade-portal): keep paged read results passive / fix(upgrade-portal): report lost capture and gate pages |
| 21 | `recovery/3699-handoff-20261004` | same | c0261d9fba | 1 | 505 | 18 | held #4813 | fix(export): retain documented SLE trend objects |
| 22 | `recovery/3375-handoff-20261004` | same | 499b764f16 | 1 | 502 | 12 | ready | fix(tests): align capture seeds with lifecycle contracts |
| 23 | `recovery/3158-handoff-20261004` | same | ecb0bc87ce | 1 | 501 | 18 | ready | fix(web-portal): add WIP target controls and result guidance |
| 24 | `recovery/3743-handoff-20261004` | same | 4ecd16c7e4 | 1 | 500 | 14 | ready | fix(export): reject failed WiFi response pages |
| 25 | `recovery/3491-handoff-20261004` | same | 97139eb2c6 | 1 | 500 | 14 | ready | fix(upgrade-portal): keep history records compact |
| 26 | `recovery/2747-handoff-20261004` | same | 2d5695fb4e | 1 | 499 | 1 | ready | test(ssh): verify native CLI shell refusals |
| 27 | `recovery/3745-handoff-20261004` | same | 50e3d841df | 1 | 499 | 13 | ready | fix(export): refuse failed organization webhook responses |
| 28 | `recovery/3749-handoff-20261004` | same | 9f930182fa | 1 | 497 | 1 | ready | test(scripts): use native title guard path expectations |
| 29 | `recovery/3161-handoff-20261004` | same | 33141f05cd | 2 | 497 | 9 | ready | test(web-portal): cover stale clipping frame race / fix(web-portal): disclose clipped result values |
| 30 | `recovery/3388-handoff-20261004` | same | ea0a7467b8 | 1 | 496 | 14 | ready | fix(upgrade-portal): refuse unsafe option number tokens |
| 31 | `recovery/3380-handoff-20261004` | same | a3af99af23 | 1 | 496 | 7 | ready | fix(upgrade-portal): verify capture click journey controls |
| 32 | `recovery/3761-handoff-20261004` | same | ebc40dac8d | 1 | 494 | 5 | ready | test(websocket): structure shell log assertions |
| 33 | `recovery/3760-handoff-20261004` | same | 12f10ece09 | 2 | 492 | 2 | ready | test(websocket_streams): correct the loopback client response handling / test(websocket_streams): narrow the nullable fake cloud on_connect handler |
| 34 | `recovery/3769-handoff-20261004` | same | 54188ffcaf | 2 | 492 | 9 | ready | fix(websocket): freeze cleanup terminal decisions / fix(websocket): wait for utility capture cleanup before completion |
| 35 | `recovery/2708-handoff-20261004` | same | f195788a09 | 1 | 490 | 1 | ready | test(mist): assert the complete list error text |
| 36 | `recovery/3818-handoff-20261004` | same | 0bb3149476 | 2 | 486 | 1 | ready | test(export): assert Cradlepoint status behavior / test(export): keep Cradlepoint module in test analysis |
| 37 | `recovery/3738-handoff-20261004` | same | c70007d407 | 2 | 501 | 9 | ready | test(export): preserve CSV suffix qualification WIP / fix(export): preserve existing CSV filename suffixes |
| 38 | `docs/3818-campaign-stop-20261004` | same | 8c3e6cacc6 | 1 | 485 | 1 | ready | docs(handoff): preserve the paused repair campaign |
| 39 | `fix/3292-isolate-retry-e2e-sites` | same | f706902a5a | 2 | 485 | 6 | ready | fix(upgrade-portal): order retry imports / test(upgrade-portal): isolate retry fixtures |
| 40 | `jmorrison-juniper-startup-dependency-reassessment` | same | e849f3fe4e | 3 | 421 | 18 | ready | fix(upgrade-portal): build request dependencies lazily / chore(upgrade-portal): preserve issue 3834 scope audit / docs(spec): generate issue 3834 implementation tasks |
| 41 | `jmorrison-juniper-fix-2863-identifier-defaults-batch-1` | same | 6eec0e4bf0 | 1 | 398 | 13 | ready | fix(upgrade-portal): refuse missing scope identifiers |
| 42 | `jmorrison-juniper-assessment-4026` | same | 83d197e30f | 3 | 393 | 12 | ready | docs(spec): record issue 4026 validation / fix(web-portal): synchronize executor initialization / docs(spec): record operations portal concurrency |
| 43 | `jmorrison-juniper-issue-3416-lint-pattern` | same | 3d51242e41 | 2 | 397 | 1 | ready | test(docs): hold complete diagram reference names / test(diagram): guard complete class references |
| 44 | `jmorrison-juniper-false-success-family-4028` | same | 4be5f321a3 | 2 | 400 | 12 | ready | test(export): strengthen client abort assertion / fix(export): reject menu 209 HTTP failures |
| 45 | `jmorrison-jnpr-test-4035-menu-92-selection-result` | same | 9851ed28ce | 1 | 391 | 5 | ready | test(web-portal): record menu 92 completion defect |
| 46 | `jmorrison-juniper-issue-2746` | same | 4ebe402c19 | 2 | 397 | 42 | held #4208 | test: preserve HTTP proof symbols / test: add HTTP 4xx failure proofs |
| 47 | `jmorrison-juniper-coordinate-issue-work` | same | 29c5489751 | 1 | 430 | 3 | ready | fix(org): handle http refusal in org name lookup |
| 48 | `jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090` | same | d8a7b9c715 | 1 | 315 | 8 | ready | fix(specs): remove nested duplicate feature record |
| 49 | `jmorrison-juniper-issue-2747-wan-probe-test-quality` | same | db030903fb | 1 | 272 | 1 | ready | test(gateway): cover HTTP 503 template refusal |
| 50 | `jmorrison-juniper-publish-test-quality-slice` | `archive/laptop-20261121/jmorrison-juniper-publish-test-quality-slice` | 51603bfefb | 1 | 254 | 1 | ready | test(ui): verify the complete autofilled session result |
| 51 | `jmorrison-juniper-test-quality-second-http-5xx-slice` | `archive/laptop-20261121/jmorrison-juniper-test-quality-second-http-5xx-slice` | 4f71aa5db6 | 1 | 221 | 1 | ready | test(upgrade-portal): cover HTTP 503 site refusal |
| 52 | `jmorrison-juniper-test-quality-http-4xx-slice-6ce` | `archive/laptop-20261121/jmorrison-juniper-test-quality-http-4xx-slice-6ce` | 9b94803e11 | 2 | 219 | 1 | ready | test(firmware): explain HTTP refusal assertions / test(firmware): cover HTTP 403 running-version refusal |

Rows 50 to 52 are renamed. The original names return HTTP 404 (R52 to R54), and the archive names hold the same head SHA (R49 to R51).

## Report Comparison

- The 2026-11-23 report in issue #4911 lists 505 rows.
- The read-only emulation finds 543 in-scope branches on 2026-11-26.
- All 505 report names appear in the 543 names. That includes the 49 live names of the issue body.
- 38 in-scope names do not appear in that report. Section "Report Comparison" in `data-model.md` gives their shared properties.
- The commit subject count in each row of the table equals the ahead count.

## Remote Verification

Column `Blob or commit SHA` holds a blob SHA for files and a commit SHA for pull request heads. It holds `none` for an absent path. Column `Ref` holds `main` for repository files, `origin` for branch paths, and the pinned commit for the sibling repository.

| # | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | AGENTS.md states the one-file rule for open pull requests | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 245 |
| R02 | AGENTS.md states the preservation rule before an unmerged close | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| R03 | The copilot instructions hold the local gates section | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R04 | The stranded branch workflow runs on a weekly schedule | `.github/workflows/stranded-branch-report.yml` | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 20 |
| R05 | The stranded branch workflow calls the shared workflow at commit 79a5e45 | `.github/workflows/stranded-branch-report.yml` | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 47 |
| R06 | The stranded branch workflow passes the quiet period input | `.github/workflows/stranded-branch-report.yml` | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 50 |
| R07 | The contributing guide holds the branch cleanup section | `documentation/contributing.md` | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 52 |
| R08 | The contributing guide warns against deleting a branch with no pull request | `documentation/contributing.md` | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 54 |
| R09 | The contributing guide requires a pull request for each named branch | `documentation/contributing.md` | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 76 |
| R10 | The contributing guide requires deletion only after the pull request step | `documentation/contributing.md` | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 79 |
| R11 | The review document states that the pull request head is the only permanent copy | `documentation/stranded-branch-review.md` | main | 8091539c31ff8648d0426f4a8a92e01e0eb902b4 | present | 46 |
| R12 | The development requirements pin misthelper-devtools at commit 2239e7bd | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| R13 | The CI workflow runs pull request events only for checks_requested | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 19 |
| R14 | The pull request title workflow runs on the opened event and four other events | `.github/workflows/pull-request-title.yml` | main | 6b161b5a7dd71a0f0c9c0f38b750a7322ae8704e | present | 5 |
| R15 | The route helper defines the base-5 segment function | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R16 | The route helper defines the record path function | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R17 | The process folder guard rejects more than five children | `tests/guardrails/test_process_folder_structure.py` | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 34 |
| R18 | The process folder guard expects 792 legacy entries | `tests/guardrails/test_process_folder_structure.py` | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 136 |
| R19 | The spec route contract guard exists | `tests/guardrails/test_spec_route_contract.py` | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| R20 | The process folder baseline exists | `tests/guardrails/process_folder_baseline.json` | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R21 | The constitution states the five-item rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R22 | The STE workflow grades each named file with ste-linter | `.github/workflows/ste-lint.yml` | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 6 |
| R23 | The spec template exists | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R24 | The plan template exists | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R25 | The tasks template exists | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R26 | The checklist template exists | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R27 | The reference record spec exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R28 | The reference record plan exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| R29 | The reference record tasks exist | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| R30 | The reference record analysis exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md` | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| R31 | The reference record research exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| R32 | The route folder for issue 4583 is absent | `specs/numbered/0/0/1/2/1/3/1/3` | main | none | absent | 0 |
| R33 | No legacy record for issue 4583 exists | `specs/**/4583-*` | main | none | absent | 0 |
| R34 | The old WebSocket source path is absent | `src/websocket_streams` | main | none | absent | 0 |
| R35 | The current WebSocket source path holds 221 files | `src/mist/realtime/websocket_streams` | main | none | present | 0 |
| R36 | The report command sets the quiet period to 7 days | `src/misthelper_devtools/stranded_branch_report.py` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 49 |
| R37 | The report command ignores three bot prefixes | `src/misthelper_devtools/stranded_branch_report.py` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 53 |
| R38 | The report command treats an open pull request head name as protection | `src/misthelper_devtools/stranded_branch_report.py` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 104 |
| R39 | The report command reads closed pull requests by head name | `src/misthelper_devtools/stranded_branch_report.py` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 210 |
| R40 | The report command accepts a closed pull request when its compare count is zero | `src/misthelper_devtools/stranded_branch_report.py` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 216 |
| R41 | The shared workflow searches open report issues by title | `.github/workflows/reusable-stranded-branch-report.yml` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 156 |
| R42 | The shared workflow opens a new report issue when the search finds none | `.github/workflows/reusable-stranded-branch-report.yml` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 175 |
| R43 | The shared workflow closes the report issue when no branch is stranded | `.github/workflows/reusable-stranded-branch-report.yml` in misthelper-devtools | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 179 |
| R44 | Open pull request 4208 changes `deploy/.env.example` | `deploy/.env.example` | refs/pull/4208/head | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 0 |
| R45 | Open pull request 4813 changes `tests/unit/export/test_endpoint_family_exporter.py` | `tests/unit/export/test_endpoint_family_exporter.py` | refs/pull/4813/head | c00a85f8b3fe1dc7a972521e6f162aa4881f8dab | present | 0 |
| R46 | Open pull request 4886 changes `.github/workflows/auto-merge.yml` | `.github/workflows/auto-merge.yml` | refs/pull/4886/head | 9e70001433bae97055b6bbe2825a345c0674273e | present | 0 |
| R47 | Open pull request 4887 changes `ops-portal/package-lock.json` | `ops-portal/package-lock.json` | refs/pull/4887/head | 7839c578e1455d6c9a817c04a268c109a4bd725f | present | 0 |
| R48 | Open pull request 4888 changes `requirements-dev.txt` | `requirements-dev.txt` | refs/pull/4888/head | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| R49 | The renamed head of the publish test quality slice exists | `refs/heads/archive/laptop-20261121/jmorrison-juniper-publish-test-quality-slice` | origin | 51603bfefbd4a4b269ff7d83bbe265633bdae5b8 | present | 0 |
| R50 | The renamed head of the second HTTP 5xx slice exists | `refs/heads/archive/laptop-20261121/jmorrison-juniper-test-quality-second-http-5xx-slice` | origin | 4f71aa5db6631073f976987063a8018295af7852 | present | 0 |
| R51 | The renamed head of the HTTP 4xx slice exists | `refs/heads/archive/laptop-20261121/jmorrison-juniper-test-quality-http-4xx-slice-6ce` | origin | 9b94803e112a41e3d80ed94117845a001c63b49e | present | 0 |
| R52 | The original name of the publish test quality slice is absent | `refs/heads/jmorrison-juniper-publish-test-quality-slice` | origin | none | absent | 0 |
| R53 | The original name of the second HTTP 5xx slice is absent | `refs/heads/jmorrison-juniper-test-quality-second-http-5xx-slice` | origin | none | absent | 0 |
| R54 | The original name of the HTTP 4xx slice is absent | `refs/heads/jmorrison-juniper-test-quality-http-4xx-slice-6ce` | origin | none | absent | 0 |

## Sources

- Local files read in the working tree: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates in `.specify/templates/`.
- Remote file reads: `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main` for each line in the remote table, and `gh api repos/jmorrison-juniper/misthelper-devtools/contents/<path>?ref=79a5e45970e876f1656d69520d9635cea1aa25ef` for R36 to R43.
- Remote tree: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree holds 11,404 entries and is not truncated.
- Branch and pull request state: `gh api repos/jmorrison-juniper/MistHelper/branches?per_page=100 --paginate`, `gh pr list --state all`, `gh pr view <number>`, and `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/<branch>`.
- Issue state: `gh issue view 4583`, `gh issue view 4911`, and `gh issue list --search "a branch holds work with no pull request in:title"`.
- Local git reads: `rev-list --count`, `log`, `merge-base`, `merge-base --is-ancestor`, `diff --name-only`, and `for-each-ref`, each run with `git -C <repo>`.
- Web URLs: none fetched. The record relies on local and GitHub API sources only.
- Skills: none loaded. This issue has no Podman, Juniper device, or Mist API work.
- Mist API and mistapi: not applicable. The issue makes no Mist REST call and names no Mist endpoint.

## Unverified

1. The report command did not run in this session. Rule 2 forbids running repository tooling. The emulation includes all 505 names of the 2026-11-23 report.
2. The cause of the 38 in-scope names that the 2026-11-23 report omits is not verified. No push log was read. The names have no open pull request and no closed pull request that holds their head.
3. A closed draft pull request keeps its head. R11 and the report source (R39 and R40) state this rule. No write test ran.
4. The write permission of the account for pull request create and close is not tested.
5. GitHub secondary rate limit values are not read from documentation. The five-second pacing and the backoff waits are procedure choices.
6. The trigger of `ste-lint.yml` on pull request events is not read. Only its named-files lines (R22) were read.
7. `requirements-dev.txt` pins misthelper-devtools at commit 2239e7bd (R12). The shared workflow runs commit 79a5e45 (R05). The reason for the difference is not verified.
8. The duration of the full run is not measured.
9. The exact cause of the failed title search is not verified. The report title contains a colon and parentheses, which GitHub search may read as query syntax. No test query ran.
