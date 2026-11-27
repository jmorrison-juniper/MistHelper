# Research: Offline Dynamic JVD Labs Preview

This record lists each decision with its alternatives and reason. It also lists each remote check and each local read. Remote checks use the GitHub API against the default branch.

## Evidence Rules

- The main commit read for this record is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (R-01).
- Ref `main` means the default branch.
- A blob SHA of `none` means the path is absent on main.
- A blob SHA of `not applicable` means the check reads a commit, a ref, a comment, or a pull request.
- Local evidence does not prove that GitHub holds an object. Only a remote check proves that.
- A line number comes from the decoded remote file body. Each line was read in this session.

## Decisions

### D-1 Record route and slug

- Decision: Use the record folder `specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview`.
- Alternatives: Use the slug `offline-dynamic-jvd-labs-preview`. Use a timestamp record under `specs/live/`.
- Reason: The numeric route is the base-5 form of 4631 (R-54, R-55). Record 4822 already plans this path (L-10).
- Risk: The slug omits the word "dynamic". The title still names it.
- Human decision: No.

### D-2 Source package location

- Decision: Place the new package at `src/interfaces/labs/`.
- Alternatives: Place it at `src/interfaces/portals/labs/`. Place it at `web_portal/labs/`.
- Reason: `src/interfaces/portals` holds six children (R-23). `web_portal` holds seven children (R-20). `src/interfaces` holds four children (R-22), so one new child fits.
- Risk: The package sits beside the portal folders, not inside them.
- Human decision: No.

### D-3 Test location

- Decision: Place all Labs tests under `tests/integration/web_portal/labs/`. The browser module stays in the same folder.
- Alternatives: Place tests under `tests/e2e/labs/`. Place tests under `tests/unit/web_portal/labs/`. Place tests under `tests/e2e/web_portal/`.
- Reason: `tests/e2e` holds five children (R-29), and guard R-57 forbids more. `tests/unit/web_portal` holds 52 children (R-33). `tests/e2e/web_portal` holds 32 children (R-30). `tests/integration/web_portal` holds four children (R-25). Record 4648 D-4 chooses the same feature-folder pattern (L-11).
- Risk: The browser module does not run in CI (D-19).
- Human decision: No.

### D-4 Shared-file gate

- Decision: Make no edit to `web_portal/app.py` or `web_portal/templates/base.html` before the shared-file handover. T013 and T014 wait.
- Alternatives: Edit now and rebase after PR 4208 merges. Add a separate module that the portal imports, which still edits `app.py`. Wait until PR 4208 closes.
- Reason: PR 4208 is open and draft, and it owns both files (R-11). AGENTS requires a handover when files overlap (R-52). Issue #4633 records the coordinator decision for this handover rule, as record 4648 cites (L-11). Record 4648 D-3 uses the same gate (L-11).
- Risk: The Labs page stays unreachable until the handover.

Caution: An early edit to a shared file causes a merge conflict in PR 4208.

- Human decision: No.

### D-5 Test composition

- Decision: Build the test app with the real `WebPortalApp.create_app`. Register the Labs blueprint only when the factory does not register it. Inject planners through `app.config`.
- Alternatives: Build a small Flask app with its own CSRF setup. Reuse the session fixtures of `tests/e2e/conftest.py`.
- Reason: The real factory keeps the shared CSRF answer (R-15, R-16). The e2e fixture shows the factory call (R-31, lines 273 to 277). Fixtures in `tests/e2e/conftest.py` do not reach `tests/integration`. Record 4648 D-2 uses the same composition pattern (L-11).
- Risk: The factory starts background work. The harness must call `WebPortalApp.shutdown_app` at teardown (R-31, lines 280 to 283).
- Human decision: No.

### D-6 Route set

- Decision: Use three routes under `/labs`: `GET /labs/`, `GET /labs/capability`, and `POST /labs/plan`.
- Alternatives: Use an `/api/labs` prefix. Use one POST route for the page and the plan.
- Reason: The shared CSRF answer uses JSON for `/api/` paths (L-12). A form needs an HTML answer. Separate read and write routes keep each GET free of side effects. FR-019 limits the set.
- Risk: The route names become public. Low risk.
- Human decision: No.

