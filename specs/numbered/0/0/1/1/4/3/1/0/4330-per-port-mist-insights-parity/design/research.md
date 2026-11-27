# Research: Per-port Mist Insights parity in the WAN dashboard

This file records the decisions, the remote verification table, the sources, and the unverified items. The remote checks read `main` through `gh api`. The SDK checks read the installed `mistapi` 0.64.1 files under `.venv`. Each row uses one blob SHA and one line. A blank blob SHA means that the claim concerns a missing item, so the value is `none`.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. The `Human` line marks a decision that needs a human. Every other decision is final for this record.

### D-1 Owner of the parity work

- **Decision**: The canonical WAN dashboard at `/wan-dashboard` owns the feature. The code lives in `src/interfaces/portals/wan_dashboard/`.
- **Alternatives**: (a) Wire the `wan_performance` presentation from pull request #4208. (b) Add a separate per-port page.
- **Reason**: The canonical dashboard merged through pull request #4252. Its blueprint is registered in the portal (R-17). The `wan_performance` collector has no portal path on `main` (A-09). A second page breaks the one-dashboard rule in the issue.
- **Risk**: Pull request #4208 may keep the `wan_performance` path alive (A-10). Mitigation: D-12.
- **Human**: No.

### D-2 Where the port series is read

- **Decision**: The refresh worker reads one seven-day hourly series for each WAN port. The routes stay cache-only. One series yields the 1h, 6h, 24h, 3d, and 7d ranges by slicing.
- **Alternatives**: (a) Read from a route on demand. (b) Read every port in every refresh without a cap. (c) Keep the bulk counters only.
- **Reason**: The routes must not call Mist (R-03, R-04, R-05). An uncapped read exceeds the budget (U-1, R-42). The bulk counters are cumulative since reboot (R-41). One request yields every range (R-40). The source also reads one hourly series for each port (R-54, R-55).
- **Risk**: The 1h range has one hourly sample, so its resolution is low. Mitigation: the port view states the resolution.
- **Human**: No.

### D-3 SDK request shape

- **Decision**: Call `getSiteInsightMetricsForGateway` with `mist_session`, `site_id`, `device_id`, and `metrics` set to `rx_bps,tx_bps`. Set `port_id`, `start`, and `end` to epoch seconds. Set `interval` to `1h`, `limit` to 168, and `page` to 1. Do not set `duration`.
- **Alternatives**: (a) Set `duration` to `7d` without `start` and `end`. (b) Set `interval` to the integer 3600. (c) Use direct HTTP.
- **Reason**: The SDK adds `port_id` only when it has a value (R-45). The explicit window gives an exact UTC range (R-38). The limit of 168 covers the window and avoids the default of 100 (R-46, R-43). Direct HTTP is forbidden when an SDK method exists (R-69).
- **Risk**: The live acceptance of `limit` 168 is unverified (U-3).
- **Human**: No.

### D-4 Response contract

- **Decision**: Accept the named arrays `timestamps`, `rx_bps`, and `tx_bps`, plus the metadata `start`, `end`, and `interval`. Reject every other shape. Record the OpenAPI names `results` and `rt` as an unresolved conflict.
- **Alternatives**: (a) Accept only the OpenAPI names. (b) Accept both shapes.
- **Reason**: The source reads named arrays (R-77, R-55). The canonical code and its tests use named arrays (R-31). The OpenAPI schema names different fields (R-39). Accepting both shapes would guess the live shape, which AGENTS.md forbids.
- **Risk**: The live response may use the OpenAPI names. The parser then rejects every response (A-04). Mitigation: the parser fails closed. U-2 needs an owner-approved live shape check.
- **Human**: No.

### D-5 Byte totals and coverage

- **Decision**: Derive each seven-day byte total as the floor of the sum of present bits per second times 3600, divided by 8. Coverage equals the present samples divided by 168. A series with a `next` value or fewer than 168 samples is partial.
- **Alternatives**: (a) Round each sample before summing. (b) Treat a missing sample as zero, which the source does (R-61). (c) Use the bulk counters.
- **Reason**: The source formula is simple and matches FR-008 (R-55). A missing sample is not a zero measurement (FR-011). The bulk counters measure a different period (R-41).
- **Risk**: The totals differ from production totals if Mist drops samples (U-5). Mitigation: the partial state and the coverage value.
- **Human**: No.

