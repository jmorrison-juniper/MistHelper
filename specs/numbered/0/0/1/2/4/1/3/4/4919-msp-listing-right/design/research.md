# Research: MSP organization list skipped without the listing right

## Scope of This Research

- **Issue facts**: Issue #4919 is open. Its labels are `chore`, `MistHelper.py`, and `priority:P3`. The author is `jmorrison-juniper`. The body states that the report calls `msps/<msp_id>/orgs` for each MSP grant. It also states that an account can hold an MSP grant and still lack the right to list it. The issue states that the call returns HTTP 403 on every run. The issue status marks the work as a future item that is not scheduled. It has no comments and no reproduction steps. The issue links #4713.
- **Linked pull requests**: `gh pr list --search 4919` returned no pull request.
- **Legacy record**: No folder under the local `specs\` tree starts with `4919-`. No path on remote `main` contains `4919` (remote row R51). The field `existing_record.found` is false.
- **Related issue #4713**: Open. The body names `src/foundation/support/refactors/msp_privilege_detection.py` and states ownership holds for the detector and the inventory orchestrator. This change keeps both files unchanged.
- **Open pull requests**: Seven open pull requests were checked with `gh pr list --json number,title,headRefName,files`. None changes a file that matches `subscription`, `msp`, `operator-guide`, `ex_hardware_inventory/scope/profile`, `hardware_fakes`, `test_endpoint_catalog`, or `CHANGELOG`.
- **Skills**: No local skill was loaded. The issue concerns Mist cloud API calls and Python code. It does not concern Podman or Juniper devices.
- **Limits of this run**: No test, build, linter, container, or package install ran. No live Mist call was made. Repository reads used read-only Git commands and `gh` reads only.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk.

### D1. Controlling privilege for the MSP organization listing right

- **Alternatives**: (a) Any grant with `msp_id` holds the right. This is the current behavior. (b) A grant `role` value decides the right. (c) Probe the listing call and skip after an HTTP 403.
- **Chosen**: The grant `scope` value `msp` controls the right. A grant with another scope value makes no listing call.
- **Reason**: The OpenAPI defines the `scope` enum and requires `msp_id` when `scope` is `msp` (E2). The menu 309 profile reader counts only scope `msp` as MSP (E4). The operator guide assigns the listing effect to scope `msp` only (E5). The `mist-ops-platform` reader treats one scope `msp` row as MSP-wide access (E6). Option (c) sends the request that the issue asks to remove.
- **Risk**: A grant with scope `msp` and an insufficient role still receives HTTP 403 (U1). The existing failure row keeps the outcome visible.
- **Human decision required**: No.

### D2. The grant role does not gate the listing call

- **Alternatives**: (a) Allow only role `admin`. (b) Allow roles `admin`, `read`, and `write`. (c) Allow every role.
- **Chosen**: Option (c). The role does not gate the call.
- **Reason**: No local source names the role that `listMspOrgs` requires (E1, E2, E8). The public Juniper page could not be read (E9). A role gate could hide organizations that a read-level MSP admin can list. Option (c) keeps the current behavior for every role.
- **Risk**: A role without listing rights still gets HTTP 403. The change does not fix that case. Unverified item U1 records the gap.
- **Human decision required**: No.

### D3. A missing `scope` key counts as scope `msp`

- **Alternatives**: (a) Treat a missing key as not MSP, as `mist-ops-platform` does (E6). (b) Treat a missing key as MSP, as the menu 309 reader does (E4).
- **Chosen**: Option (b).
- **Reason**: The same MistHelper package already uses this rule (E4). Option (b) keeps the current call for a malformed grant, so the change adds no regression. The OpenAPI requires `scope` (E2), so the default affects only malformed data.
- **Risk**: A malformed grant with no scope still makes a listing call. Unverified item U3 records the lack of a Mist API statement.
- **Human decision required**: No.

### D4. Skipped sources reuse the status row fields

- **Alternatives**: (a) Add a `reason` field to `OrganizationScope`. (b) Add a second return value to `discover_organizations`. (c) Write a separate CSV file for skipped sources.
- **Chosen**: The row reuses `request_status` with value `skipped` and the `error` field for the reason text. The model file stays unchanged.
- **Reason**: Option (a) changes the CSV columns, and the contract in `design/contracts/status-rows.md` keeps them. Option (b) changes a method signature used by `operation.py` and tests. Option (c) adds an output file, which the operator guide does not describe.
- **Risk**: A reader that expects only the four current status values sees a fifth value. The reference update (FR-012) documents it.
- **Human decision required**: No.

### D5. One skipped row for each MSP id, and suppression when a listing right exists

- **Alternatives**: (a) One row for each grant without the right. (b) One row for each MSP id without the right, and no row when another grant for that MSP id holds the right.
- **Chosen**: Option (b).
- **Reason**: Option (a) writes duplicate rows. It also writes a skipped row for an MSP whose organizations the report lists. Option (b) matches the natural key `msp_id` in `design/data-model.md`.
- **Risk**: None known. The test functions 5 and 6 in T005 cover both cases.
- **Human decision required**: No.

### D6. The pending warning change stays out of this work

- **Alternatives**: (a) Include the pending working-copy change in this pull request. (b) Wait for the pending change to reach `main`. (c) Build on `main` and keep the pending change out.
- **Chosen**: Option (c).
- **Reason**: AGENTS.md requires one subject for each issue. The pending change has no issue number (U5). This change does not need the warning or the SDK mute. Overlap with the pending change is limited to new test functions in `test_client.py`.
- **Risk**: A rebase conflict in `test_client.py`. Keep new test functions separate from the pending test function.
- **Human decision required**: No.

### D7. Console summary behavior

- **Alternatives**: (a) Print nothing new. (b) Print the skipped count and each skipped source, and exclude skipped rows from the "Organizations discovered" count. (c) Print the skipped count and keep the discovered count unchanged.
- **Chosen**: Option (b).
- **Reason**: The issue requires the summary to show the MSP source as skipped, with the reason (acceptance criterion 2). A skipped source is not an organization, so option (c) inflates the discovered count.
- **Risk**: A reader who compares the discovered count across runs sees a change only when a skipped row exists. FR-012 documents the change.
- **Human decision required**: No.

### D8. Schedule the implementation

- **Alternatives**: (a) Schedule the implementation now at priority P3. (b) Keep the issue unscheduled until a later planning cycle.
- **Chosen**: Recommended option (a). The human owner approves scheduling.
- **Reason**: The issue marks the work as a future item that is not scheduled. Scheduling sets product priority. This decision belongs to a human.
- **Risk**: Scheduling without a human answer delays nothing, and it can create unplanned work.
- **Human decision required**: Yes. HUMAN-DECISION-REQUIRED. This decision is product priority.

## Evidence

- **E1 (Mist API, listing operation)**: `documentation/mist-api-openapi31yaml.yaml` lines 4081 to 4087 define `/api/v1/msps/{msp_id}/orgs`, `operationId: listMspOrgs`, and the description "List organizations managed by this MSP account, including MSP ownership and organization-group membership metadata." The operation names no role and no scope requirement. Remote row R45 confirms line 4085.
- **E2 (Mist API, privilege schema)**: The `admin_privilege` schema starts at line 68139. Its `msp_id` property (line 68143) reads "Required if `scope`==`msp`" (line 68145, remote row R47). The `role` enum at line 68213 lists `admin`, `helpdesk`, `installer`, `read`, and `write`. The `scope` enum at line 68223 lists `msp`, `org`, `orggroup`, `site`, and `sitegroup` (remote row R48). The `privilege_msp` schema at line 91465 has the same role enum at line 91498 and the scope enum at line 91508 (remote row R49). The enum lines are local copies with blob `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`, which matches remote `main`.
- **E3 (Mist API, profile read)**: `getSelf` is `operationId: getSelf` at line 25490 (remote row R46). The description reads "Get 'whoami' and privileges (which org and which sites I have access to)."
- **E4 (repository reader rule)**: `src/operations/exporting/ex_hardware_inventory/scope/profile.py` lines 131 to 136 read `_msp_ids`. Line 136 holds `grant.get("scope", "msp") == "msp"` with the comment "An org grant is not MSP." Remote rows R13 and R14 confirm lines 126 and 136. Line 126 holds the matching org rule `grant.get("scope", "org") == "org"`. The comment at line 136 states that an organization grant can carry `msp_id`.
- **E5 (operator guide)**: `documentation/operator-guide.md` lines 604 to 608 map each grant scope to its run effect. Scope `msp` "Adds every organization that `listMspOrgs` returns for that MSP." Scope `org` "Adds that organization." Scopes `orggroup`, `site`, and `sitegroup` "Add nothing." Remote row R18 confirms line 606. This table describes the menu 309 run, but it gives the repository rule for each scope.
- **E6 (mist-ops-platform rule)**: `mist-ops-platform/src/shared/services/auth.py` line 164 reads `is_msp = is_msp or priv.get("scope", "") == "msp"  # One MSP row grants every org.` Remote row R19 confirms the line.
- **E7 (installed mistapi source)**: `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py` line 17 defines `listMspOrgs(mist_session: _APISession, msp_id: str) -> _APIResponse`. Line 36 builds `uri = f"/api/v1/msps/{msp_id}/orgs"`. Line 38 calls `mist_session.mist_get(uri=uri, query=query_params)`. The docstring at lines 18 to 34 names no role. `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` line 17 defines `getSelf(mist_session: _APISession) -> _APIResponse`. The installed version is `mistapi-0.64.1.dist-info`.
- **E8 (Mist MSP API page, local copy)**: `documentation/MSP _ API _ Mist.html` line 1052 states "A MSP admin can invite other admin to manage (admin or read) the MSP and/or Org(s) under the MSP." The page shows MSP-scope privilege examples with `"scope":"msp"` and `"role": "admin"` at lines 980, 1041, and 1061. It does not state a listing requirement. Remote row R44 confirms line 1052.
- **E9 (external page)**: The tool fetched `https://www.juniper.net/documentation/us/en/software/mist/api/http/api/msps/orgs/list-msp-orgs`. The tool rejected the request with "resolves to blocked address". No role statement was read.
- **E10 (existing tests)**: `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` lines 104 to 135 use grant `{"org_id": "org-1", "org_name": "Primary", "scope": "org", "role": "read"}` and grant `{"msp_id": "msp-1", "scope": "msp", "role": "read"}`. Both grants use scopes that the planned rule keeps. Blob `fec6907fa47190960c5870f0d5093b301bec6566` matches local HEAD and remote `main`.
- **E11 (existing report code)**: `operation.py` line 818 iterates `_unique_msp_ids(organizations)` in `_read_msp_purchases`. MSP license evidence is read only for MSP ids that have organization rows. A skipped MSP therefore has no MSP license read. Remote row R12 confirms line 830.
- **E12 (other `listMspOrgs` callers)**: Nine callers exist in `src` (A3). Only the menu 309 resolver filters grants before the call, through the profile reader in E4.