### D-7 Blueprint precondition

- Decision: Registration checks `"csrf" in app.extensions` and fails at startup when the check fails.
- Alternatives: Skip the check. Check at request time only.
- Reason: `CSRFProtect.init_app` sets `app.extensions["csrf"]` (L-2). A startup failure is safer than a form without protection. Record 4648 uses the same check (L-12).
- Risk: The registration fails if the factory changes its CSRF setup. The failure is intended.
- Human decision: No.

### D-8 CSRF protection

- Decision: Reuse the shared `CSRFProtect` and the shared answer. Add no Labs CSRF handler.
- Alternatives: Add a Labs-specific handler. Use a custom token and field name.
- Reason: The global `before_request` hook protects each POST (L-3). The shared protection is configured in `_configure_csrf` (R-15). The shared answer is registered in `_register_csrf_error_handler` (R-16). Record 4648 D-6 keeps the shared handler (L-11).
- Risk: The answer shape follows the shared rule. Low risk.
- Human decision: No.

### D-9 Form contract

- Decision: Accept the fields `run_name` and `csrf_token` only. Reject any other field with HTTP 400. Reject a repeated `run_name` with HTTP 400.
- Alternatives: Ignore extra fields. Accept extra fields and log them. Accept a list of run names.
- Reason: The issue requires rejection of extra fields (comment 6962287494). A repeated field can hide a second value.
- Risk: A new field needs a spec change. The change is intended.
- Human decision: No.

### D-10 Run-name rule

- Decision: Accept only names that match `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`. Check the pattern with `re.fullmatch`.
- Alternatives: Accept free text. Accept Unicode letters. Allow 32 characters.
- Reason: The issue requires one valid run name and defines none (assumption). ASCII keeps logs and display simple (R-46). A 64-character limit keeps the value short for display.
- Risk: A valid operator name with a space fails.

Caution: A wider rule needs new tests and a spec change.

- Human decision: No.

### D-11 Server example

- Decision: Define one synthetic example as a constant in `planner.py`. The client cannot select an example. The default run name comes from the example.
- Alternatives: Let the client choose an example from a list. Accept an example query parameter.
- Reason: The issue requires a server-selected example (comment 6962287494). D-9 blocks extra fields, so the client cannot send an example.
- Risk: One example limits coverage. The preview accepts that limit.
- Human decision: No.

### D-12 Plan result allow-list

- Decision: Accept exactly the keys `logical_devices` and `links`. Show only the device fields `id` and `label` and the link fields `a_end` and `z_end`.
- Alternatives: Render the whole planner output. Reject known authority keys only.
- Reason: An allow-list fails closed. The issue limits the page to logical devices, links, and a fingerprint (comment 6962287494).
- Risk: A new planner field needs a spec change.
- Human decision: No.

### D-13 Intent fingerprint

- Decision: The fingerprint is `sha256:` followed by the SHA-256 hex digest of canonical JSON. The JSON holds the devices sorted by `id` and the links sorted by `a_end` and `z_end`. The JSON uses sorted keys, compact separators, and ASCII.
- Alternatives: Use SHA-1. Use an HMAC with a key. Show no fingerprint.
- Reason: The Python standard library provides SHA-256. An HMAC key would need credential handling, which is outside this preview (W-1, U-13).
- Risk: The digest depends on content only. Low risk.
- Human decision: No.

### D-14 Unavailable state status

- Decision: The unavailable state returns HTTP 200. The page shows `data-testid="labs-unavailable"` and a reason code. Errors also reach the logs.
- Alternatives: Return HTTP 503. Return HTTP 500.
- Reason: The page stays usable. The state is an expected result, not a server fault. FR-022 keeps the logs useful.

Caution: Monitoring that reads only status codes misses this state. Monitoring must read the page text or the logs.

- Human decision: No.

### D-15 Planner adapter