### D-6 Overview copy

- **Decision**: State that the RX and TX counters are cumulative since the last device reboot.
- **Alternatives**: (a) Keep the copy and add a footnote. (b) Remove the RX and TX values.
- **Reason**: Mist defines the port counters as cumulative since reboot (R-41). The current copy names seven-day totals (R-14). Removing the values would reduce the overview contract (FR-014).
- **Risk**: Operators see a new label. Mitigation: TC-21 checks the copy.
- **Human**: No.

### D-7 Admission, retries, and tenant context

- **Decision**: Each port series read calls the service request method once for each token. The runner clone keeps the SDK retry count at zero (R-11, R-49). Site-scoped reads run inside a new `organization_scope` in `request_admission.py`. An admission refusal fails closed (R-22).
- **Alternatives**: (a) Bind a second ledger to the worker session. (b) Pass the organization into the global ledger at session setup. (c) Remove site-scoped reads.
- **Reason**: The global ledger connects without an organization (R-25), so a site read has no tenant (R-22). A second ledger changes the transport that the runner clones, which needs separate review. Removing the reads would remove the feature. The scope keeps the change in one module.
- **Risk**: Pull request #4208 and the owner's local change touch the same module (A-10, A-11). Mitigation: D-12.
- **Human**: No.

### D-8 Request cap and headroom

- **Decision**: Add the operator setting `WAN_PORT_INSIGHT_REQUEST_CAP`. The value is empty by default, which disables the phase. The phase reads at most the cap in each refresh. The planned calls for each token must stay at or below 2,500 for each hour. The formula is `refreshes_per_hour` times the sum of the bulk calls and the port calls. Here, `refreshes_per_hour` equals 3600 divided by `WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS` (R-19).
- **Alternatives**: (a) A default cap from an estimate. (b) No cap with a fixed port list. (c) A cap for each organization only.
- **Reason**: The production counts are unmeasured (U-1). A default number would invent data (AGENTS.md). The headroom leaves room for other reads and avoids HTTP 429 (R-42, R-20).
- **Risk**: A small cap gives partial port coverage. Mitigation: the cursor rotation (D-9) and the operator guide (T010).
- **Human**: No. Enablement is decided in D-14.

### D-9 Cursor rotation

- **Decision**: Sort the WAN ports by device identifier and port identifier before each refresh. Store the cursor in the worker status record. Advance the cursor by the number of calls. Wrap the cursor at the end of the list.
- **Alternatives**: (a) Select ports at random. (b) Select the port with the oldest collection time first. (c) Store the cursor under a separate Redis key.
- **Reason**: Deterministic rotation covers every port over repeated refreshes. The worker status record already stores worker state through `write_status` (R-78). A separate key adds a second write path.
- **Risk**: A changed port list shifts the coverage. Mitigation: the list sorts again before each refresh, as TC-12 checks.
- **Human**: No.

### D-10 Data states and labels

- **Decision**: Use four data states: `live`, `stale`, `partial`, and `unavailable`. Show each state with the UTC collection time and the coverage. Never label stale or synthetic data as live.
- **Alternatives**: (a) Use two states. (b) Show the state by color only.
- **Reason**: The issue requires operators to tell live, stale, incomplete, and unavailable results apart. The existing code already uses the `stale` and `unavailable` statuses (R-10, R-64).
- **Risk**: More text in the port view. Mitigation: short labels and the `data-testid` values from T008.
- **Human**: No.

### D-11 Source provenance and license

- **Decision**: Implement from the Mist API contract only. Copy no source code, tests, fixtures, screenshots, or assets from the source repository. Record the source repository, the commit, and the license blob as provenance (R-58, R-59). Draft the attribution notice for human approval.
- **Alternatives**: (a) Port the source functions. (b) Wait for a license exemption before any work.
- **Reason**: The source license is CC BY-NC-SA 4.0 (R-58). A clean-room implementation avoids a derivative work. The issue records the owner's authorization for reuse with attribution. The attribution wording is legal text.
- **Risk**: A reviewer may see similar behavior. Mitigation: the tests use synthetic records and the spec cites no copied text.
- **Human**: Yes. The attribution notice text needs human approval.

Warning: copying source code or assets into the product can breach the CC BY-NC-SA 4.0 license. Do not copy without a legal review.

### D-12 Sequencing around pull request #4208 and the owner's local change

