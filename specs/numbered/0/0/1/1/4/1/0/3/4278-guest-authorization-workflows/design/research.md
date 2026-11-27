# Research: Guest authorization workflows

**Issue**: [#4278](https://github.com/jmorrison-juniper/MistHelper/issues/4278). **Evidence date**: 2026-11-26. **Remote head**: main `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## 1. Method and Limits

- The run read `AGENTS.md`, the repository instructions, the constitution, and the four templates in full. It read the sections of `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md` that the cited rows name.
- The run read the owner comments on issue 4278 and the records for issues 4231 and 4588. The 4231 record exists in the repository. No 4231 folder exists in `spec-drafts`.
- The 4588 draft in `spec-drafts` was read in part for context: `spec.md` lines 1 to 120, `plan.md`, the decision register and remote table of `research.md`, and `contracts/api.md`. Other draft files were not read. The draft is not used as proof.
- The run made GitHub reads only with `gh`. It made no comment, label, edit, merge, or branch change.
- The run set the GitHub host and the token from the account variable. No variable value appears in this record.
- The run fetched the full `main` tree once. It decoded each cited file body from the contents API. The OpenAPI file exceeds the contents API limit, so the run used the blob API for that file only. The blob SHA is the same.
- The run ran no build, test, linter, formatter, install, container, or repository script.
- The run used read-only git commands only. The run computed blob hashes with `git hash-object` without the write flag.
- The SDK checks read the local `.venv` copy. Third-party packages are outside the repository tree.
- The run loaded no skill. Section 11 gives the reason.

## 2. Pins and Freshness

| Item | Value | Evidence |
| --- | --- | --- |
| Remote main | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | R001 |
| Local HEAD | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local checkout equals main. | R002 |
| Local blob hashes | Each of the 42 present cited repository paths has the same blob SHA locally and on main. | Tree check, Section 8 |
| mistapi, local SDK | 0.64.1 | R112 |
| mistapi, requirements | 0.64.1 | R049 |
| mistapi, pyproject | At least 0.64.1 and below 0.65 | R047 |
| mistapi, repository instructions | At least 0.64.0 and below 0.65 | R008 |
| PR 4279 | Merged 2026-10-18 with the offline projection. Merge commit `1e9b280d`. | R090 |
| PR 4290 | Merged 2026-10-20 with nine 4231 planning files. Merge commit `fcb0fc98`. | R091 |
| PR 4589 | Merged 2026-11-05 with the 4588 planning record. Merge commit `5d444bda`. | R092 |
| PR 4208 | Open. It changes `web_portal/app.py` and `web_portal/templates/base.html`. | R093 |
| Issue 4278 | Open. Labels: `feature`, `web-portal`, `needs-human-review`. | R094 |
| Issue 4231 | Open. | R095 |
| Issue 4588 | Open. | R096 |

Warning: the pin conflict in R008 and R047 can change which mistapi release installs. Task T-LOCAL-GATES checks the installed version before merge.

## 3. Existing Record Verification

**Step 3 (local search)**: No folder under `specs\` starts with `4278-`. The route folder `specs\numbered\0\0\1\1\4\1\0\3` does not exist.

**Step 4 (remote verification)**: The `main` tree holds no path that contains 4278 (R003). The `spec-drafts\4278` folder did not exist before this run.

**Result**: `existing_record.found` is false. The counts for verified, stale, and absent are zero. The run created the record from the issue and the cited evidence.

**Context records**:

- The 4231 planning record exists at `specs\numbered\0\0\1\1\3\4\1\1\4231-mist-guest-authorizations` (R084 to R087). It defines gates G1 through G5 (R085, R086).
- The 4588 planning record exists on main (R088, R089). Its draft in `spec-drafts\4588` includes a decision register and a remote table. Two of its claims conflict with the evidence here. Section 10 lists them.

## 4. Source Evidence and Licensing

- The issue body names the source repository `jmorrison-juniper/MistGuestAuthorizations` at commit `0213240cb9edfa237f763acd156b90a6049363cb`.
- The source `LICENSE` at that commit names Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (R097).
- MistHelper `LICENSE` names the same license (R052). Both repositories use one license family.
- The owner comment of 2026-11-06 states that the user confirmed authorship and control. It also states that the user authorized use, and that attribution and share-alike obligations apply. It asks that source-rights permission not be listed as an unresolved blocker.
- The issue body states that maintainers approve a clean-room path or record a compatible path before any source reuse.

**Decision D-3** (Section 6) selects a clean-room path. The run did not read the source application for design. The source claims in this record come from the issue body and the 4231 planning record (U15).

## 5. Evidence Summary for the Design

### 5.1 Mist API

- The site guest collection path and record path exist in the checked-in OpenAPI file (R028, R029).
- The update operation `updateSiteGuestAuthorization` is defined for the site record path (R030).
- The site guest schema marks `authorized` as writable (R032). It marks `mac` and `name` as read-only (R033, R035).
- The site guest `minutes` field has a maximum of 259200, which is 180 days (R034). The organization guest schema states the same maximum (R037).
- The client unauthorize path and operation exist (R038, R039). The description states that the operation unauthorizes a guest client and disconnects it.
- The site WLAN derived path and the site client statistics path exist (R040, R041).

### 5.2 mistapi SDK (local)

- The site guest module defines the list, get, update, and delete functions (R098 to R102).
- The organization guest module defines an update function (R103). The design excludes it (D-5).
- The client module defines `unauthorizeSiteWirelessClient` (R104).
- The stats module defines `listSiteWirelessClientsStats` (R105).
- The WLAN module defines `listSiteWlans` and `listSiteWlansDerived` (R106, R107). Derived WLANs wait for gate G5 (D-5).
- The organization site module defines `listOrgSites` (R108).
- The request module sets the HTTP 429 retry limit to three (R109). Its wrapper retries requests (R110). The `mist_put` method uses the wrapper (R111). The portal therefore reads the final response as the outcome.

### 5.3 Repository code

- The projection module defines `GuestAuthorizationReadModel` (R063). Its `project` method masks each MAC address and keeps missing values unknown (R064, R065). The projection test holds 22 cases (R066).
- The site guest exporter calls `searchSiteGuestAuthorization` for menu 200 (R067, R068). Menu 200 stays unchanged.
- The portal creates the app with an organization identifier (R057). It stores the Mist session in `APISESSION` (R059). It registers blueprints in `_register_blueprints` (R058). The WAN dashboard registration sits at line 207 (R060).
- The navigation bar holds one link for each page (R061, R062).
- The portal has no user login (R053). The allowlist defaults to empty (R055). The CSRF setup is in `_configure_csrf` (R056).
- The firmware policy route requires the typed word `CONFIGURE` (R070, R071). This is the portal precedent for typed confirmation.
- Menu 286 calls `unauthorizeSiteWirelessClient` through the client control action `unauthorize_guest` (R072, R073). The operation registry names guest unauthorize as destructive (R074, R075).
- The primary key strategy for `listSiteAllGuestAuthorizations` exists (R076).
- The Flask test fixtures `flask_app` and `client` exist (R077, R078).
- The guards for the e2e root (R079), the nested packages (R080), the changelog (R081), the container policy (R082), and module moves (R083) exist.

### 5.4 Configuration and runtime

- The Gunicorn command documents one worker with four threads (R046).
- `structlog` is pinned (R051). `flask-wtf` is pinned (R050). `mistapi` is pinned (R049).
- The SQLite file `data/mist_data.db` appears in the operator guide (R027).
- The compose file names the application service and publishes port 8055 (R043, R044).

## 6. Decision Register

Each decision lists the options, the chosen option, the reason, the risk, and the human flag. Only D-4 needs a human decision.

### D-1 Record location and slug

- **Options**: (a) the ROUTE folder plus `4278-guest-authorization-workflows`. (b) The ROUTE folder plus a shorter slug. (c) The 4231 folder.
- **Chosen**: (a).
- **Reason**: The orchestrator fixed the ROUTE. The slug follows the issue title. The 4231 folder belongs to a planning issue.
- **Risk**: Two folders describe guest work. The analysis names the owner of each.
- **Human decision**: No.

### D-2 Legacy record reuse

- **Options**: (a) reuse the 4588 draft. (b) reuse the 4231 repository record. (c) start a new record.
- **Chosen**: (c).
- **Reason**: No 4278 folder exists locally or on main (Section 3). The 4588 and 4231 records describe other issues. Reuse would blur the tracker identity.
- **Risk**: Future drafts may repeat claims from the 4588 draft. This record cites a remote row for each claim.
- **Human decision**: No.

### D-3 Source reuse and licensing

- **Options**: (a) copy source code and assets under CC BY-NC-SA with attribution. (b) build a clean-room implementation from functional requirements. (c) relicense the source.
- **Chosen**: (b).
- **Reason**: The issue body requires an independent implementation unless maintainers record a compatible path. The owner comment states that rights are not a blocker. Clean room meets both statements. Clean room copies no source expression, so no source license term applies to the new code.
- **Risk**: Clean room costs more work. Reviewers must reject copied expression. A later choice to reuse source needs a new human licensing decision.
- **Human decision**: No.

### D-4 Access model and write authority

- **Options**: (a) shared Mist session with the allowlist only, and writes with typed confirmation. (b) trusted identity from the header `X-Forwarded-User`, accepted only from peers in `PORTAL_TRUSTED_PROXIES`, required for reads and writes. (c) new local operator accounts with password hashes. (d) reads and writes disabled.
- **Chosen**: Recommended option (b). The maintainers must approve it or choose option (c).
- **Reason**: The portal has no user login (R053). The allowlist is the only access control (R055). Attribution needs a named operator under the 4231 requirement FR-017. Option (b) reuses the trusted-peer rule in the config docstring (R054) and adds no secret. Option (a) gives no attribution. Option (c) adds a credential store. Option (d) completes no workflow.
- **Risk**: A misconfigured proxy lets a client send the header. Without a configured proxy, the feature stays disabled. HUMAN-DECISION-REQUIRED: approve option (b), or choose option (c).
- **Human decision**: Yes.

### D-5 Scope and discovery

- **Options**: (a) organization and site scope. (b) site scope only. (c) automatic fallback to organization scope after an error.
- **Chosen**: (b). Site discovery uses `listOrgSites` (R108). WLAN discovery uses `listSiteWlans` (R106). Derived WLANs wait for gate G5 (R107).
- **Reason**: The 4231 contract states that the organization list has no WLAN filter (R087). A fallback widens the scope, which the 4231 record forbids.
- **Risk**: Operators cannot manage template-inherited WLANs yet.
- **Human decision**: No.

### D-6 Read path

- **Options**: (a) list call, masked projection, and read-back. (b) search call with time windows. (c) read each target only.
- **Chosen**: (a). The read-back uses `getSiteGuestAuthorization` (R101).
- **Reason**: The list call returns the records for one site and one WLAN (R028, R102). The projection keeps missing values unknown (R063 to R065).
- **Risk**: The list call may page (U03). TEST-005 checks the call arguments. A response sample must confirm the paging rule before release.
- **Human decision**: No.

### D-7 Grant and edit fields

- **Options**: (a) copy every source field. (b) send all fields and rely on Mist to ignore read-only fields. (c) send writable fields only.
- **Chosen**: (c). The writable fields are `authorized`, `minutes`, `company`, `email`, and `field1` through `field4` (R032). Read-only fields such as `mac` and `name` never reach the body (R033, R035). The body omits any notification field.
- **Reason**: The schema marks `mac` and `name` read-only (R033, R035). Sending a read-only field can cause a silent change.
- **Risk**: Operators cannot edit the name. The page shows the name as read-only.
- **Human decision**: No.

### D-8 Duration

- **Options**: (a) source presets with a maximum of 2628000 minutes. (b) clamp to the schema maximum. (c) reject values outside 1 through 259200.
- **Chosen**: (c). Presets are 60, 480, 1440, 2880, 4320, 10080, 43200, and 129600 minutes. The default is 1440.
- **Reason**: The schema bounds minutes at 259200 (R034, R037). The meaning of 0 minutes is unverified (U01).
- **Risk**: Operators cannot grant more than 180 days. The owner can change the bound with new evidence.
- **Human decision**: No.

### D-9 Extension

- **Options**: (a) enable now. (b) disable until gate G5 records verified behavior. (c) remove extension.
- **Chosen**: (b).
- **Reason**: The extension semantics are unverified (U02). The 4231 record requires verified duration behavior before extension (R086).
- **Risk**: Operators cannot extend access until G5 passes.
- **Human decision**: No.

### D-10 Revocation

- **Options**: (a) PUT with 0 minutes, which the source uses. (b) DELETE the record. (c) PUT with `authorized` set to false. (d) call `unauthorizeSiteWirelessClient` once, then read back the record. (e) keep revoke disabled.
- **Chosen**: (d), gated by G5. The call is `unauthorizeSiteWirelessClient` (R104). The existing menu 286 action already calls it (R072, R073). The OpenAPI operation documents guest unauthorize with disconnect (R038, R039).
- **Reason**: Option (a) has no verified meaning (U04). Option (b) destroys a production record, and a 200 response does not prove removal. Option (c) has no evidence. Option (d) reuses a reviewed path and adds a read-back check.
- **Risk**: Warning: the call disconnects a live client. Use REVOKE only after review. The read-back may still show the record as active (U04).
- **Human decision**: No.

### D-11 Client search

- **Options**: (a) site client statistics with a local filter. (b) organization-wide client search. (c) manual MAC entry only.
- **Chosen**: (a). The result holds at most 200 rows.
- **Reason**: The SDK function is site scoped (R105). Organization search widens the scope (D-5).
- **Risk**: The hostname and IP fields are unverified (U05).
- **Human decision**: No.

### D-12 Typed confirmation and review digest

- **Options**: (a) one word for every write. (b) click-only confirmation. (c) one word for each action, with a digest of the review.
- **Chosen**: (c). The words are GRANT, UPDATE, EXTEND, REVOKE, and IMPORT. The digest covers the scope, the payload, and the revision.
- **Reason**: Constitution Principle III requires typed confirmation for cloud changes (R012). The firmware policy route uses a typed word (R070, R071).
- **Risk**: Operators must type each word exactly. The page shows the word and the scope.
- **Human decision**: No.

### D-13 CSV bounds and headers

- **Options**: (a) no limit. (b) 1 MiB and 1000 rows, the value in the 4588 draft. (c) 262144 bytes and 200 rows.
- **Chosen**: (c). The ten headers are `site_id`, `wlan_id`, `guest_mac`, `minutes`, `company`, `email`, `field1`, `field2`, `field3`, and `field4`. Duplicates reject. Writes run one row at a time.
- **Reason**: 200 rows fit one review page. Sequential writes keep one target in review at a time. The owner can raise the limit with new evidence.
- **Risk**: Large sites need several batches. The issue asks maintainers to approve these limits.
- **Human decision**: No.

### D-14 Audit store and retention

- **Options**: (a) ArangoDB transactions. (b) Redis keys. (c) a SQLite table in `data/mist_data.db`.
- **Chosen**: (c). The table is `guest_authorization_audit`. An intent row precedes dispatch. An outcome row follows the response. Rows are never deleted by the feature. The operator copies the file while the portal is stopped.
- **Reason**: The operator guide lists `data/mist_data.db` (R027). The constitution requires a declared store for transactions (R013). Redis is ephemeral. The table holds masked data only.
- **Risk**: The store can lock under load (U08). TEST-017 and TEST-018 cover it before any write.
- **Human decision**: No.

### D-15 Failure policy

- **Options**: (a) retry an unknown write. (b) stop and reconcile. (c) continue the batch.
- **Chosen**: (b). An intent failure stops before dispatch. An outcome failure reports the cloud result and the audit failure, then stops later writes. A rate limit after SDK retries stops the batch. A timeout, a server error, or a missing response reports unknown.
- **Reason**: The 4231 requirements FR-016 and FR-018 require this behavior. The SDK retries 429 responses before the portal reads the final response (R109, R110).
- **Risk**: Operators must reconcile after a stop. The page shows the next step.
- **Human decision**: No.

### D-16 Concurrency

- **Options**: (a) rely on the database alone. (b) a process lock and an immediate transaction. (c) several workers.
- **Chosen**: (b). The run keeps one worker with four threads (R046).
- **Reason**: One worker gives one lock domain. The threads share the lock. The in-flight check uses the site, the WLAN, and the masked target.
- **Risk**: U08 remains open. TEST-018 covers races between threads.
- **Human decision**: No.

### D-17 Logging and masking

- **Options**: (a) log full MAC addresses. (b) log masked MAC addresses and error categories. (c) log nothing.
- **Chosen**: (b). The feature uses structlog (R051). Log text stays ASCII.
- **Reason**: FR-025 forbids private values in logs. The projection already masks MAC addresses (R063 to R065).
- **Risk**: Less detail for troubleshooting. Each error category names the next step.
- **Human decision**: No.

### D-18 Portal integration and file ownership

- **Options**: (a) edit the shared files now. (b) wait for the PR 4208 handover. (c) place the feature in a separate application.
- **Chosen**: (b). Option (c) breaks FR-027.
- **Reason**: PR 4208 changes `web_portal/app.py` and `base.html` (R093).
- **Risk**: The feature waits for the handover.
- **Human decision**: No.

### D-19 Package and test placement

- **Options**: (a) keep the module. (b) replace the module with a package. (c) add a second module beside it.
- **Chosen**: (b) for `src`. Unit and contract tests sit under `tests/unit/web_portal/guest_authorizations`. The browser test sits under `tests/e2e/web_portal`.
- **Reason**: The nested-package guard counts children under `src` (R080). The e2e guard fixes the root entries (R079). The e2e convention places shared portal tests under `tests/e2e/web_portal`.
- **Risk**: Remediations R-1 and R-2 remain open for the grandfathered test folders.
- **Human decision**: No.

### D-20 Delivery order

- **Options**: (a) writes first. (b) read review first, then writes, then import. (c) import first.
- **Chosen**: (b).
- **Reason**: Read review needs the fewest approvals. The 4588 record uses the same order.
- **Risk**: Read review still needs D-4 and the G5 read evidence.
- **Human decision**: No.

### D-21 Documentation and surface

- **Options**: (a) a new menu. (b) a new service. (c) one portal page, one operator guide section, and one changelog fragment.
- **Chosen**: (c).
- **Reason**: FR-027 forbids new services and ports. The operator guide (R026) and the changelog (R022) cover the change.
- **Risk**: The operator guide must stay current.
- **Human decision**: No.

## 7. Remote Verification Table

Rows R001 to R112 are the remote checks. The `remote_checks` array in `4278-STATUS.json` holds the same 112 rows in the same order. Local SDK rows use the path prefix `.venv/Lib/site-packages/`. Their blob SHA is the local `git hash-object` value. Pull request and issue rows carry the merge commit or the state in the blob column.

| # | Claim | Path | Ref | Blob SHA or object | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R001 | Main commit exists on GitHub | commit main (MistHelper) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R002 | Local HEAD equals main | local HEAD (MistHelper) | local | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R003 | A 4278 record folder exists on main | git/trees/main (paths containing 4278) | main | n/a (tree) | absent | 0 |
| R004 | A guest authorization package exists on main | src/interfaces/portals/guest_authorizations/ | main | n/a (tree) | absent | 0 |
| R005 | web_portal/wsgi.py exists on main | web_portal/wsgi.py | main | n/a (tree) | absent | 0 |
| R006 | AGENTS.md defines the writing rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R007 | Repository instructions define the local gates | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R008 | Repository instructions name the mistapi range 0.64.0 to 0.65 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| R009 | Repository instructions define the module move gates | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 261 |
| R010 | Repository instructions require data-testid tests for web UI | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 301 |
| R011 | Repository instructions place wsgi.py under web_portal | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 180 |
| R012 | Constitution Principle III requires typed confirmation for cloud changes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R013 | Constitution names the declared operational store | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| R014 | Constitution forbids new direct children in noncompliant parents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 43 |
| R015 | Constitution defines test containers in the compose group | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 302 |
| R016 | Constitution names a mistapi floor of 0.59 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 279 |
| R017 | Spec template has the User Scenarios heading | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 11 |
| R018 | Plan template has the Constitution Check heading | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 44 |
| R019 | Tasks template has the Format heading | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 20 |
| R020 | Checklist template has the category heading | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 23 |
| R021 | Reference record 4920 has the User Scenarios heading | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 26 |
| R022 | Changelog README defines the issue fragment name | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R023 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R024 | CI defines VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R025 | Container policy documents test and debug containers | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R026 | Operator guide has the Open a portal section | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 211 |
| R027 | Operator guide lists data/mist_data.db as the SQLite database | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 752 |
| R028 | OpenAPI defines the site guests collection path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32317 |
| R029 | OpenAPI defines the site guest record path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32465 |
| R030 | OpenAPI defines operation updateSiteGuestAuthorization | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32509 |
| R031 | OpenAPI defines the guest schema at site scope | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80928 |
| R032 | OpenAPI marks authorized as writable | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80944 |
| R033 | OpenAPI marks mac as read-only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80987 |
| R034 | OpenAPI bounds site guest minutes at 259200 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80994 |
| R035 | OpenAPI marks site guest name as read-only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80998 |
| R036 | OpenAPI defines the guest_org schema | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81023 |
| R037 | OpenAPI bounds guest_org minutes at 259200 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81096 |
| R038 | OpenAPI defines the client unauthorize path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 27818 |
| R039 | OpenAPI defines operation unauthorizeSiteWirelessClient | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 27826 |
| R040 | OpenAPI defines the site WLAN derived path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 42404 |
| R041 | OpenAPI defines the site stats clients path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 39482 |
| R042 | MIST_API_GET_ENDPOINTS lists the Sites Guests group | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1253 |
| R043 | compose.yml defines the misthelper service | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 53 |
| R044 | compose.yml publishes port 8055 | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 86 |
| R045 | wsgi.py creates WebPortalApp | wsgi.py | main | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 107 |
| R046 | wsgi.py documents one worker with four threads | wsgi.py | main | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 4 |
| R047 | pyproject.toml pins mistapi from 0.64.1 below 0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R048 | pyproject.toml requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R049 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R050 | requirements.txt pins flask-wtf 1.3.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 54 |
| R051 | requirements.txt pins structlog 26.1.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 249 |
| R052 | MistHelper LICENSE names CC BY-NC-SA 4.0 | LICENSE | main | d115eeab9dbd6f61d0233b0894d3f8309bb976e8 | present | 1 |
| R053 | Config states the portal has no user authentication | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 12 |
| R054 | Config describes the trusted proxy setting | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 9 |
| R055 | Config defaults PORTAL_ALLOWED_IPS to empty | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 83 |
| R056 | Config configures CSRF protection | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 297 |
| R057 | app.py defines create_app with an organization identifier | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 37 |
| R058 | app.py defines _register_blueprints | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 182 |
| R059 | app.py stores the Mist session in APISESSION | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 155 |
| R060 | app.py registers wan_dashboard_bp | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 207 |
| R061 | base.html defines the nav-dashboard link | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 52 |
| R062 | base.html defines the nav-operations link | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 60 |
| R063 | Projection class GuestAuthorizationReadModel exists | src/interfaces/portals/guest_authorizations.py | main | 7101772d492af0a340b88d3cd3c2e221db9e7d31 | present | 17 |
| R064 | Projection defines project | src/interfaces/portals/guest_authorizations.py | main | 7101772d492af0a340b88d3cd3c2e221db9e7d31 | present | 21 |
| R065 | Projection docstring keeps guest writes blocked | src/interfaces/portals/guest_authorizations.py | main | 7101772d492af0a340b88d3cd3c2e221db9e7d31 | present | 6 |
| R066 | Projection tests hold 22 parametrized cases | tests/unit/web_portal/test_guest_authorization_read_model.py | main | 464c999daefa9d77ff451778e5228aa9a9033e38 | present | 11 |
| R067 | Site guest exporter calls searchSiteGuestAuthorization | src/operations/exporting/export/site_guest_authorization_exporter.py | main | 4d4c500b56ed9932611fe0d7ad837b8af8d03677 | present | 109 |
| R068 | Site guest exporter defines guest_authorizations | src/operations/exporting/export/site_guest_authorization_exporter.py | main | 4d4c500b56ed9932611fe0d7ad837b8af8d03677 | present | 84 |
| R069 | MistHelper.py maps menu 200 to the exporter | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4112 |
| R070 | Firmware policy requires the typed word CONFIGURE | web_portal/routes/firmware_policy/__init__.py | main | cea61c06f9ff88cc8cac107e758ea434d7f084c0 | present | 155 |
| R071 | Firmware policy page labels the CONFIGURE field | web_portal/routes/firmware_policy/templates/firmware_policy.html | main | 4ef6222c68e2eca163a270d22c698cee33f618fd | present | 55 |
| R072 | Client control defines the unauthorize_guest action | src/mist/resources/device/client_session_control/actions.py | main | a8e95367db10ad31292befdb7d6446cf260c6fc3 | present | 60 |
| R073 | Client control maps unauthorize_guest to unauthorizeSiteWirelessClient | src/mist/resources/device/client_session_control/actions.py | main | a8e95367db10ad31292befdb7d6446cf260c6fc3 | present | 88 |
| R074 | Operation registry names guest unauthorize as destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 427 |
| R075 | Operation registry defines menu 286 as destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 430 |
| R076 | Primary key strategies define listSiteAllGuestAuthorizations | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 1288 |
| R077 | e2e conftest defines the flask_app fixture | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 260 |
| R078 | e2e conftest defines the client fixture | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 287 |
| R079 | E2E root guard allows five entries | tests/guardrails/test_e2e_package_structure.py | main | c5be7ed0b21eec56c7d586b7025cf28f0fc4fb42 | present | 18 |
| R080 | Nested package guard sets five children under src | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R081 | Changelog fragment guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 1 |
| R082 | Container policy guard exists | tests/guardrails/test_container_policy_docs.py | main | 1b842c302e52bcb43a95e4a2aed2366a93d94909 | present | 1 |
| R083 | Move-module guard exists | tests/guardrails/test_move_module_guidance.py | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 1 |
| R084 | Record 4231 spec.md has its feature title | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/spec.md | main | c54db8de9e10647e1936731946135566fca8faf5 | present | 1 |
| R085 | Record 4231 research defines the unresolved gate section | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/research.md | main | fcbbf71c1cbc2f223ee3bba5e2932a967793c540 | present | 85 |
| R086 | Record 4231 research defines gate G5 | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/research.md | main | fcbbf71c1cbc2f223ee3bba5e2932a967793c540 | present | 96 |
| R087 | Record 4231 contract lists candidate signatures | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/contracts/mist-api.md | main | f0efcca2c752a420448ed91f9f70f65dd0e9a683 | present | 10 |
| R088 | Record 4588 spec defines User Story 2 | specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/spec.md | main | 1abe8eb89d62178063764a22be66c1902a570967 | present | 39 |
| R089 | Record 4588 research defines the conflicts section | specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/design/research.md | main | 5b65dfc349c28f4404f1685f128e9b223fcb0fd1 | present | 107 |
| R090 | PR 4279 merged with the offline projection | pull/4279 (merge commit) | main | 1e9b280ddb0285048e515cb837f6802ac38ceb0e | present | 0 |
| R091 | PR 4290 merged with nine 4231 planning files | pull/4290 (merge commit) | main | fcb0fc980b9124116307ea37fefbbbd1306bce3f | present | 0 |
| R092 | PR 4589 merged with the 4588 planning record | pull/4589 (merge commit) | main | 5d444bda23ea50de131d67b6e6fcf37055adfa77 | present | 0 |
| R093 | PR 4208 is open and changes web_portal/app.py and base.html | pull/4208 | main | n/a (pull request) | present | 0 |
| R094 | Issue 4278 is open | issues/4278 | main | n/a (issue) | present | 0 |
| R095 | Issue 4231 is open | issues/4231 | main | n/a (issue) | present | 0 |
| R096 | Issue 4588 is open | issues/4588 | main | n/a (issue) | present | 0 |
| R097 | Source LICENSE names CC BY-NC-SA 4.0 at the pinned commit | MistGuestAuthorizations: LICENSE | 0213240cb9edfa237f763acd156b90a6049363cb | bbea5fed78ca98720c6590d4151de423714ea6de | present | 1 |
| R098 | SDK defines searchSiteGuestAuthorization | .venv/Lib/site-packages/mistapi/api/v1/sites/guests.py | local | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 148 |
| R099 | SDK defines updateSiteGuestAuthorization | .venv/Lib/site-packages/mistapi/api/v1/sites/guests.py | local | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 280 |
| R100 | SDK defines deleteSiteGuestAuthorization | .venv/Lib/site-packages/mistapi/api/v1/sites/guests.py | local | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 252 |
| R101 | SDK defines getSiteGuestAuthorization | .venv/Lib/site-packages/mistapi/api/v1/sites/guests.py | local | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 224 |
| R102 | SDK defines listSiteAllGuestAuthorizations | .venv/Lib/site-packages/mistapi/api/v1/sites/guests.py | local | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 17 |
| R103 | SDK defines updateOrgGuestAuthorization | .venv/Lib/site-packages/mistapi/api/v1/orgs/guests.py | local | 398490dbcefef76c86ab6750af51bd21e6d98cb2 | present | 225 |
| R104 | SDK defines unauthorizeSiteWirelessClient | .venv/Lib/site-packages/mistapi/api/v1/sites/clients.py | local | 7f07a0f78e66291b72d961e1e5421bf9d2767232 | present | 852 |
| R105 | SDK defines listSiteWirelessClientsStats | .venv/Lib/site-packages/mistapi/api/v1/sites/stats.py | local | bce91c2c8ff2c793190c2afb3548ae83e15322c2 | present | 960 |
| R106 | SDK defines listSiteWlans | .venv/Lib/site-packages/mistapi/api/v1/sites/wlans.py | local | 45f2572e4e3b23ee8e4df9a7a061abef2423dcd4 | present | 17 |
| R107 | SDK defines listSiteWlansDerived | .venv/Lib/site-packages/mistapi/api/v1/sites/wlans.py | local | 45f2572e4e3b23ee8e4df9a7a061abef2423dcd4 | present | 89 |
| R108 | SDK defines listOrgSites | .venv/Lib/site-packages/mistapi/api/v1/orgs/sites.py | local | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 17 |
| R109 | SDK sets the HTTP 429 retry limit to three | .venv/Lib/site-packages/mistapi/__api_request.py | local | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 59 |
| R110 | SDK request wrapper retries requests | .venv/Lib/site-packages/mistapi/__api_request.py | local | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 203 |
| R111 | SDK mist_put sends through the request wrapper | .venv/Lib/site-packages/mistapi/__api_request.py | local | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 325 |
| R112 | Installed mistapi version is 0.64.1 | .venv/Lib/site-packages/mistapi-0.64.1.dist-info/METADATA | local | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |

**Row count**: 112. The STATUS file holds 112 rows. The summary states 112.

Notes on the table:

- R011 and R016 are stale. Each file states a claim that the repository contradicts. Section 10 explains the conflict.
- R047 and R008 disagree on the mistapi lower bound. Section 2 and Section 10 record the conflict.
- R003 to R005 are absent by design. They confirm that the feature has no existing record, package, or web_portal wsgi file.

## 8. Tree and Hash Method

- The tree call returned 11404 entries with `truncated` false. Every cited repository path appeared in the tree, except `web_portal/wsgi.py`.
- The first tree check covered 43 cited paths. Forty-two appeared in the tree. `web_portal/wsgi.py` did not.
- For each of the 42 present paths, the local `git hash-object` value equaled the remote blob SHA. Each of those files is identical locally and remotely.
- The five guard files were read through the contents API. Their blob SHAs appear in R079 to R083.
- The SDK hashes come from `git hash-object` on the `.venv` files without the write flag.
- The guard file blob SHAs came from the contents API.

## 9. Sources

- Issue 4278 body and owner comments of 2026-11-06 and 2026-11-08 (`gh issue view`).
- Issue 4231 and issue 4588 metadata (`gh issue view`).
- PR 4279, PR 4290, PR 4589, and PR 4208 metadata and files (`gh pr view`).
- Remote repository files at `main` (`gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`).
- Remote OpenAPI file blob (`gh api repos/jmorrison-juniper/MistHelper/git/blobs/b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`).
- Source `LICENSE` at the pinned commit (`gh api repos/jmorrison-juniper/MistGuestAuthorizations/contents/LICENSE?ref=0213240cb9edfa237f763acd156b90a6049363cb`).
- Local repository files under `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper` (read only).
- Local SDK files under `.venv\Lib\site-packages\mistapi` (read only).
- Draft records under `spec-drafts\4588` (context only).

## 10. Conflicts Found in Existing Work

1. The repository instructions place `wsgi.py` under `web_portal/` (R011). The file is at the root (R045). `web_portal/wsgi.py` is absent (R005).
2. The constitution names a mistapi floor of 0.59 (R016). The pin is at least 0.64.1 (R047, R049).
3. The repository instructions name a mistapi lower bound of 0.64.0 (R008). The pyproject lower bound is 0.64.1 (R047). The brief uses 0.64.0. Task T-LOCAL-GATES must confirm which bound applies.
4. The 4588 draft states that issue 4278 is closed (draft R11). GitHub reports it open (R094).
5. The 4588 draft omits the existing unauthorize operation. Menu 286 already uses it (R072, R073, R075). The draft decision D-8 therefore misses an option.
6. The 4588 draft cites a 1 MiB and 1000-row CSV bound. This record selects 262144 bytes and 200 rows (D-13).

## 11. Skills

No skill was loaded. The guest authorization design needs Mist API evidence, SDK evidence, and repository evidence. The available Juniper skills cover device behavior and network access control design. The Podman skills cover container internals. None answers a question in this record.

## 12. Unverified

- U01: Whether a grant creates a missing authorization record. The SDK signature shows a generic body (R099). The OpenAPI text does not state the create behavior (R030).
- U02: Whether a new minutes value replaces or adds to the expiry during extension (R032, R034). No live call was made.
- U03: Whether `listSiteAllGuestAuthorizations` returns every record without paging (R102). The SDK call exposes no paging parameter, and no response sample exists.
- U04: Whether `unauthorizeSiteWirelessClient` changes the `authorized` value of the record (R039). The OpenAPI text describes the client effect only.
- U05: Whether `listSiteWirelessClientsStats` returns hostname and IP fields (R105). The SDK signature does not describe the response.
- U06: Whether `listSiteWlansDerived` returns template-inherited WLANs in the same shape as `listSiteWlans` (R107).
- U07: Whether `listSiteWlans` returns an enabled field. This run did not read the response shape.
- U08: Whether SQLite stays safe under one worker with four threads. No test exists yet (D-16).
- U09: The Mist rate limits for these calls. The adaptive tuning file `data/tuning_data.json` exists, but this run did not read it.
- U10: Whether a declared operational store exists in the tree. Constitution line 315 names one (R013). A search found only a docstring in `src/mist/intelligence/juniper_docs/harvest/state_store.py` line 16. The search is not exhaustive.
- U11: Whether the upstream mistapi tag and source commit match the local SDK. This run used local files only (R098 to R112).
- U12: The official HPE documentation pages were not fetched. The local OpenAPI file and the SDK docstrings answer the questions in scope.
- U13: Visual parity with the source application. No UI exists, so no comparison ran.
- U14: The 4588 draft claims were not used as proof. The conflicts appear in Section 10.
- U15: The source application behavior was not read for the design. The source claims come from the issue body and the 4231 record (R084 to R087).
- U16: The scope of the owner live-test approval of 2026-11-08 has no run limit in the comment.
- U17: Whether the deployment proxy removes client-supplied identity headers. The repository holds no proxy configuration.