- Decision: Import `vmm_topology` inside the gateway method, not at package load. Call one function named `plan` with the keyword arguments `run_name` and `example`. A test sets the planner through `app.config["LABS_PLANNER_GATEWAY"]`.
- Alternatives: Import at module load. Vendor the framework. Discover the framework through an entry point.
- Reason: The portal must start without the private framework (FR-017). Vendoring the framework changes its licensing position (D-16). The planner API is unknown to this record (U-1).
- Risk: The call name may differ. The gateway then reports `failed`. The owner must confirm the API.
- Human decision: No.

### D-16 Private framework licensing and delivery

- Decision: HUMAN-DECISION-REQUIRED. Keep the private framework outside the public change. A developer loads it only on a local machine. Do not publish its adapter fixtures or archives.
- Alternatives: (a) Publish the adapter and its fixtures in the public repository. (b) Vendor the framework under `src/`. (c) Keep the framework private and load it only on a local machine.
- Reason: Comment 6703043366 states that no authorized public delivery method exists. A licensing decision needs a human answer.
- Risk: Public CI never runs the available planner path. The stub tests check the gateway contract only.
- Human decision: Yes. Category: licensing or legal text. Recommended option: (c). The owner must confirm that local use is allowed and that no public copy exists.

### D-17 Shared-file handover order

- Decision: HUMAN-DECISION-REQUIRED. Decide the product priority of the shared-file handover. Decide whether the Labs registration joins one combined handover with the Cisco converter registration.
- Alternatives: (a) One combined handover after PR 4208 closes or hands over. (b) Separate handovers, Labs first. (c) Separate handovers, converter first.
- Reason: Both features change the same two shared files. The record 4645 plan names the handover owner (L-14). The owner sets the order.
- Risk: The Labs page waits for the converter work under option (a).

Caution: A late handover delays both pages.

- Recommended option: (a). One change to two shared files creates one merge surface.
- Human decision: Yes. Category: product priority.

### D-18 Logging convention

- Decision: Use stdlib `logging` with `%s` templates and key=value text. Log reason codes, counts, and the fingerprint. Never log a raw run name or a raw form value. Keep log output ASCII.
- Alternatives: Use structlog. Use a JSON formatter.
- Reason: `web_portal` logs with the stdlib logger (R-17). Record 4636 asks the owner to confirm this convention (L-13). structlog is pinned (R-71), but this record does not adopt it without an owner answer.
- Risk: The constitution asks for structlog or an equivalent (R-46). The owner check U-8 stays open.
- Human decision: No.

### D-19 Browser journey

- Decision: Run the browser module on a developer machine after Chromium installs. Each browser test skips with a stated cause when Chromium is absent. Save each failure screenshot to `test-artifacts/labs-preview/`.
- Alternatives: Add a CI browser shard. Place the module under `tests/e2e/`.
- Reason: The E2E shards run the `tests/e2e` paths of the upgrade portal, the web portal, and the websockets tab (`ci.yml` lines 794 to 798). R-35 cites the web-portal shard. `tests/e2e` cannot take a new child (R-29, R-57). CI installs Chromium in the E2E job (R-36). Record 4648 D-11 stores browser evidence under `test-artifacts/` (L-11).

Caution: CI does not run the browser module. A UI regression can reach `main` without a browser check. RA-1 tracks the gap.

- Human decision: No.

### D-20 Labels and merge gating

- Decision: Add `in-progress` before the branch. Keep `feature`, `web-portal`, and `needs-human-review`. Add `auto-merge` only after a human clears review and the orchestrator authorizes the merge.
- Alternatives: Remove `needs-human-review` after CI passes. Add `auto-merge` as soon as CI starts.
- Reason: The issue carries `needs-human-review` for a safety path. The constitution requires a status label while work is in progress (R-48). The constitution adds `auto-merge` only after each check passes (R-50).
- Risk: Merges wait for a human. Accepted.
- Human decision: No.

### D-21 Documentation and changelog