- **Decision**: Do not edit `request_admission.py` or `deploy/.env.example` until the owner records the order for pull request #4208 and the local change. T002 and every task that depends on it wait. T001, T003, T004, and T011 may proceed.
- **Alternatives**: (a) Edit now and rebase later. (b) Close pull request #4208.
- **Reason**: The head of pull request #4208 changes the same admission module (R-51) and the same environment example (gh metadata). The local change adds an organization scope that T002 needs (A-11).
- **Risk**: The work waits for the owner. Mitigation: the tasks that do not touch those files proceed.
- **Human**: No.

### D-13 Test strategy

- **Decision**: Use mocked responses and synthetic records only. Extend `test_mistapi_contract.py`, `test_services.py`, `test_worker.py`, `test_request_admission.py`, and `test_wan_dashboard_cache_only.py`. Add `test_port_insights.py`. Make no live call and use no production credential.
- **Alternatives**: (a) Add a live smoke test with a validation token. (b) Add a new browser test file.
- **Reason**: The owner states that the available account has validation scope only (issue comment). The five-item rule blocks a new child in `tests/e2e/web_portal/` (A-14, R-68). The existing contract file already pins the SDK method (R-29).
- **Risk**: Mocks can hide live shape differences (A-04). Mitigation: U-2 and an owner-approved live check after the merge.
- **Human**: No.

### D-14 Production enablement

- **Decision**: Keep the phase disabled until the owner records measured site, gateway, and port counts from an authorized production scope. The owner also approves the enablement cap.
- **Alternatives**: (a) Enable with a default cap now. (b) Remove the phase.
- **Reason**: Enablement changes the shared API budget for every token. The choice sets product priority and the budget.
- **Risk**: No per-port data appears after release. Mitigation: the port view shows `unavailable` with the reason.
- **Human**: Yes.

## Remote Verification