## Remote Verification

Remote `main` commit: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. This commit equals the local HEAD commit. The local working copy differs from HEAD in `client.py` and `test_client.py`. Local line numbers below come from HEAD, which equals `main` for every committed file listed here. Each remote check reads the file body through `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main` and decodes the base64 text. The OpenAPI file, about 4.3 MB, was read through `git/blobs`.

The full tree was read three times with read-only calls. The calls fetched blob SHAs, checked the route folder, and searched for `4919`.

Result values: `present` means the claim holds at the line shown. `absent` means the claim does not hold on `main`. The blob column is `none` when the path does not exist.

| # | Claim | Path | Ref | Remote blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | `discover_organizations` is defined | `src/mist/intelligence/reports/subscription_expiry/client.py` | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 79 |
| R02 | The MSP branch tests `msp_id` only and calls `_discover_msp` | `src/mist/intelligence/reports/subscription_expiry/client.py` | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 99 |
| R03 | `_discover_msp` calls `listMspOrgs` | `src/mist/intelligence/reports/subscription_expiry/client.py` | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 170 |
| R04 | Helper `_warn_msp_list_failed` exists | `src/mist/intelligence/reports/subscription_expiry/client.py` | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | absent | 0 |
| R05 | Constant `HTTP_FORBIDDEN` exists | `src/mist/intelligence/reports/subscription_expiry/client.py` | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | absent | 0 |
| R06 | Function `_sdk_error_lines_muted` exists | `src/mist/intelligence/reports/subscription_expiry/client.py` | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | absent | 0 |
| R07 | `OrganizationScope` has a `request_status` field | `src/mist/intelligence/reports/subscription_expiry/model.py` | main | b5d8e29b20485425a826bd4b67ce727164d016e7 | present | 101 |
| R08 | `OrganizationScope` has an `error` field | `src/mist/intelligence/reports/subscription_expiry/model.py` | main | b5d8e29b20485425a826bd4b67ce727164d016e7 | present | 102 |
| R09 | `OrganizationScope.to_dict` returns `asdict` | `src/mist/intelligence/reports/subscription_expiry/model.py` | main | b5d8e29b20485425a826bd4b67ce727164d016e7 | present | 106 |
| R10 | The report starts status rows from discovery failures | `src/mist/intelligence/reports/subscription_expiry/operation.py` | main | c0d4d13d2390152da9596c7e3bea298d7867af64 | present | 534 |
| R11 | The console prints the "Organizations discovered" count | `src/mist/intelligence/reports/subscription_expiry/operation.py` | main | c0d4d13d2390152da9596c7e3bea298d7867af64 | present | 505 |
| R12 | `_unique_msp_ids` derives MSP ids from organization rows | `src/mist/intelligence/reports/subscription_expiry/operation.py` | main | c0d4d13d2390152da9596c7e3bea298d7867af64 | present | 830 |
| R13 | `_msp_ids` counts only scope `msp` grants | `src/operations/exporting/ex_hardware_inventory/scope/profile.py` | main | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 136 |
| R14 | `_org_grants` counts only scope `org` grants | `src/operations/exporting/ex_hardware_inventory/scope/profile.py` | main | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 126 |
| R15 | The status CSV row lists the request status | `documentation/cross-org-subscription-stock.md` | main | 405e9b6c9fe44a1b1a053f48a7be26e0a72f2d3e | present | 30 |
| R16 | The reference has a "Failure behavior" section | `documentation/cross-org-subscription-stock.md` | main | 405e9b6c9fe44a1b1a053f48a7be26e0a72f2d3e | present | 73 |
| R17 | The reference documents the `skipped` status | `documentation/cross-org-subscription-stock.md` | main | 405e9b6c9fe44a1b1a053f48a7be26e0a72f2d3e | absent | 0 |
| R18 | The operator guide maps scope `msp` to `listMspOrgs` | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 606 |
| R19 | The mist-ops reader treats one scope `msp` row as MSP-wide | `mist-ops-platform/src/shared/services/auth.py` | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 164 |
| R20 | A direct and MSP discovery test exists | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` | main | fec6907fa47190960c5870f0d5093b301bec6566 | present | 104 |
| R21 | The 403 warning test exists on `main` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` | main | fec6907fa47190960c5870f0d5093b301bec6566 | absent | 0 |
| R22 | The cross-org linked report test exists | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py` | main | 84f550ec961d7ddcd0ae3b727be7fa3c60a0328d | present | 112 |
| R23 | A skipped-source test exists on `main` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py` | main | 84f550ec961d7ddcd0ae3b727be7fa3c60a0328d | absent | 0 |
| R24 | CI defines `MYPY_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R25 | CI defines `VULTURE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R26 | CI defines `PYDOCSTYLE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R27 | CI defines `INTERROGATE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R28 | The Local gates table exists | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R29 | The five-children rule exists | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| R30 | The mistapi pin text reads `>=0.64.0,<0.65` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| R31 | Constitution Principle I, Five-Item Rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R32 | Constitution Principle VII, Action Logging | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R33 | AGENTS.md has a Writing style section | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R34 | AGENTS.md sets the 20-word instruction limit | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| R35 | The changelog fragment rule table exists | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 24 |
| R36 | The writing gate section exists | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| R37 | The directory and runtime layout section exists | `documentation/architecture.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 160 |
| R38 | The test and debug container section exists | `documentation/container-deployment.md` | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R39 | A pytest command example exists | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 268 |
| R40 | The MSP orgs page says the endpoint is not used | `documentation/api/msps/GET_msps_msp_id_orgs.md` | main | ffbc12a08dfcba82b1819e55e7866d0bf1ee0b8f | present | 183 |
| R41 | The reference record has a User Scenarios section | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 26 |
| R42 | The spec template has a Requirements section | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 82 |
| R43 | The plan template places `design/` artifacts | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 8 |
| R44 | The MSP admin page describes admin or read invites | `documentation/MSP%20_%20API%20_%20Mist.html` | main | e4efe5eb713556511b901c36c59703c517d4e808 | present | 1052 |
| R45 | OpenAPI defines `listMspOrgs` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 4085 |
| R46 | OpenAPI defines `getSelf` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25490 |
| R47 | OpenAPI requires `msp_id` when scope is `msp` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68145 |
| R48 | OpenAPI lists the admin privilege scope enum | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68223 |
| R49 | OpenAPI lists the MSP privilege scope enum | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 91508 |
| R50 | The route folder `specs/numbered/0/0/1/2/4/1/3/4` is free | `specs/numbered/0/0/1/2/4/1/3/4` | main | none | absent | 0 |
| R51 | No path on `main` contains `4919` | tree paths containing `4919` | main | none | absent | 0 |

Row count: 51. The `remote_checks` array in `4919-STATUS.json` has 51 entries.

## Sources

Local paths are relative to the repository root. Remote sources use `main`.

- Issue #4919 and issue #4713 bodies: `gh issue view` read on 2026-11-26.
- Open pull requests: `gh pr list --state open` read on 2026-11-26.
- Repository rules: `AGENTS.md` (full), `.github/copilot-instructions.md` (full), `.specify/memory/constitution.md` (full), the four templates under `.specify/templates/`, `changelog.d/README.md`, and `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md`, as they apply.
- Mist API: `documentation/mist-api-openapi31yaml.yaml` (E1 to E3) and `documentation/api/msps/GET_msps_msp_id_orgs.md` (R40). The coverage tables `documentation/MIST_API_GET_ENDPOINTS.md` line 331 and `documentation/MIST_API_MISSING_ENDPOINTS.md` line 336 also list the endpoint. Those local copies were not remote-checked, and no decision rests on them.
- mistapi source: `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py` (E7) and `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` (E7).
- Repository code: E4, E6, E10, E11, and `src/mist/intelligence/reports/subscription_expiry/operation.py` lines 494 to 519 (`_print_summary`).
- Public Juniper page: attempted and rejected (E9).

## Unverified

- **U1 (role threshold)**: No local source names the role that `listMspOrgs` requires. The public page was blocked (E9). The role decision D2 rests on the absence of evidence. A live test with one account for each role would settle it. That test needs a credential and belongs to the operator.
- **U2 (live `msp_id` on organization grants)**: The repository comment at `profile.py` line 136 says that an organization grant can carry `msp_id`. The OpenAPI does not state this. The run made no live call.
- **U3 (missing `scope` key in Mist responses)**: The OpenAPI requires `scope` (E2). The repository default (D3) is the only evidence for a missing key.
- **U4 (issue HTTP 403 claim)**: The HTTP 403 on every run comes from the issue body. No log, request, or response was attached to the issue.
- **U5 (pending change owner)**: The pending warning change exists only in the working copy. No issue number, pull request, or changelog fragment names it.
- **U6 (MSP license right)**: The right behind `listMspLicenses` is not checked. MSP license reads depend on organization rows (E11).
- **U7 (other callers)**: The line numbers and the content of the other eight `listMspOrgs` call sites are not checked against `main`. A local working-tree search found them (A3).

## Validation Not Possible

- No test, lint, type, coverage, or security gate ran. The local gates table requires these runs before merge (T-LOCAL-GATES).
- No live Mist call ran. The role threshold (U1) and the live `msp_id` presence (U2) need a live check by the operator.
- The local working copy holds uncommitted changes in `client.py` and `test_client.py`. The research read HEAD for every line citation.