- Decision: Add the changelog fragment `changelog.d/issue-4631-offline-jvd-preview.md` now. Add the operator guide row after registration. Leave `README.md` unchanged.
- Alternatives: Edit `CHANGELOG.md`. Add a row to `README.md`.
- Reason: The fragment rule names the issue form (R-62). The guard `test_changelog_fragment_policy.py` checks each fragment name (R-59). The operator guide holds the portal table (R-75). `README.md` points portal details to the operator guide (R-80). One fact has one home.
- Risk: The fragment name changes after the pull request exists. The change renames it to `pr-<number>.md`.
- Human decision: No.

### D-22 No Mist call, container, or dependency change

- Decision: The feature makes no Mist API call, starts no container, and changes no dependency.
- Alternatives: Use mistapi for a read-only status. Start a test container for the browser journey.
- Reason: Comment 6962287494 keeps provider access disabled. The Mist coverage files list no Labs entry (R-78, R-79). The compose naming rules apply only when a container starts (R-43).
- Risk: None known.
- Human decision: No.

### D-23 Implementation starts from main

- Decision: Create the branch from `main`. Write new files. Do not cherry-pick, rebase, or push the recovered branch.
- Alternatives: Rebase the recovered branch onto `main`. Push the recovered branch as a draft.
- Reason: The recovered branch has no GitHub copy (R-07 to R-10). Publication needs a secret review (record 4822 D-2, L-10). The constitution forbids branching from another feature branch (R-49).
- Risk: The recovered work must be rebuilt from the tests. The tests define the behavior.

Warning: Publishing private fixtures creates a copy that cannot be recalled.

- Human decision: No.

### D-24 Size and status

- Decision: Set the size to `L`. Set the status to `complete`. Implementation waits for D-4, D-16, and D-17.
- Alternatives: Set the size to `M`. Set the status to `blocked`.
- Reason: The change touches 12 new or edited files in two areas. A size `M` misstates the handover work. Record 4648 uses the same status rule for a record whose implementation waits (L-11).
- Risk: None known.
- Human decision: No.

## Remote Verification

Each row is one remote check. The table and `STATUS.json` hold the same 82 rows.