Each row is one remote check. The `Ref` column names the branch, the installed package, or the commit that the check reads. The `Result` column uses `present`, `absent`, `partial`, or `stale`. The `Line` column gives the line in the file. The count of rows is 90.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Per-port traffic read passes `port_id` to the gateway insight method | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 705 |
| R-02 | Per-port insight read passes `port_id` to the gateway insight method | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1096 |
| R-03 | Traffic route returns cached data only | `src/interfaces/portals/wan_dashboard/routes.py` | main | d58229ce8f0c15998785f88b3cbf5a7009e15f58 | present | 137 |
| R-04 | Insight route returns cached data only | `src/interfaces/portals/wan_dashboard/routes.py` | main | d58229ce8f0c15998785f88b3cbf5a7009e15f58 | present | 150 |
| R-05 | Routes call no live per-port read method | `src/interfaces/portals/wan_dashboard/routes.py` | main | d58229ce8f0c15998785f88b3cbf5a7009e15f58 | absent | 0 |
| R-06 | Refresh worker calls no live per-port read method | `src/interfaces/portals/wan_dashboard/services/worker.py` | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | absent | 0 |
| R-07 | Refresh worker calls the bulk snapshot method | `src/interfaces/portals/wan_dashboard/services/worker.py` | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | present | 363 |
| R-08 | Bulk snapshot reads the port dataset | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 517 |
| R-09 | Per-port traffic cache key helper exists | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1312 |
| R-10 | Detail helper returns unavailable without a cache entry | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1273 |
| R-11 | Runner clone disables SDK retries after HTTP 429 | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 143 |
| R-12 | Runner cooldown lasts 60 seconds | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 59 |
| R-13 | WAN port rows are rows with usage `wan` grouped by MAC | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 945 |
| R-14 | Overview template says RX and TX show 7-day totals | `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` | main | eb58f7e5618f51379d0451bf4b0de92e299bf344 | present | 59 |
| R-15 | Dashboard script requests the per-port traffic route | `src/interfaces/portals/wan_dashboard/static/dashboard.js` | main | c0930484b1d20f244e51b64f0076183357f804ec | present | 430 |
| R-16 | Dashboard script requests the per-port insight route | `src/interfaces/portals/wan_dashboard/static/dashboard.js` | main | c0930484b1d20f244e51b64f0076183357f804ec | present | 530 |
| R-17 | Web portal registers the WAN dashboard blueprint | `web_portal/app.py` | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 207 |
| R-18 | Worker reads the load-test approval key | `src/interfaces/portals/wan_dashboard/services/worker.py` | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | present | 38 |
| R-19 | Worker reads the refresh interval key | `src/interfaces/portals/wan_dashboard/services/worker.py` | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | present | 39 |
| R-20 | Shared ledger caps each rolling hour at 5000 requests | `src/interfaces/wan_performance/collection/request_admission.py` | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 24 |
| R-21 | Shared admission mode reads `WAN_SHARED_ADMISSION` | `src/interfaces/wan_performance/collection/request_admission.py` | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 48 |
| R-22 | Site-scoped requests fail without an organization | `src/interfaces/wan_performance/collection/request_admission.py` | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 108 |
| R-23 | Main defines no organization scope | `src/interfaces/wan_performance/collection/request_admission.py` | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | absent | 0 |
| R-24 | Session setup enables the shared adapter when the ledger is enabled | `src/foundation/support/refactors/initialize_mist_session.py` | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 72 |
| R-25 | Session setup connects the ledger without an organization | `src/foundation/support/refactors/initialize_mist_session.py` | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 74 |
| R-26 | Gateway insight request in `wan_performance` omits `port_id` | `src/interfaces/wan_performance/collection/snapshot_client.py` | main | eca7564b5210f211ff8e1464d6720c810086d429 | absent | 295 |
| R-27 | Gateway insight result sets `port_id` to None | `src/interfaces/wan_performance/collection/snapshot_client.py` | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 310 |
| R-28 | Peer insight builds a raw VPN peer path | `src/interfaces/wan_performance/collection/peer_insights.py` | main | 0433c69a95c75e866c0693baebe3ce772d60dc9b | present | 114 |
| R-29 | SDK contract test pins the gateway insight method | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` | main | 95f7a85deb2c632ad89a1b5f12d2d1235b00f407 | present | 28 |
| R-30 | SDK contract test pins mistapi 0.64 | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` | main | 95f7a85deb2c632ad89a1b5f12d2d1235b00f407 | present | 49 |
| R-31 | Service test mocks named rate arrays with timestamps | `tests/integration/web_portal/wan_dashboard/test_services.py` | main | d83ed6394e67721d110b8f51d6414462db68e479 | present | 769 |
| R-32 | `wan_performance` test mocks `rt` arrays | `tests/unit/wan_dashboard/wan_performance/collection/test_gateway_insights.py` | main | a43cc4479c74747687082b7af65229b1b62aa05c | present | 67 |
| R-33 | Cache-only browser test file exists | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` | main | a51f0f8495f8200352db7cbaf15c2a16eae0b853 | present | 118 |
| R-34 | Changelog naming rule for issue fragments is documented | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 452 |
| R-35 | Environment example has no WAN dashboard setting | `deploy/.env.example` | main | 7137364423308485be734a391798d85c6a37eaf4 | absent | 0 |
| R-36 | Operator guide has no WAN dashboard section | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R-37 | OpenAPI defines the gateway insight operation | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32714 |
| R-38 | OpenAPI operation defines the `port_id` query field | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32728 |
| R-39 | OpenAPI metric response schema defines `results` and `rt` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94086 |
| R-40 | OpenAPI example pairs interval 3600 with limit 168 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 47783 |
| R-41 | OpenAPI port search says counters are cumulative since reboot | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 22032 |
| R-42 | OpenAPI rate-limit text states 5000 calls per hour | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 62707 |
| R-43 | OpenAPI limit parameter defaults to 100 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59747 |
| R-44 | OpenAPI `rx_bps` schema defines bits per second | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 98919 |
| R-45 | SDK gateway insight method accepts `port_id` | `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py` | installed 0.64.1 | sha1 3501c61095809aa4fa332b6ac1d306b5bce44ca7 | present | 295 |
| R-46 | SDK gateway insight method documents default limit 100 | `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py` | installed 0.64.1 | sha1 3501c61095809aa4fa332b6ac1d306b5bce44ca7 | present | 330 |
| R-47 | Installed SDK version is 0.64.1 | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` | installed 0.64.1 | none | present | 0 |
| R-48 | SDK port search has no duration parameter | `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py` | installed 0.64.1 | sha1 89f6ea80d35e3e430b2552998695aad44e1d0ad9 | absent | 1157 |
| R-49 | SDK retries HTTP 429 three times by default | `.venv\Lib\site-packages\mistapi\__api_request.py` | installed 0.64.1 | sha1 056ad4ebb57f500d6d97cedb09d674042b620663 | present | 59 |
| R-50 | SDK has no per-device `vpn_peer-metrics` method | `.venv\Lib\site-packages\mistapi` | installed 0.64.1 | none | absent | 0 |
| R-51 | PR 4208 head defines `RequestLedger` in the admission module | `src/interfaces/wan_performance/collection/request_admission.py` | PR 4208 head branch | 4cf92ab977bb667ef0fe4e72de68994a80f1ffea | present | 132 |
| R-52 | PR 4208 head removes the legacy wan_dashboard snapshot test | `tests/unit/wan_dashboard/wan_performance/collection/test_snapshot_client.py` | PR 4208 head branch | none | absent | 0 |
| R-53 | PR 4208 head changes the gateway snapshot client | `src/interfaces/wan_performance/collection/snapshot_client.py` | PR 4208 head branch | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 0 |
| R-54 | Source loop requests insights for each gateway port | `worker.py` in MistCircuitStats-Redis | main | 1dcce642d9e21dc632c7b98d7a57db957f54eb13 | present | 630 |
| R-55 | Source computes byte totals from named rate arrays and the interval | `worker.py` in MistCircuitStats-Redis | main | 1dcce642d9e21dc632c7b98d7a57db957f54eb13 | present | 592 |
| R-56 | Source insight request sends no limit or page | `worker.py` in MistCircuitStats-Redis | main | 1dcce642d9e21dc632c7b98d7a57db957f54eb13 | absent | 637 |
| R-57 | Source insight request uses a direct HTTP client | `worker.py` in MistCircuitStats-Redis | main | 1dcce642d9e21dc632c7b98d7a57db957f54eb13 | present | 645 |
| R-58 | Source license is CC BY-NC-SA 4.0 | `LICENSE` in MistCircuitStats-Redis | main | 38bc1cae211b4f6bff4cfa462f64cd7033b1a017 | present | 1 |
| R-59 | Source research commit is 61153fcb8dc51c6c7ff41a46179ef376d9da7601 | commit in MistCircuitStats-Redis | main | 61153fcb8dc51c6c7ff41a46179ef376d9da7601 | present | 0 |
| R-60 | No record folder for 4330 or 4634 and no route folder exists on main | `specs/` | main | none | absent | 0 |
| R-61 | Source replaces a missing sample with zero | `worker.py` in MistCircuitStats-Redis | main | 1dcce642d9e21dc632c7b98d7a57db957f54eb13 | present | 1083 |
| R-62 | Worker refresh method starts at line 502 | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 502 |
| R-63 | SDK org-level VPN peer count path exists | `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py` | installed 0.64.1 | sha1 89f6ea80d35e3e430b2552998695aad44e1d0ad9 | present | 1576 |
| R-64 | Last complete value write uses the stale time to live | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1240 |
| R-65 | Stale time to live constant is 86400 seconds | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 442 |
| R-66 | Local gates table exists in the instruction file | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-67 | Browser UI rule requires stable `data-testid` values | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 306 |
| R-68 | Constitution five-item rule exists | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-69 | Constitution forbids direct HTTP when a working mistapi method exists | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 281 |
| R-70 | Constitution output backend rule exists | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 312 |
| R-71 | AGENTS specification rule exists | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| R-72 | AGENTS STE gate covers each Markdown file | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| R-73 | Worker refresh method returns at line 557 | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 557 |
| R-74 | Shared normalizer holds the traffic sample method | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 297 |
| R-75 | Shared request method exists in the service | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 841 |
| R-76 | Per-port insight cache key helper exists | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1316 |
| R-77 | Source reads named rate arrays | `worker.py` in MistCircuitStats-Redis | main | 1dcce642d9e21dc632c7b98d7a57db957f54eb13 | present | 589 |
| R-78 | Worker status record write method exists | `src/interfaces/portals/wan_dashboard/services/worker.py` | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | present | 160 |
| R-79 | Constitution sets 25 lines as the function limit | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 85 |
| R-80 | Browser test folder holds 32 direct children | `tests/e2e/web_portal` | main | none | present | 0 |
| R-81 | Changelog folder holds 335 direct children | `changelog.d` | main | none | present | 0 |
| R-82 | Bulk snapshot reads the gateway dataset | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 511 |
| R-83 | Traffic range map holds 1h, 6h, 24h, and 7d | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 165 |
| R-84 | Insight range map holds 1h, 6h, 24h, 3d, and 7d | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 166 |
| R-85 | SDK adds the `port_id` query field only when a value is set | `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py` | installed 0.64.1 | sha1 3501c61095809aa4fa332b6ac1d306b5bce44ca7 | present | 345 |
| R-86 | Traffic cached read expects a list | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 595 |
| R-87 | Insight cached read expects an object | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 600 |
| R-88 | Result envelope holds status, data, notice, and stale | `src/interfaces/portals/wan_dashboard/services/__init__.py` | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1332 |
| R-89 | Refresh button keeps identifier `wan-refresh` | `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` | main | eb58f7e5618f51379d0451bf4b0de92e299bf344 | present | 17 |
| R-90 | Refresh status panel keeps identifier `wan-refresh-panel` | `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` | main | eb58f7e5618f51379d0451bf4b0de92e299bf344 | present | 28 |

