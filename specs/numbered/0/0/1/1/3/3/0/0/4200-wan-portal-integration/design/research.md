# Research: WAN Performance portal integration (Issue 4200)

**Record**: `specs/numbered/0/0/1/1/3/3/0/0/4200-wan-portal-integration/`
**Method**: Read-only checks. Remote truth comes from GitHub `main` and from draft PR 4208 head `843be63bc837513b4442dae69da9f0db922e0ed1`. Local `main` equals remote `main` (`f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, row R15).
**Skill use**: No skill loaded. The feature changes no Podman runtime setting and no Juniper device behavior. Local repository documents and the installed mistapi source answered each question.

## Decisions

### D-1 Source reuse and visual capture rights (HUMAN-DECISION-REQUIRED)
- Alternatives: (a) copy source code, fixtures, or screenshots under written rights approval. (b) independent implementation with the source used as a behavior reference only. (c) no reference to the source.
- Chosen: (b). Recommended option: (b).
- Reason: The source README states "Internal use only - Hewlett Packard Enterprise" (R131). The public source repository has no license file (R132). No written rights approval exists in the issue comments.
- Risk: Parity work takes longer. Any copy or visual capture needs approval first.

### D-2 Retention, backfill, and purge (HUMAN-DECISION-REQUIRED)
- Alternatives: (a) keep the bounded 31-day read and no purge job. (b) approve 13-month retention with a purge job. (c) approve a backfill of older records.
- Chosen: (a). Recommended option: (a).
- Reason: The OpenAPI 13-month statement applies to the Premium Analytics product, not to the gateway or peer endpoints (R116). No verified retention contract exists. Warning: a purge destroys production records.
- Risk: The 13-month parity row stays open until a human approves a policy.

### D-3 Product priority for executive, engineering, and SLE views (HUMAN-DECISION-REQUIRED)
- Alternatives: (a) include the views in this issue. (b) split the views to a follow-up issue.
- Chosen: (b). Recommended option: (b).
- Reason: The SDK exposes SLE functions (R127, R128), but the WAN SLE score meaning and entity mapping are unverified (U-3). The four page journeys already define the minimum scope.
- Risk: Customers wait longer for the executive and engineering views.

### D-4 Redis use and failure policy
- Alternatives: (a) keep fail-open admission from `request_admission.py` (R59). (b) fail closed for background refresh and allow operator reads only under a per-process ceiling. (c) remove Redis from WAN work and use process memory only.
- Chosen: (b). Key families: `misthelper:api:v1:*` (existing shared admission, reused) and `misthelper:wan:v1:*` (refresh lease and snapshot keys). TTL: refresh lease 300 seconds (proposed value). Snapshot 3600 seconds (main value, R66).
- Reason: The constitution requires fail-closed behavior for each operational store (constitution line 315). Open admission can exceed the Mist request budget during an outage.
- Risk: Operator reads degrade during a Redis outage. Users see a stale-data state, not a live value.

### D-5 Background refresh default
- Alternatives: (a) default on, as in PR 4208 (R97). (b) default off with explicit opt-in by `WAN_BACKGROUND_REFRESH=true`.
- Chosen: (b). Recommended option: (b).
- Reason: The issue requires bounded Mist calls and bounded background refresh (issue Constraints section). Default-off limits risk at portal start.
- Risk: Operators must enable refresh to see updated snapshots.

### D-6 Route layout and navigation gate
- Alternatives: (a) add WAN pages under `/wan-dashboard`. (b) add `/wan-performance/preview/` for synthetic preview and `/wan-performance/live/` for live pages.
- Chosen: (b). The `/wan-dashboard` routes stay unchanged (FR-018, R79).
- Reason: The issue requires synthetic data separate from live data. PR 4208 gates the nav on `wan_performance.overview` (R97), which is the synthetic route (R93), but links to `wan_performance.live.overview` (R98). The gate must test the live endpoint.
- Risk: Bookmarks to PR 4208 synthetic URLs change.

### D-7 Historical storage path
- Alternatives: (a) a new SQLite file (rejected: second application database). (b) Snowflake (rejected by the issue). (c) the configured store through `DataExporter.write_with_format_selection()` with natural keys.
- Chosen: (c). Reason: constitution line 312 requires data collection to support configured output backends.
- Risk: PR 4208 writes SQLite and ArangoDB rows directly (`integration/sqlite_history.py`, `integration/arango_history.py`). Task T012 moves those writes.

### D-8 Mist API access
- Alternatives: (a) direct HTTP to Mist endpoints (rejected by constitution Technology section). (b) mistapi functions only.
- Chosen: (b). Functions: `searchOrgSwOrGwPorts` (R120), `searchOrgPeerPathStats` (R119), `listOrgDevicesStats` (R121), `getSiteInsightMetricsForGateway` (R122), `getSiteInsightMetricsForDevice` (R123).
- Reason: The SDK exposes each function. The source call `sites.insights.getSiteGatewayMetrics` is absent from the SDK (R125). The function exists in `sites.stats` (R124), which the feature does not need.
- Risk: The SDK signature can change in a later release. The pin `mistapi>=0.64.0,<0.65` limits the change.

### D-9 Historical VPN peer metrics
- Alternatives: (a) build a time series from repeated snapshots (rejected: invents history). (b) show the latest peer snapshot and mark history as an explicit gap.
- Chosen: (b). Reason: OpenAPI lists only VPN peer count and search operations (R109, R110).
- Risk: The VPN peer page cannot show trends until a verified endpoint exists.

### D-10 Synthetic preview labeling
- Alternatives: (a) one route with a query flag. (b) a separate `/wan-performance/preview/` route, a visible banner, and `data_origin` set to `synthetic` on each record.
- Chosen: (b). Reason: The issue requires that synthetic data never appear as live data. PR 4208 already uses a separate synthetic overview route (R93).
- Risk: Tests must check the banner on each synthetic page.

### D-11 PR 4208 reconciliation
- Alternatives: (a) overwrite the 11 main files with PR 4208 versions (rejected: drops merged PR 4629 content, R06). (b) keep main content as the base and port PR 4208 changes in reviewed commits. (c) close PR 4208 and restart (rejected: discards preserved recovery branches, R04, R05).
- Chosen: (b). Recommended option: (b).
- Reason: Main is the released state. PR 4629 changed the 11 files (R56-R66). PR 4208 is a dependency, not the base.
- Risk: The porting work takes longer. The PR 4208 owner asked for a human decision before reconciliation (issue comment 2026-11-10T21:57:21Z). This record leaves that request open for the owner.

### D-12 Legacy record disposition
- Alternatives: (a) reuse the path `4200-wan-parity-recovery` (rejected: add/add collision with PR 4208 branch files R16-R26). (b) a new slug `wan-portal-integration`. (c) discard the legacy record (rejected: loses verified evidence).
- Chosen: (b). The legacy record stays on the PR 4208 branch. Only verified legacy claims enter this record (R16-R55).
- Risk: Two records describe one issue until PR 4208 closes.

### D-13 Issue closure keyword
- Alternatives: (a) `Closes #4200` in the pull request body, as the brief template requires. (b) `Refs #4200`.
- Chosen: (b). Reason: The issue owner keeps issue 4200 open until acceptance (comments 2026-10-16T20:14:55Z, 2026-11-14T22:14:21Z). PR 4208 already names #4200 as a closing issue (R01 context), so a closing keyword can close the issue on merge.
- Risk: Reviewers must close the issue by hand after acceptance.

### D-14 Structured logging
- Alternatives: (a) standard `logging.getLogger` as in PR 4208 (R107). (b) `structlog`, as 22 repository source files use (sampled by `git grep -l structlog` on `main`).
- Chosen: (b). Reason: constitution Principle V (line 182) requires structured entries for each new service or module.
- Risk: Each touched module needs a logger change.

### D-15 Five-child layout
- Alternatives: (a) keep the PR 4208 layout (rejected: six children in five directories, R106 and the directory list in plan.md). (b) nested packages.
- Chosen: (b). The file map in plan.md shows the nested paths.
- Risk: Import paths change. Each import needs an update in the same change.

## Remote verification

Result values: `present`, `absent`, `partial`, or `stale`. The count of rows equals the `remote_checks` count in `4200-STATUS.json`. The existing-record counts use the legacy rows. Rows R16-R26, R27-R55, R139, and R140 count as verified (41 rows). Rows R45, R141, and R142 count as absent (3 rows). Row R143 counts as stale (1 row).

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|---|---|---|---|---|---|---|
| R01 | PR 4208 is open, draft, DIRTY, and lists #4200 as a closing issue | PR #4208 | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | present | 0 |
| R02 | PR 4208 body says the branch is conflict-free | PR #4208 body | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | stale | 0 |
| R03 | Head branch jmorrison-juniper-4200-migrate-mistwanperformance is at 843be63 | branch | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | present | 0 |
| R04 | Branch recovery/4208-pre-csrf-admission-b035341 is at b035341 | branch | b035341759d03df7589c11213c6ea9f3a5d7bc57 | n/a | present | 0 |
| R05 | Branch recovery/4208-gateway-reviewed-ff9615 exists | branch | ff9615db61f6f16393d9ab264ab9d3528e109599 | n/a | present | 0 |
| R06 | PR 4629 merged 2026-11-07 (WAN collection base) | PR #4629 | main | n/a | present | 0 |
| R07 | PR 4750 merged 2026-11-10 | PR #4750 | main | n/a | present | 0 |
| R08 | PR 4757 merged 2026-11-10 (auth replay fix) | PR #4757 | main | n/a | present | 0 |
| R09 | PR 4358 merged 2026-11-13 | PR #4358 | main | n/a | present | 0 |
| R10 | PR 4291 merged 2026-10-19 (Redis migration spec) | PR #4291 | main | n/a | present | 0 |
| R11 | Issue 4793 is open (duplicate WAN history sample) | issue #4793 | main | n/a | present | 0 |
| R12 | Issue 4794 is open (missing flap_count) | issue #4794 | main | n/a | present | 0 |
| R13 | Issue 4795 is open (WAN gateway history disappears) | issue #4795 | main | n/a | present | 0 |
| R14 | Issue 4796 is closed (route test failure) | issue #4796 | main | n/a | present | 0 |
| R15 | Remote main equals local main | refs/heads/main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | n/a | present | 0 |
| R16 | Legacy spec.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/spec.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 19126c68b5f977bff9d8b09b8d32172c94f0de21 | present | 0 |
| R17 | Legacy plan.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/plan.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 2dcdd77bfa3cec81be8374f5bba6509e7a5a682b | present | 0 |
| R18 | Legacy tasks.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/tasks.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 995e727fd9385ebb3e5efc6af2e2ee48f3cc8b0f | present | 0 |
| R19 | Legacy analysis.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/analysis.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | bd8da16d5b9892a82561adfbac59d0e4daa0259d | present | 0 |
| R20 | Legacy design/research.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/research.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 72eb4359a17ffe0937ec2693089b1c9572bb29e3 | present | 0 |
| R21 | Legacy design/data-model.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/data-model.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 07d7d7a34641a29e067fcb6166fb91428c842e68 | present | 0 |
| R22 | Legacy design/quickstart.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/quickstart.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 82d1bc9ea56793a96b14381aeec13838bb61d539 | present | 0 |
| R23 | Legacy design/checklists/requirements.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/checklists/requirements.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1bed11557f16ee8f7dbb676e9f38f94936cef32b | present | 0 |
| R24 | Legacy design/contracts/discovery.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/contracts/discovery.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 14c41f08c9a1e3f4932c359c85c4df42ed9aa770 | present | 0 |
| R25 | Legacy design/contracts/parity.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/contracts/parity.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | c26cbede3bd010cf27a0dbe5d55e1f3c9b19552a | present | 0 |
| R26 | Legacy design/contracts/replacements.md exists at PR head | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/contracts/replacements.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | e92b1471d3ebde697fa47df213e66dcbe5da4808 | present | 0 |
| R27 | Commit 11d692592accd8f4b41d2e5cb46f42869f6d4d33 exists | commit 11d692592accd8f4b41d2e5cb46f42869f6d4d33 | main | n/a | present | 0 |
| R28 | Commit f632c19e236e90a503b68d17f512dd7b391363b0 exists | commit f632c19e236e90a503b68d17f512dd7b391363b0 | main | n/a | present | 0 |
| R29 | Commit 51fdff653f03b3335e959f599c44904c68716cd8 exists | commit 51fdff653f03b3335e959f599c44904c68716cd8 | main | n/a | present | 0 |
| R30 | Commit cb5abb377cffe0744d2f16c396569581fc48b1e9 exists | commit cb5abb377cffe0744d2f16c396569581fc48b1e9 | main | n/a | present | 0 |
| R31 | Commit f641147af185682141e86637615078c885f0615f exists | commit f641147af185682141e86637615078c885f0615f | main | n/a | present | 0 |
| R32 | Commit acb4e34244dfec4cdf78f6f44ab08d5b61aa8725 exists | commit acb4e34244dfec4cdf78f6f44ab08d5b61aa8725 | main | n/a | present | 0 |
| R33 | Commit 0bfe3e21ac36829c7e1f9f56a1a2f917599c7eef exists | commit 0bfe3e21ac36829c7e1f9f56a1a2f917599c7eef | main | n/a | present | 0 |
| R34 | Commit 481cc3b56aa5067089baa49d5758ffd88ade8f0b exists | commit 481cc3b56aa5067089baa49d5758ffd88ade8f0b | main | n/a | present | 0 |
| R35 | Commit b035341759d03df7589c11213c6ea9f3a5d7bc57 exists | commit b035341759d03df7589c11213c6ea9f3a5d7bc57 | main | n/a | present | 0 |
| R36 | Commit 20df3e41b350bcac918ae1ba946cb695a5bab46f exists | commit 20df3e41b350bcac918ae1ba946cb695a5bab46f | main | n/a | present | 0 |
| R37 | Commit 843be63bc837513b4442dae69da9f0db922e0ed1 exists (PR 4208 head) | commit 843be63bc837513b4442dae69da9f0db922e0ed1 | main | n/a | present | 0 |
| R38 | Commit 2a6a5844698aeb180fea353e0243034890774565 exists (merge base) | commit 2a6a5844698aeb180fea353e0243034890774565 | main | n/a | present | 0 |
| R39 | Commit c9aa2bbc01893a07bb7eec1a6462026a6e70b41b exists (main at 2026-11-10) | commit c9aa2bbc01893a07bb7eec1a6462026a6e70b41b | main | n/a | present | 0 |
| R40 | Commit 1a408c9511d8b32662d201068f2f54196f643450 exists | commit 1a408c9511d8b32662d201068f2f54196f643450 | main | n/a | present | 0 |
| R41 | Commit c57c9b704c1ce23976228cd72cad80b9d99926be exists (main at 2026-11-05) | commit c57c9b704c1ce23976228cd72cad80b9d99926be | main | n/a | present | 0 |
| R42 | Commit fbb23f8a2348e6840caf479dc10d8841635ea91e exists | commit fbb23f8a2348e6840caf479dc10d8841635ea91e | main | n/a | present | 0 |
| R43 | Commit d77a900f9ec4db7149f90f324f1ade7772a6243d exists | commit d77a900f9ec4db7149f90f324f1ade7772a6243d | main | n/a | present | 0 |
| R44 | Commit 816f42bac74aebfb936ac9fc9b72fe1ec2030c09 exists | commit 816f42bac74aebfb936ac9fc9b72fe1ec2030c09 | main | n/a | present | 0 |
| R45 | Commit 40278aa1948cda154f7372c1b0dd893b3865c9f5 is cited by the legacy analysis | commit 40278aa1948cda154f7372c1b0dd893b3865c9f5 | main | n/a | absent | 0 |
| R46 | Commit d519094517ab73f32168fe63a823e3168252a43b exists | commit d519094517ab73f32168fe63a823e3168252a43b | main | n/a | present | 0 |
| R47 | Commit 2326357014930504e0c6fb68e741f142dbccb106 exists | commit 2326357014930504e0c6fb68e741f142dbccb106 | main | n/a | present | 0 |
| R48 | Commit 36f72b08d6eb9b0b7de2dae319d4d593050b6be3 exists | commit 36f72b08d6eb9b0b7de2dae319d4d593050b6be3 | main | n/a | present | 0 |
| R49 | Commit 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc exists | commit 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | main | n/a | present | 0 |
| R50 | Commit d7a706d71cf13661cf33e5b4a96ddafd79b6b67b exists | commit d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | main | n/a | present | 0 |
| R51 | Commit df83c353b0efe35b1cfd4436133455ff9c2fc7c0 exists | commit df83c353b0efe35b1cfd4436133455ff9c2fc7c0 | main | n/a | present | 0 |
| R52 | Commit 565213a7aed67615a82c2bd92961cce12264ea31 exists | commit 565213a7aed67615a82c2bd92961cce12264ea31 | main | n/a | present | 0 |
| R53 | Commit d476f19e385941a7958ad36b030aa327f0f4e8d0 exists | commit d476f19e385941a7958ad36b030aa327f0f4e8d0 | main | n/a | present | 0 |
| R54 | Short SHA 960d81c resolves to 960d81c76050167ac8886dfc2292f9dfa520770e | commit 960d81c76050167ac8886dfc2292f9dfa520770e | main | n/a | present | 0 |
| R55 | MistWANPerformance pinned source revision exists | jmorrison-juniper/MistWANPerformance commit 2d1c2199fa1e31c129ef1e051c5389349a207785 | 2d1c2199fa1e31c129ef1e051c5389349a207785 | n/a | present | 0 |
| R56 | Main has WAN add/add file (PR 4629) | src/interfaces/wan_performance/__init__.py | main | b1638ab4517329e155dbff58d7a74500fd562eec | present | 0 |
| R57 | Main has WAN add/add file (PR 4629) | src/interfaces/wan_performance/collection/__init__.py | main | 5dd53f9be2b0b7a1e848a852268b12706da0923c | present | 0 |
| R58 | Main has WAN add/add file. PEER_ROW_LIMIT is 2 | src/interfaces/wan_performance/collection/peer_insights.py | main | 0433c69a95c75e866c0693baebe3ce772d60dc9b | present | 12 |
| R59 | Main has WAN add/add file. Shared admission keys and fail-open path | src/interfaces/wan_performance/collection/request_admission.py | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 82 |
| R60 | Main has WAN add/add file. Mistapi calls and page limit 100 | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 17 |
| R61 | Main has WAN add/add file (PR 4629) | src/interfaces/wan_performance/collection/snapshot_records.py | main | bb73aed2de9a3e8db18c6f83ea057a7c48ef1c74 | present | 0 |
| R62 | Main has WAN add/add file (PR 4629) | src/interfaces/wan_performance/domain/__init__.py | main | 9f87f1a88519276d90116296413b5e67e5730e53 | present | 0 |
| R63 | Main has WAN add/add file. IdentityValidator class | src/interfaces/wan_performance/domain/identity.py | main | 437582449d8c3355f71aa35390050cb06be0ddc1 | present | 7 |
| R64 | Main has WAN add/add file (PR 4629) | src/interfaces/wan_performance/domain/measurement.py | main | 79a02452d82b4117aec6ddbf3fc549e230d342c3 | present | 0 |
| R65 | Main has WAN add/add file (PR 4629) | src/interfaces/wan_performance/domain/metric_validation.py | main | 77cfc1da9cbba9ee56e7bc0db4becfa8d2d42f8c | present | 0 |
| R66 | Main has WAN add/add file. Refresh key and 3600-second snapshot TTL | src/interfaces/wan_performance/integration/refresh_store.py | main | 76ff0cdcc6abe7e8aed874a9e9e6bc89ad2cf8c8 | present | 24 |
| R67 | Guardrail test exists on main. PR 4208 adds 61 lines (conflict status unverified) | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 0 |
| R68 | Background worker module is absent on main | src/interfaces/wan_performance/background_refresh.py | main | n/a | absent | 0 |
| R69 | Presentation package is absent on main | src/interfaces/wan_performance/presentation | main | n/a | absent | 0 |
| R70 | Unit test package for WAN performance is absent on main | tests/unit/wan_performance | main | n/a | absent | 0 |
| R71 | Portal registers the existing WAN dashboard blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 207 |
| R72 | Main base.html has no WAN Performance nav entry | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| R73 | Shared env template exists | deploy/.env.example | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 0 |
| R74 | Mist session configurator exists | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 35 |
| R75 | SecurityMiddleware allowlist class exists | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 159 |
| R76 | Test fixtures flask_app and client exist | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 260 |
| R77 | Existing WAN dashboard browser tests exist (six functions) | tests/e2e/web_portal/test_wan_dashboard_cache_only.py | main | a51f0f8495f8200352db7cbaf15c2a16eae0b853 | present | 118 |
| R78 | PR 4208 head has no files under tests/unit/wan_dashboard/wan_performance (main has eight) | tests/unit/wan_dashboard/wan_performance | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | absent | 0 |
| R79 | Existing WAN dashboard blueprint and URL rules exist | src/interfaces/portals/wan_dashboard/routes.py | main | d58229ce8f0c15998785f88b3cbf5a7009e15f58 | present | 21 |
| R80 | Existing WAN dashboard worker configuration keys exist | src/interfaces/portals/wan_dashboard/services/worker.py | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | present | 37 |
| R81 | Compose group defines services and published ports | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 53 |
| R82 | Test and debug container policy exists | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R83 | Playwright gate row exists | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 68 |
| R84 | VPN peer endpoints show 0 of 2 implemented in MistHelper.py usage | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 109 |
| R85 | VPN peer section lists two endpoints | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 106 |
| R86 | Constitution version 1.9.0 with Principles I to VII | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R87 | Route script base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R88 | Process folder baseline exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R89 | Changelog fragment rules exist | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| R90 | PR head adds worker lease with format-based key | src/interfaces/wan_performance/background_refresh.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | b08895652d7450e24399bed66c3763b46a0fa5c9 | present | 23 |
| R91 | PR head adds live service module | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 19 |
| R92 | PR head live blueprint uses /live and defines overview | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 43 |
| R93 | PR head synthetic overview route is wan_performance.overview | src/interfaces/wan_performance/presentation/routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1b7dbc5dfe0c56ca6cea9dd6bf15847b4dae80fc | present | 77 |
| R94 | PR head adds synthetic preview module | src/interfaces/wan_performance/presentation/offline_preview.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | b629d27aec2ff7fb5c349840f7c7d46cfb3cdaf9 | present | 0 |
| R95 | PR head live template has 90 data-testid attributes | src/interfaces/wan_performance/presentation/templates/wan_performance/live.html | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1f63bc8316b05052cdb3d0bf554c5b9159a40593 | present | 0 |
| R96 | PR head overview template has 9 data-testid attributes | src/interfaces/wan_performance/presentation/templates/wan_performance/overview.html | 843be63bc837513b4442dae69da9f0db922e0ed1 | 2ee200c8d1061c73b9ba0103b84ccc98e6a26b0e | present | 0 |
| R97 | PR head nav gate tests the synthetic endpoint, not the live endpoint | web_portal/app.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | f0d9f5b63eb2f5465a2c5034c7887e7fa32736d3 | partial | 221 |
| R98 | PR head nav link targets the live overview endpoint | web_portal/templates/base.html | 843be63bc837513b4442dae69da9f0db922e0ed1 | dab25f33e74d3f3ece20f801beabef23e04db5a7 | present | 82 |
| R99 | PR head adds shared admission hook and renames private helpers | src/foundation/support/refactors/initialize_mist_session.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 9bf7be0521c468f17fc4552287d89d75a26700e8 | present | 41 |
| R100 | PR head live browser tests define 93 functions | tests/e2e/web_portal/test_wan_performance_live.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d485c28afb5bf4bd6de20ba9291feb9b267babac | present | 0 |
| R101 | PR head offline browser tests define 19 functions | tests/e2e/web_portal/test_wan_performance_offline.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 86a0cef21fe97dd02d217d551be998298ec2cc30 | present | 0 |
| R102 | PR head adds WAN performance document | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 0 |
| R103 | PR head adds changelog fragment named for PR 4208 | changelog.d/pr-4208.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 3d571a370f9cd3b6a7e3367b96dcc652ddf4653e | present | 0 |
| R104 | PR head adds WAN stylesheet | web_portal/static/css/wan_performance.css | 843be63bc837513b4442dae69da9f0db922e0ed1 | a58847dd2ffa78521d1a86903cab9a4eab7b9fb0 | present | 0 |
| R105 | PR head adds two WAN environment names, commented out | deploy/.env.example | 843be63bc837513b4442dae69da9f0db922e0ed1 | 069b497c2aec80f9eb8eb888b74056b0b0001fb9 | present | 42 |
| R106 | PR head directories each have six children (limit is five): WAN package, collection, domain, integration, presentation | src/interfaces/wan_performance | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | partial | 0 |
| R107 | PR head WAN worker logs with logging.getLogger, not structlog | src/interfaces/wan_performance/background_refresh.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | b08895652d7450e24399bed66c3763b46a0fa5c9 | partial | 17 |
| R108 | OpenAPI operation listOrgDevicesStats exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 21396 |
| R109 | OpenAPI has no VPN peer time-series path (count and search only) | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 22422 |
| R110 | OpenAPI operation searchOrgPeerPathStats is on vpn_peers/search | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 22457 |
| R111 | OpenAPI operation searchOrgSwOrGwPorts is on ports/search | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 22034 |
| R112 | OpenAPI operation getSiteInsightMetricsForDevice exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32678 |
| R113 | OpenAPI operation getSiteInsightMetricsForGateway exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32717 |
| R114 | OpenAPI operation getSiteGatewayMetrics is on stats/gateways/metrics | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 39885 |
| R115 | OpenAPI operation searchSiteSwOrGwPorts is on stats/ports/search | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 40386 |
| R116 | Premium Analytics stores up to 13 months. Standard analytics keeps 30 days | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 804 |
| R117 | search_after is a cursor from the next URL and must not be built | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 60227 |
| R118 | mistapi 0.64.1 is installed locally | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | mistapi 0.64.1 local install | n/a | present | 0 |
| R119 | SDK function searchOrgPeerPathStats is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | mistapi 0.64.1 local install | n/a | present | 1592 |
| R120 | SDK function searchOrgSwOrGwPorts is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | mistapi 0.64.1 local install | n/a | present | 1157 |
| R121 | SDK function listOrgDevicesStats is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | mistapi 0.64.1 local install | n/a | present | 397 |
| R122 | SDK function getSiteInsightMetricsForGateway is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | mistapi 0.64.1 local install | n/a | present | 290 |
| R123 | SDK function getSiteInsightMetricsForDevice is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | mistapi 0.64.1 local install | n/a | present | 219 |
| R124 | SDK function getSiteGatewayMetrics is defined in sites.stats | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | mistapi 0.64.1 local install | n/a | present | 1536 |
| R125 | SDK function getSiteGatewayMetrics is absent from sites.insights | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | mistapi 0.64.1 local install | n/a | absent | 0 |
| R126 | SDK function searchSiteSwOrGwPorts is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | mistapi 0.64.1 local install | n/a | present | 2120 |
| R127 | SDK function getSiteSleSummary is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\sle.py | mistapi 0.64.1 local install | n/a | present | 770 |
| R128 | SDK function listSiteSlesMetrics is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\sle.py | mistapi 0.64.1 local install | n/a | present | 1004 |
| R129 | SDK function listSiteDevicesStats is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | mistapi 0.64.1 local install | n/a | present | 1051 |
| R130 | Main peer call keywords mac, site_id, duration, and limit match the SDK signature | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 121 |
| R131 | Source README declares internal use only | jmorrison-juniper/MistWANPerformance README.md | 2d1c2199fa1e31c129ef1e051c5389349a207785 | 6367d549dcb5a16766007eae1b4fbd123ce0cfa4 | present | 53 |
| R132 | Source repository has no root LICENSE, LICENSE.md, or LICENSE.txt | jmorrison-juniper/MistWANPerformance LICENSE | 2d1c2199fa1e31c129ef1e051c5389349a207785 | n/a | absent | 0 |
| R133 | PR 4208 file list adds 82 files, including storage adapters, calendar, and summary modules | PR #4208 file list | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | present | 0 |
| R134 | 22 repository source files on main use structlog | src and web_portal (git grep on main) | main | n/a | present | 0 |
| R135 | PR head live routes exist for overview, site, gateway, port, VPN peer, and three POST refresh routes | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 268 |
| R136 | PR head synthetic routes exist for overview, gateway, port, and VPN peer under the root prefix | src/interfaces/wan_performance/presentation/routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1b7dbc5dfe0c56ca6cea9dd6bf15847b4dae80fc | present | 94 |
| R137 | SDK searchOrgSwOrGwPorts accepts device_type, mac, and limit | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | mistapi 0.64.1 local install | n/a | present | 1181 |
| R138 | Main portal applies CSRF protection and exempts the webhook blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 236 |
| R139 | Legacy tasks.md has 43 checked and 23 unchecked task lines (66 tasks) | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/tasks.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 995e727fd9385ebb3e5efc6af2e2ee48f3cc8b0f | present | 0 |
| R140 | Legacy spec.md defines 24 FR identifiers and 14 SC identifiers | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/spec.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 19126c68b5f977bff9d8b09b8d32172c94f0de21 | present | 0 |
| R141 | Legacy research.md has no Unverified section and no remote verification table | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/research.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 72eb4359a17ffe0937ec2693089b1c9572bb29e3 | absent | 0 |
| R142 | Legacy plan.md has no risk section and no rollback section | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/plan.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 2dcdd77bfa3cec81be8374f5bba6509e7a5a682b | absent | 0 |
| R143 | Legacy analysis.md line 856 states 12 complete, 8 buildable, and 27 blocked of 47, which conflicts with its task audit | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/analysis.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | bd8da16d5b9892a82561adfbac59d0e4daa0259d | stale | 856 |
| R144 | Legacy record holds 17 occurrences of a placeholder tag forbidden by rule 9 (analysis 3, plan 1, spec 3, research 5, discovery 3, parity 2) | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | present | 0 |
| R145 | Legacy parity.md holds one three-dot ellipsis, forbidden by rule 9 | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/design/contracts/parity.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | c26cbede3bd010cf27a0dbe5d55e1f3c9b19552a | present | 313 |
| R146 | PR 4208 head has 52 hosted checks: 42 success, 10 skipped, zero failures | PR #4208 checks | 843be63bc837513b4442dae69da9f0db922e0ed1 | n/a | present | 0 |

## Sources

- Local repository paths with line ranges appear in the table above, and in plan.md and tasks.md.
- Governance: `AGENTS.md` lines 40 (writing style), 157 (safety), 179 (git flow). `.github/copilot-instructions.md` lines 50 (local gates), 354 (containers and ports), 501 (pull request titles). `.specify/memory/constitution.md` lines 38-235 (Principles I to VII), 312 (output backends), 315 (operational store), 330 (container security).
- Container policy: `documentation/container-deployment.md` lines 141-210 (test and debug containers, ports 9600 to 9699).
- Mist API: OpenAPI rows R108-R117. Coverage documents: R84, R85.
- SDK: rows R118-R130. The package path is local. It is not a repository path.
- Upstream: `https://github.com/jmorrison-juniper/MistWANPerformance` (checked with the GitHub API, not a web fetch). Rows R55, R131, and R132.

## Unverified

- U-1: Source behavior of MistWANPerformance at revision 2d1c2199. No source file was read. Only the README and the root license check were read (R131, R132).
- U-2: The source call `sites.insights.getSiteGatewayMetrics`. The SDK absence is verified (R125). The source call is not verified (U-1).
- U-3: The WAN SLE score meaning and entity mapping. The SDK functions exist (R127, R128). No WAN-specific SLE field contract was read.
- U-4: The history method argument mismatch described in the issue comment of 2026-11-06T00:04:54Z. The source was not read, so the claim is not verified.
- U-5: Test pass counts in issue comments (642, 478, 404, 137). No test was run. Rule 2 forbids test execution in this task.
- U-6: Live Mist API responses for gateway insights and peer statistics. No live call was made. Rule 2 and the issue forbid production requests.
- U-7: Visual parity with the source user interface. No capture was made because rights are absent (D-1).
- U-8: The guardrail test conflict status (R67). The PR head blob SHA was not fetched.
- U-9: Constitution compliance beyond the sampled lines. Inline comments and action logging were sampled, not audited for each line.
- U-10: Local gate commands from `copilot-instructions.md` were not run (rule 2).
- U-11: Legal effect of the absent license file (R132). The human decision D-1 owns that question.
- U-12: Behavior of Redis under load. The fail-closed rule in D-4 is a design choice, not a measured result.