| ID | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Main head is commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | refs/heads/main | main | not applicable | present | 0 |
| R-02 | Issue 4631 comment 6703043366 exists, dated 2026-11-07 | issues/comments/6703043366 | main | not applicable | present | 0 |
| R-03 | Issue 4631 comment 6961775907 exists, dated 2026-11-17 | issues/comments/6961775907 | main | not applicable | present | 0 |
| R-04 | Issue 4631 comment 6962287494 exists, dated 2026-11-17 | issues/comments/6962287494 | main | not applicable | present | 0 |
| R-05 | Commit a9a2d36dfc7555f0107ec7162d04c6348229c056 is absent | commits/a9a2d36dfc7555f0107ec7162d04c6348229c056 | main | not applicable | absent | 0 |
| R-06 | Commit 01e0a701608dc82e09403186d2f2eb285fc29f91 is absent | commits/01e0a701608dc82e09403186d2f2eb285fc29f91 | main | not applicable | absent | 0 |
| R-07 | Branch feat/4631-recovered-offline-preview is absent | refs/heads/feat/4631-recovered-offline-preview | main | none | absent | 0 |
| R-08 | Tag recovery/4822/labs-original is absent | refs/tags/recovery/4822/labs-original | main | none | absent | 0 |
| R-09 | Tag recovery/4822/labs-preview is absent | refs/tags/recovery/4822/labs-preview | main | none | absent | 0 |
| R-10 | Branch docs/4822-recovered-vmm-export is absent | refs/heads/docs/4822-recovered-vmm-export | main | none | absent | 0 |
| R-11 | Pull request 4208 is open and draft, and it owns the two shared files | pulls/4208 | main | not applicable | present | 0 |
| R-12 | `web_portal/app.py` calls `_apply_security` at line 52 | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 52 |
| R-13 | `web_portal/app.py` defines `_register_blueprints` at line 182 | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 182 |
| R-14 | `web_portal/app.py` registers no Labs or converter blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| R-15 | `web_portal/services/config.py` defines `_configure_csrf` at line 297 | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 297 |
| R-16 | `web_portal/services/config.py` answers CSRF failures with `csrf_expired` at line 324 | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 324 |
| R-17 | `web_portal/services/config.py` logs the CSRF answer with a stdlib logger at line 327 | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 327 |
| R-18 | `web_portal/templates/base.html` has the `nav-websockets` anchor at line 74 | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 74 |
| R-19 | `web_portal/templates/base.html` has no Labs navigation anchor | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| R-20 | `web_portal` holds seven children | web_portal | main | 1d1a9efa3f808aed5698f655385f4294e7accf06 | present | 0 |
| R-21 | `src/interfaces/labs` does not exist | src/interfaces/labs | main | none | absent | 0 |
| R-22 | `src/interfaces` holds four children | src/interfaces | main | c03966ecf6f2d8e2b87c21671ec45f2fd7afeaa7 | present | 0 |
| R-23 | `src/interfaces/portals` holds six children | src/interfaces/portals | main | 7f5ac6778b6a7a78ad7268542bb8de2a9c550926 | present | 0 |
| R-24 | `src/interfaces/portals/cisco_config_converter` exists | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R-25 | `tests/integration/web_portal` holds four children | tests/integration/web_portal | main | 1ae7142b9720687639abc3e3fc3212351f01304a | present | 0 |
| R-26 | `tests/integration/web_portal/labs` does not exist | tests/integration/web_portal/labs | main | none | absent | 0 |
| R-27 | `tests/integration` holds 26 children | tests/integration | main | e5b3e9f9d45a2b2694d923b6dbb484f1c530c818 | present | 0 |
| R-28 | `tests/integration/conftest.py` names the credentialed fixtures at line 46 | tests/integration/conftest.py | main | d2055ec1b483548a1b9220fbfb5ee9697f3dd000 | present | 46 |
| R-29 | `tests/e2e` holds five children | tests/e2e | main | 828f24a6106147d9263b550da13acfaa4866b3bf | present | 0 |
| R-30 | `tests/e2e/web_portal` holds 32 children | tests/e2e/web_portal | main | 3d492d6e0bec7e4a76925d345c095dfa44bb813e | present | 0 |
| R-31 | `tests/e2e/conftest.py` defines the `flask_app` fixture at line 260 | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 260 |
| R-32 | `tests/unit` holds 50 children | tests/unit | main | fc987db029020f6dae58078bf377825336567be6 | present | 0 |
| R-33 | `tests/unit/web_portal` holds 52 children | tests/unit/web_portal | main | 091139596e93c865ebf1f7f93cd5b7feba2ba772 | present | 0 |
| R-34 | The CI root-and-contracts shard runs `tests/integration` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| R-35 | The CI web-portal E2E shard runs `tests/e2e/web_portal` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 796 |
| R-36 | The CI E2E job installs Chromium | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 887 |
| R-37 | The CI `MYPY_PATHS` value includes `src/` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-38 | The CI `VULTURE_PATHS` value includes `src/` and `web_portal` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-39 | The CI `PYDOCSTYLE_PATHS` value includes `src/` and `web_portal` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-40 | The CI `INTERROGATE_PATHS` value includes `src/` and `web_portal` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-41 | The copilot instructions hold the Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-42 | The copilot instructions hold the Web UI tests rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 301 |
| R-43 | The copilot instructions hold the containers and ports rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 354 |
| R-44 | The copilot instructions hold the pull request title rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| R-45 | The constitution holds the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-46 | The constitution asks for structlog or an equivalent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 193 |
| R-47 | The constitution holds the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R-48 | The constitution holds the Required Labels rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 487 |
| R-49 | The constitution holds the Branch Naming rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 476 |
| R-50 | The constitution holds the PR Checklist rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 516 |
| R-51 | AGENTS.md holds the Writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-52 | AGENTS.md holds the Parallel agents section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 242 |
| R-53 | AGENTS.md holds the Specifications section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| R-54 | `spec-route.ps1` sets the numbered base to 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-55 | `spec-route.ps1` defines `Resolve-SpecFeaturePath` | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R-56 | The nested package guard sets the child limit to five | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R-57 | The E2E package guard enforces the five-item limit | tests/guardrails/test_e2e_package_structure.py | main | c5be7ed0b21eec56c7d586b7025cf28f0fc4fb42 | present | 18 |
| R-58 | The source domain guard lists four domains | tests/guardrails/test_src_domain_structure.py | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | present | 11 |
| R-59 | The changelog guard defines the issue fragment name | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| R-60 | The spec route guard file exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| R-61 | The nested package baseline file exists | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 0 |
| R-62 | The changelog README defines the issue fragment name | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R-63 | The changelog holds the 4504 fragment | changelog.d/issue-4504-dynamic-jvd-labs-planning.md | main | 25433e30a679a0365d33c554684f1b7300dafbd0 | present | 0 |
| R-64 | The 4504 planning spec exists | specs/numbered/0/0/1/2/1/0/0/4/4504-dynamic-jvd-labs-planning/spec.md | main | 37b2966c2ddd5aec52b77d84d3eb7ca9baece3dc | present | 0 |
| R-65 | The 4631 record folder is absent | specs/numbered/0/0/1/2/2/0/1/1 | main | none | absent | 0 |
| R-66 | The route parent `specs/numbered/0/0/1/2/2/0` is absent | specs/numbered/0/0/1/2/2/0 | main | none | absent | 0 |
| R-67 | The route grandparent `specs/numbered/0/0/1/2/2` holds three children | specs/numbered/0/0/1/2/2 | main | 69448521ad293f85e5b4fb0703815880f0bcd1a8 | present | 0 |
| R-68 | The reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-69 | `pyproject.toml` requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-70 | `requirements.txt` pins Flask-WTF 1.3.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 54 |
| R-71 | `requirements.txt` pins structlog 26.1.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 249 |
| R-72 | `requirements-dev.txt` pins Playwright 1.65.2 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 272 |
| R-73 | `requirements-dev.txt` pins pytest-playwright 0.10.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 333 |
| R-74 | `compose.yml` publishes port 8055 | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 86 |
| R-75 | The operator guide holds the Open a portal section | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 211 |
| R-76 | The quality gates guide holds the writing gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| R-77 | The development setup guide downloads Chromium | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 265 |
| R-78 | The Mist GET coverage file holds no Labs entry | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | absent | 0 |
| R-79 | The Mist MISSING coverage file holds no Labs entry | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | absent | 0 |
| R-80 | The README refers portal details to the operator guide | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 113 |
| R-81 | The STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R-82 | The pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |

## Local Reads

These reads support the design. They do not prove that GitHub holds a file.

| ID | Local path | Lines or name | Use |
| - | - | - | - |
| L-1 | `.venv\Lib\site-packages\flask_wtf\csrf.py` | Line 47 | The default CSRF field name is `csrf_token`. |
| L-2 | `.venv\Lib\site-packages\flask_wtf\csrf.py` | Line 212 | `init_app` sets `app.extensions["csrf"]`. |
| L-3 | `.venv\Lib\site-packages\flask_wtf\csrf.py` | Line 231 | A `before_request` hook protects each POST. |
| L-4 | `.venv\Lib\site-packages\flask_wtf\csrf.py` | Line 225 | The Jinja global `csrf_token` is set. |
| L-5 | `.venv\Lib\site-packages\flask_wtf\csrf.py` | Line 346 | `CSRFError` subclasses `BadRequest`, which returns HTTP 400. |
| L-6 | `.venv\Lib\site-packages\flask\sansio\app.py` | Line 536 | `select_jinja_autoescape` decides autoescape for each template. |
| L-7 | `.venv\Lib\site-packages` | Name search | No `vmm_topology` entry exists. |
| L-8 | `.venv\Lib\site-packages` | Name search | `mistapi` and `flask_wtf-1.3.0.dist-info` exist. This record uses neither for code. |
| L-9 | `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md` | Line counts 265, 473, and 462 | The local copies are shorter than the remote copies. Remote lines are cited. |
| L-10 | `spec-drafts\_meta\4822-STATUS.json` | Remote checks for issue 4631 | Record 4822 plans the path `specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/`. It reports no Labs source package. |
| L-11 | `spec-drafts\4648\design\research.md` | Decisions D-2 (line 20), D-3 (line 27), D-4 (line 34), D-6 (line 48), D-8 (line 62), D-11 (line 83), D-15 (line 111) | Shared-file gate, browser folder, CSRF answer, browser evidence, and size rule. |
| L-12 | `spec-drafts\4648\design\contracts\csrf-negotiation.md` and `portal-registration.md` | Whole files | The shared answer rule, the registration order, and the precondition checks. |
| L-13 | `spec-drafts\4636\analysis.md` and `spec-drafts\4636\design\research.md` | `analysis.md` lines 49 and 50. `research.md` line 383. | The folder debt remediation and the owner check on stdlib logs. |
| L-14 | `spec-drafts\4645\plan.md` and `spec-drafts\4646\analysis.md` | `4645/plan.md` line 131. `4646/analysis.md` lines 127 and 128. | The handover owner and the folder debt remediation. |
| L-15 | `spec-drafts\4640\spec.md` | Parent line | The parent issue #4224 names the Cisco config converter. |
| L-16 | `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` | Headings of the spec, plan, research, analysis, and tasks files | The record shape. Content is not copied. |
| L-17 | `.specify\templates\*.md` | Headings of the spec, plan, tasks, and checklist templates | The section headings used in this record. |