## Sources

- Issue #4330 body and comments (`gh issue view 4330`). The comments are IC_kwDOQltU8c8AAAABkIhj7A (2026-11-08T09:29:31Z) and IC_kwDOQltU8c8AAAABkNSiDQ (2026-11-08T17:41:01Z).
- Pull request #4208 metadata (`gh pr view 4208`). The pull request is an open draft. Its head branch is `jmorrison-juniper-4200-migrate-mistwanperformance`. Its file list holds 82 entries, and it adds seven lines to `deploy/.env.example`. Its check rollup holds 52 entries: 42 success and 10 skipped. Its body does not name issue 4330.
- The search for issue 4330 returned pull requests #4364 and #4332. Both merged on 2026-10-20. The issue text and its comments do not link them.
- Pull request #4252 (merged 2026-10-16), pull request #4332 (merged 2026-10-20, "add cache-only stale dashboard reads"), and pull request #4364 (merged 2026-10-20). These are gh metadata.
- Issue #4220 (closed 2026-10-20), issue #4200 (open), and issue #4224 (open, Mist Cisco config converter). These are gh metadata.
- Spec drafts. The 4224 record is absent. The 4634 summary is in `_meta/4634-summary.md`, and it provides evidence style only.
- Local `git status` (five modified files) and `git hash-object` for the admission file. The local tree is not `main`, so these outputs prove nothing about committed code.
- Installed mistapi 0.64.1 under `.venv\Lib\site-packages\mistapi`, read with read-only views and `Get-FileHash` (SHA-1).
- MistCircuitStats-Redis at `main` commit 61153fcb8dc51c6c7ff41a46179ef376d9da7601 (2026-10-06). The LICENSE blob and the worker blob are cited in the table.
- No skill was loaded. The work involves no Podman runtime behavior and no Juniper device behavior.
- No `web_fetch` call was made. The local OpenAPI file answers each Mist API question.