### Reading Scope

- The issue names no file or test. Its comments name PR 4208, issue 4504, and the recovered refs. Each named item has a remote check (R-01 to R-11, R-63, R-64).
- `documentation/quality-gates.md` and `documentation/development-setup.md` were searched for the writing gate and Chromium lines (R-76, R-77).
- `documentation/architecture.md` was searched for portal terms only (lines 44, 242, and 272).
- `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md` were searched for Labs terms only (R-78, R-79).
- `documentation/container-deployment.md` was not read. The feature starts no container (D-22).
- `documentation/mist-api-openapi31yaml.yaml` and the `mistapi` source were not read. The feature makes no Mist call (D-22, FR-020).

## Web Sources

| ID | URL | Read | Use |
| - | - | - | - |
| W-1 | https://docs.python.org/3/builtins/exceptions.html | The first 8,000 characters | The exception base classes. The `ImportError` section was not read (U-13). |

## Skills

No local skill was loaded. The feature has no container work and no device behavior. The Podman and Juniper skills do not apply.

## Unverified

- U-1: The `vmm_topology` API is unknown. Issue #4504 names the framework, and the local `.venv` lacks it (L-7). The `plan` call and its keyword arguments come from D-15 only.
- U-2: The recovered branch content and the owner test result of 36 passes and one skip are not verified. GitHub holds no copy (R-05 to R-10). The result came from comment 6961775907.
- U-3: The private fixtures and the private archives were not read. The owner states they are not published (comment 6962287494).
- U-4: The owner states that the source worktree is unchanged. This record did not check it.
- U-5: Chromium availability on a developer machine is not verified. The bootstrap guide states it (R-77).
- U-6: The shared-file handover is not granted. The status comes from record 4648 (L-11).
- U-7: The outcome of PR 4208 is an owner decision. This record does not predict it.
- U-8: The owner must confirm the stdlib logging convention against the structlog rule (L-13, R-46).
- U-9: The root-and-contracts job steps after line 310 of `ci.yml` were not read. The Chromium state of that job is not verified.
- U-10: No search covered every route rule of the portal for `/labs`. T-LOCAL-GATES checks the route map.
- U-11: `WebPortalApp.create_app` and `WebPortalApp.shutdown_app` were read only through the e2e fixture (R-31). They were not run.
- U-12: `web_portal.menu_registry.build_static_menu_actions` is imported by the e2e fixture (R-31, lines 269 and 270). The module was not read.
- U-13: The Python `ImportError` section was not read (W-1). The claim that `ModuleNotFoundError` subclasses `ImportError` is not verified in this session.