## Unverified

- U-1: Production site, gateway, and port counts. Cause: the owner states that no authorized production scope exists (comment of 2026-11-08T17:41:01Z).
- U-2: Live key names for the metric arrays. The OpenAPI file names `results` and `rt`, and the code names `timestamps` and named arrays (R-39, R-31). Cause: a live call is outside this task.
- U-3: Live acceptance of `limit` 168 for the insight endpoint. Cause: a live call is outside this task. The SDK default is 100 (R-46).
- U-4: The number of tokens in production. Cause: no authorized production scope exists.
- U-5: Whether production totals match totals derived from hourly samples. Cause: no production data is available. The bulk counters measure a different period (R-41).
- U-6: The final form of pull request #4208. Cause: the pull request is an open draft.
- U-7: Whether the owner's local change to `request_admission.py` lands. Cause: the change exists only in the local working tree.
- U-8: The upstream Mist documentation on juniper.net. Cause: no fetch was made. The local OpenAPI file states the same 5000-call figure (R-42).
- U-9: The runtime effect of shared admission on existing site-scoped features. Cause: the code path is verified (R-22, R-24, R-25), but no runtime test was run.
- U-10: The portal CSV export path and the use of `DataExporter`. Cause: a local search found no caller of the live per-port methods and no `DataExporter` call in the export path. No remote check exists for this claim.
