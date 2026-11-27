# Research: Migrate Mist Guest Authorizations (issue #4231)

## 1. Provenance and method

- MistHelper remote main: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The recursive tree held 11404 entries and was not truncated.
- Pinned source: `jmorrison-juniper/MistGuestAuthorizations` at `0213240cb9edfa237f763acd156b90a6049363cb`. This commit equals that repository's remote main. Its recursive tree held 46 entries.
- Installed SDK: `.venv\Lib\site-packages\mistapi`, version 0.64.1 (`METADATA` line 3).
- Method: one recursive tree call per repository. Blob SHAs were compared with the cited files. For MistHelper, 25 files matched remote main and were read locally for line numbers. `LICENSE` and `deploy/.env.example` differ locally, so their remote blobs were read. Source bodies were read by remote blob SHA.
- The local source checkout is nine commits behind its remote. It was not used as evidence. Its `.env` file was not opened.
- Brief rule 2 applies. No tests, linters, builds, containers, or repository scripts ran.
- Skill consulted: `juniper-access-assurance-nac`. No claim in this record depends on it.

## 2. Issue and linked work

| Item | State | Evidence |
| --- | --- | --- |
| Issue #4231 | OPEN. Created 2026-10-15. Updated 2026-11-06. Labels `feature` and `web-portal`. | `gh issue view 4231` (2026-11-26). Two comments dated 2026-10-16 and 2026-11-06 describe planning status. |
| PR #4290 | MERGED 2026-10-20. Restored the legacy 4231 planning files and asks to keep #4231 open. | `gh pr view 4290` (read earlier in this session). |
| PR #4589 | MERGED 2026-11-05. Parity planning for issue #4588. | `gh pr view 4589` (read earlier in this session). |
| PR #4279 | MERGED 2026-10-18. Offline three-field projection. | `gh pr view 4279` (read earlier in this session). |
| PR #2916 | Unrelated to this issue. | Read earlier in this session. |
| Issue #4278 | OPEN. Implementation tracking. | Read earlier in this session. |
| Issue #4588 | OPEN. Parity planning, labels `feature`, `docs`, `in-progress`. | `gh issue list` (2026-11-26). |
| Issue #4936 | OPEN. Browser sign-in for the operations portal on port 8055. | Operator guide line 627 (R-62). |
| PR #4208 | OPEN. Owns `web_portal/app.py` and `web_portal/templates/base.html`. | Read earlier in this session. |

## 3. Existing record verification

The legacy record at `specs\numbered\0\0\1\1\3\4\1\1\4231-mist-guest-authorizations` holds nine files on remote main. It does not match the brief layout. The claim table below lists 26 claims. Counts: 17 verified, 4 stale, 2 absent, and 3 unverified.

| ID | Legacy claim | Evidence | Status |
| --- | --- | --- | --- |
| L-01 | The record folder exists at the route with nine files | Tree listing (R-41, R-82 to R-90) | verified |
| L-02 | `spec.md` exists | R-82 | verified |
| L-03 | `plan.md` exists | R-83 | verified |
| L-04 | `tasks.md` exists | R-84 | verified |
| L-05 | `design/research.md` exists | R-85 | verified |
| L-06 | `design/data-model.md` exists | R-86 | verified |
| L-07 | `design/quickstart.md` exists | R-87 | verified |
| L-08 | `design/contracts/mist-api.md` exists | R-88 | verified |
| L-09 | `design/contracts/portal.md` exists | R-89 | verified |
| L-10 | `checklists/requirements.md` exists | R-90 | verified |
| L-11 | `guest_authorizations.py` holds `GuestAuthorizationReadModel` | R-32 | verified |
| L-12 | The read model test file holds five test functions | R-34 | verified |
| L-13 | The nested guard limit is five children | R-35 | verified |
| L-14 | The nested baseline has no `src/interfaces/portals` entry | R-37 | verified |
| L-15 | Issue #4231 is open | Section 2 | verified |
| L-16 | PR #4279 merged on 2026-10-18 | Section 2 | verified |
| L-17 | PR #4290 merged on 2026-10-20 and restored the legacy planning files | Section 2 | verified |
| L-18 | The plan targets Python 3.13 | Stale. `pyproject.toml` line 23 requires 3.15 (R-81). | stale |
| L-19 | The plan places code under `src/interfaces/portals/guest_workflows/` | Stale. The placement adds a sixth child to `portals`, and the guard allows five (R-38, R-35). | stale |
| L-20 | Checklists sit at the feature root | Stale. The brief layout requires `design/checklists/` (R-90). | stale |
| L-21 | The API source is `documentation/mist-api-openapi3json.json` | Stale. The brief names the OpenAPI 3.1 YAML (R-64 to R-73). | stale |
| L-22 | `analysis.md` exists | Absent from the tree (R-91). | absent |
| L-23 | Checkpoint commit `20cf234e2` preserves the record | GitHub returns HTTP 422. No commit found (R-92). | absent |
| L-24 | Commit `1e9b280dd` holds the record tree | The commit exists (R-93). Its tree was not compared. | unverified |
| L-25 | The projection test suite has 22 cases | Static reading only. The count was not confirmed. | unverified |
| L-26 | GitHub license metadata for the source reads NOASSERTION | Not fetched. | unverified |

## 4. Pinned source behavior

Source: `jmorrison-juniper/MistGuestAuthorizations` at `0213240cb9edfa237f763acd156b90a6049363cb`. Each line cites a remote blob row in section 8.

- The app exposes 13 routes. Authorize, delete, update, bulk import, and health routes sit at `app.py` lines 85 to 423 (R-119 to R-123).
- Authorize defaults to 1440 minutes (`app.py` line 195, R-120). Bulk import also defaults to 1440 minutes (line 407, R-123).
- `get_wlan_guests` lists site guests (`mist_connection.py` line 399, R-124). It falls back to the organization-wide list at line 423 (R-125).
- `authorize_guest` writes at site scope and then writes at organization scope at line 592 (R-126, R-127). It overwrites `field4` with the token name at lines 550 to 552.
- `deauthorize_guest` sends `minutes` 0 with no WLAN filter at line 652 (R-128). It checks for a 2xx status at line 659 (R-129).
- `search_wireless_clients` calls the site statistics method at line 797 (R-130). Its exception branch starts at line 803.
- The UI allows 2628000 minutes at `templates/index.html` line 736 (R-131). It applies 1440 minutes silently at line 1409 (R-132). It sends `DELETE` at line 1673 (R-133). It has no `confirm(` call (R-134).
- The guide claims a five-year maximum (line 27, R-116). It says DELETE returns 200 and does not remove access (line 238, R-118).
- The Mist schema caps `minutes` at 259200, which is 180 days (R-68, `mist-api-openapi31yaml.yaml` line 80994 description).

## 5. MistHelper state

- The portal has no user authentication. Its access control is the IP allowlist (`web_portal/services/config.py` line 12, R-46). CSRF uses `CSRFProtect` (lines 297 and 301, R-47 and R-48).
- Blueprints register at `web_portal/app.py` line 182 (R-42). The WAN navigation flag sits at line 208 (R-43). Navigation tabs render in `base.html` (lines 66 and 79, R-44 and R-45).
- The nested guard sets `MAX_CHILDREN = 5` (R-35). It counts modules and directories and excludes `__init__.py` (R-36). The baseline holds 33 entries and no entry for `portals` (R-37). Direct children: `portals` 5 (R-38), `src/mist/access` 3 (R-39), `src/mist/resources` 5 (R-40).
- Journal precedent: the upgrade portal action repository stores actions in `upgrade_run_actions` (R-53), with class `ActionRepository` (R-54). It keeps no expiry index (R-55). Its transactions scope to the action collection (`repository.py` line 162).
- Audit precedent: the upgrade audit logger writes to `audit_logs` (R-56).
- Cloud sign-in precedent: the upgrade portal environment token handler (R-57) and default cloud login (R-58).
- Redis writers ingest webhook events (R-50 to R-52). The dashboard checks Redis health (R-49). No guest data uses Redis (D-12).
- Compose defines services `misthelper`, `misthelper-arangodb`, and `misthelper-redis` (R-25 to R-28). The named volume `misthelper-arangodb-data` is defined at line 347 (R-29).
- Container wrapper and deployment guide exist (R-30, R-31).
- Python 3.15 is required by `pyproject.toml` line 23 (R-81), the copilot instructions line 20 (R-04), and the constitution line 278 (R-15).
- Pins: `mistapi` 0.64.1 (R-77), `python-arango` 8.3.7 (R-78), `structlog` 26.1.0 (R-79), and `playwright` 1.65.2 (R-80).

## 6. Mist API evidence

- The OpenAPI 3.1 YAML defines site guest operations at lines 32320 (list), 32351 (count), 32423 (search), 32468 (delete), 32487 (get), and 32509 (update). It defines organization operations at 10096, 10119, 10153, 10202, 10222, and 10246.
- Site guest schema: `minutes` maximum 259200 (R-68) and minimum 0 (R-69). `name` is read-only at line 81002 (R-70). `wlan_id` is read-only at line 81020 (R-71).
- Organization guest schema `guest_org` starts at line 81023 (R-72). It lists `wlan_id` as required at line 81122 (R-73). The organization list response wraps records in `guests` (line 81125, description "List of guest authorization records").
- SDK signatures: the site list takes `wlan_id` as an optional argument (`sites/guests.py` lines 17 and 18, R-94). The organization list takes only the session and organization identifier (`orgs/guests.py` line 17, R-99).
- The SDK does not raise on HTTP errors. `_request_with_retry` returns an `APIResponse` (`__api_request.py` lines 203 and 258, R-103). The response records `status_code` at `__api_response.py` line 48 (R-105). The retry limit is 3 (R-102).
- Open gap G5: the site list response shape, WLAN binding on grant, and revoke semantics were not confirmed against a live tenant (analysis U-3).

## 7. Decisions

Each decision lists alternatives, the chosen option, the reason, the risk, and the recommended option. D-11 and D-13 require a human decision under brief section 6.

### D-1 Guest Access tab in the existing portal

- Alternatives: (a) a new service on a new port. (b) Menu operations only. (c) A tab in the existing portal, hidden behind `GUEST_ACCESS_ENABLED`.
- Chosen: (c).
- Reason: No new service or port is added (SC-007). The tab reuses the IP allowlist, CSRF protection, and the navigation pattern (R-43 to R-45).
- Risk: The portal has no user authentication (R-46). Writes wait for D-11.
- Recommended: (c).

### D-2 Convert the legacy module into a package

- Alternatives: (a) add `guest_workflows/` under `portals`. This adds a sixth child and fails the guard (R-38, R-35). (b) Place all code under `src/mist/access/guests/`. (c) Convert the module into a package.
- Chosen: (c).
- Reason: `portals` keeps five children. Presentation code sits beside the read model.
- Risk: The import path changes. T006 updates the test to the module path. `__init__.py` exports only the blueprint factory.
- Recommended: (c).

### D-3 Site-scope mistapi methods only

- Alternatives: (a) organization-scope writes with a fallback, as the source does (R-127). (b) Site-scope writes only. (c) Choose the scope per request.
- Chosen: (b).
- Reason: The source changes scope after an error. The organization schema lists `wlan_id` as required (R-73), but the site schema marks it read-only (R-71). The site grant path is unproven until G5 closes.
- Risk: Grants stay blocked if G5 fails. A later decision covers organization scope.
- Recommended: (b).

### D-4 Revoke with PUT minutes 0, a WLAN check, and a read-back

- Alternatives: (a) DELETE, which the source guide says does not remove access (R-118). (b) PUT minutes 0 with a WLAN check and a GET read-back. (c) PUT only, which the source does (R-128) and which reports success on 2xx.
- Chosen: (b).
- Reason: A 2xx response alone does not prove that access ended. The read-back shows the actual state (FR-013).
- Risk: The effect of minutes 0 is unverified until G5 closes.
- Recommended: (b).

### D-5 Duration from 1 to 259200 minutes

- Alternatives: (a) the source UI maximum of 2628000 (R-131). (b) The schema maximum of 259200 (R-68). (c) No maximum.
- Chosen: (b).
- Reason: The Mist schema sets the maximum at 259200 minutes. The source maximum is 2368800 minutes larger.
- Risk: The source documents promise five years (R-116). Operators lose that range. The operator guide states the change.
- Recommended: (b).

### D-6 Send only writable site fields

- Alternatives: (a) send the full record, as the source does. (b) Send an allowlist of writable fields. (c) Send `minutes` only.
- Chosen: (b).
- Reason: The site schema marks `name` and `wlan_id` read-only (R-70, R-71). The source overwrites `field4` with the token name (lines 550 to 552). MistHelper never writes `field4`.
- Risk: Name changes are unavailable. The form omits the control.
- Recommended: (b).

### D-7 Typed words bound to reviewed content

- Alternatives: (a) a confirmation dialog. The source has none (R-134). (b) One generic word for all changes. (c) Operation-specific typed words GRANT, CHANGE, EXTEND, REVOKE, and IMPORT, bound to a reviewed-content hash.
- Chosen: (c).
- Reason: Constitution III requires typed confirmation for changes to the Mist cloud (constitution line 113). The hash blocks any change made after review.
- Risk: Operators must type each word. TC-047 tests the browser flow.
- Recommended: (c).

### D-8 CSV limits

- Alternatives: (a) the source behavior, which defaults minutes to 1440 silently (R-123). (b) No limits. (c) Fixed limits: 262144 bytes, 500 rows, UTF-8, an exact header allowlist, sequential writes, and no minutes default.
- Chosen: (c).
- Reason: The byte and row limits bound memory and the Mist call count. The 500-row cap keeps the Mist request count near 1000 for each import. The minutes rule prevents silent duration changes.
- Risk: Large lists need several imports.
- Recommended: (c).

### D-9 ArangoDB journal and audit collections

- Alternatives: (a) Redis, which D-12 rejects. (b) A JSON file under `data/`, which has no read-back or lock. (c) ArangoDB collections `guest_authorization_actions` and `audit_logs`.
- Chosen: (c).
- Reason: The upgrade portal already records actions this way (R-53 to R-56). `python-arango` is pinned (R-78). The constitution requires verified persistence and fail-closed behavior (lines 315 to 317). The journal keeps the full normalized MAC address for reconciliation. Logs and audit events never contain it (FR-026).
- Risk: An ArangoDB outage blocks writes. This behavior is intended.
- Recommended: (c).

### D-10 No automatic expiry and a named-volume backup unit

- Alternatives: (a) a TTL index on the journal. (b) A manual purge. (c) No automatic expiry, with a backup of the named volume.
- Chosen: (c).
- Reason: The journal is the only local evidence of Mist changes. The upgrade portal keeps no expiry index (R-55). The named volume `misthelper-arangodb-data` is defined at `compose.yml` lines 347 and 348 (R-29).
- Risk: The journal grows. Each release reviews retention.
- Recommended: (c).

### D-11 Authenticated operator on every guest route (HUMAN-DECISION-REQUIRED)

- Alternatives: (a) cloud sign-in with two-factor authentication, following the upgrade portal login pattern (R-57, R-58). This depends on issue #4936. (b) An environment token. It gives no operator attribution. (c) The IP allowlist only, which is the current posture (R-46).
- Chosen: (a), once approved. Until approval, all guest writes stay disabled.
- Reason: Audit events need operator attribution for each write. The IP allowlist does not identify an operator.
- Risk: The path depends on issue #4936. Credential policy needs maintainer approval.
- Recommended: (a).

### D-12 No Redis for guest data

- Alternatives: (a) Redis keys with a TTL. (b) Redis streams for the journal. (c) ArangoDB only.
- Chosen: (c).
- Reason: The journal needs durable read-back and compare-and-swap (D-9). Redis writers serve webhook ingestion only (R-50 to R-52).
- Risk: None for version 1.
- Recommended: (c).

### D-13 Clean-room reimplementation (HUMAN-DECISION-REQUIRED)

- Alternatives: (a) copy source expression with attribution. (b) Reimplement from the Mist schema and documented behavior. (c) Relicense the source.
- Chosen: (b), until a maintainer approves (a) or (c).
- Reason: Both repositories use CC BY-NC-SA 4.0 (R-75 and R-113). ShareAlike applies to any copy. Licensing text is a legal decision.
- Risk: Reimplementation takes longer. Behavior drift is possible, and contract tests cover the expected behavior.
- Recommended: (b).

### D-14 No new service, database, or published port

- Alternatives: (a) a new container on a new port. (b) A new database. (c) The existing portal and database.
- Chosen: (c).
- Reason: SC-007. The compose file already defines the portal and database services (R-25 to R-28).
- Risk: The feature shares its failure domain with the portal. The team accepts this risk.
- Recommended: (c).

### D-15 Masked MAC addresses in tables

- Alternatives: (a) full MAC addresses in every table, as the source does. (b) Masked addresses in tables, and the full address in the review panel for one row. (c) A hash only.
- Chosen: (b).
- Reason: Table views expose fewer device identifiers. The review panel still confirms the exact device.
- Risk: Operators compare masked values. The review panel shows the full value.
- Recommended: (b).

### D-16 Writes disabled until gate G5 closes

- Alternatives: (a) enable writes behind the flag. (b) Enable grants only. (c) Keep every write disabled until G5 closes.
- Chosen: (c).
- Reason: WLAN binding, revoke semantics, and the list shape are unverified (section 6).
- Risk: Delivery waits for G5.
- Recommended: (c).

### D-17 Closing keyword in the planning pull request

- Alternatives: (a) `Closes #4231`, which the brief requires. (b) `Refs #4231`, which PR #4290 and the issue comments imply.
- Chosen: (a), as the brief requires.
- Reason: Brief section 4 requires a closing keyword for issue 4231 in the pull request body.
- Risk: The closure conflicts with the issue comments. Analysis U-6 records the conflict for the orchestrator. This decision is not a human decision under brief section 6.
- Recommended: (a), with orchestrator confirmation.

## 8. Remote verification table

Each row lists one check. The `Blob or tree SHA` column holds a blob SHA for files, a tree SHA for directories, and a commit SHA for commits. `none` means the object is absent. `line` 0 means the row checks an object or an absence, not a line. The row count (134) equals the `remote_checks` length in `4231-STATUS.json`.

| ID | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | AGENTS.md writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-02 | AGENTS.md safety section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 157 |
| R-03 | AGENTS.md secrets rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 172 |
| R-04 | Python 3.15 language rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R-05 | Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-06 | Safety in this repository | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 309 |
| R-07 | Containers and ports | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 354 |
| R-08 | Constitution I Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-09 | Constitution II Class-Based Architecture | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R-10 | Constitution III Safety-First | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-11 | Constitution IV Full Deployment Pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R-12 | Constitution V Observability and Logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R-13 | Constitution VI Inline Comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-14 | Constitution VII Action Logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-15 | Constitution technology rule for Python 3.15 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| R-16 | Constitution rule that mistapi is the sole interface | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| R-17 | Constitution owned WebSocket exception | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 283 |
| R-18 | Constitution Podman primary runtime | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 300 |
| R-19 | Constitution Operational Store rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| R-20 | MYPY_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-21 | VULTURE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-22 | PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-23 | INTERROGATE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-24 | STE lint file list | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 44 |
| R-25 | Compose service misthelper | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 53 |
| R-26 | Compose container name misthelper-app | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 81 |
| R-27 | Compose service misthelper-arangodb | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 191 |
| R-28 | Compose service misthelper-redis | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 231 |
| R-29 | Compose named volume misthelper-arangodb-data | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 347 |
| R-30 | Container wrapper script exists | scripts/compose.ps1 | main | d58a2b1065d53ce9ae971a733e09aec3cbbcc6a5 | present | 1 |
| R-31 | Container deployment guide exists | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 1 |
| R-32 | GuestAuthorizationReadModel class | src/interfaces/portals/guest_authorizations.py | main | 7101772d492af0a340b88d3cd3c2e221db9e7d31 | present | 17 |
| R-33 | GuestAuthorizationReadModel.project method | src/interfaces/portals/guest_authorizations.py | main | 7101772d492af0a340b88d3cd3c2e221db9e7d31 | present | 21 |
| R-34 | Read model test file holds five test functions | tests/unit/web_portal/test_guest_authorization_read_model.py | main | 464c999daefa9d77ff451778e5228aa9a9033e38 | present | 12 |
| R-35 | Nested guard MAX_CHILDREN equals 5 | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R-36 | Nested guard _child_count excludes __init__.py | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 117 |
| R-37 | Nested baseline holds 33 entries and no portals entry | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 1 |
| R-38 | src/interfaces/portals holds five children | src/interfaces/portals | main | 7f5ac6778b6a7a78ad7268542bb8de2a9c550926 | present | 0 |
| R-39 | src/mist/access holds three children | src/mist/access | main | 7e9b2c8135cead4c013a128c04d29a0bc2224093 | present | 0 |
| R-40 | src/mist/resources holds five children | src/mist/resources | main | 30dbad9db62800e7f661c7d706c179217a0e43b7 | present | 0 |
| R-41 | Legacy record folder holds five children | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations | main | 70ed0a41b1948a14f2d464dc1acf7cf13a2d0594 | present | 0 |
| R-42 | web_portal/app.py registers blueprints | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 182 |
| R-43 | web_portal/app.py WAN navigation flag | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 208 |
| R-44 | base.html WAN navigation condition | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 66 |
| R-45 | base.html licensing comparison tab | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 79 |
| R-46 | config.py states the portal has no user authentication | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 12 |
| R-47 | config.py configures CSRF | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 297 |
| R-48 | config.py creates CSRFProtect | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 301 |
| R-49 | Dashboard checks Redis health | web_portal/routes/dashboard.py | main | 9a4f0f5398483b3dac56fdbf084d1ebd1554c300 | present | 127 |
| R-50 | Webhook route calls ingest_webhook | web_portal/routes/webhooks.py | main | bd33ba1d2f185fab411631c0b1b91e616b4226e7 | present | 143 |
| R-51 | RedisTimeSeriesWriter class | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 93 |
| R-52 | Redis writer ingest_webhook function | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 410 |
| R-53 | Upgrade action collection upgrade_run_actions | src/interfaces/portals/upgrade_portal/persistence/actions/repository.py | main | fd078d71078c956cbdbab8c9487ad437db3bebb6 | present | 37 |
| R-54 | Upgrade ActionRepository class | src/interfaces/portals/upgrade_portal/persistence/actions/repository.py | main | fd078d71078c956cbdbab8c9487ad437db3bebb6 | present | 92 |
| R-55 | Upgrade action collection has no expiry index | src/interfaces/portals/upgrade_portal/persistence/actions/repository.py | main | fd078d71078c956cbdbab8c9487ad437db3bebb6 | present | 63 |
| R-56 | Upgrade audit logger writes to audit_logs | src/interfaces/portals/upgrade_portal/audit/logger.py | main | f437f4c581001347fad88bad8e4ec2af7dc06a96 | present | 93 |
| R-57 | Upgrade environment token handler | src/interfaces/portals/upgrade_portal/app/routes/auth.py | main | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 284 |
| R-58 | Upgrade default cloud login route | src/interfaces/portals/upgrade_portal/app/routes/auth.py | main | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 304 |
| R-59 | Menu 200 guest handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4112 |
| R-60 | SiteGuestAuthorizationExporter class | src/operations/exporting/export/site_guest_authorization_exporter.py | main | 4d4c500b56ed9932611fe0d7ad837b8af8d03677 | present | 41 |
| R-61 | Operator guide states the browser page has no sign-in form | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 577 |
| R-62 | Operator guide tracks issue #4936 | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 627 |
| R-63 | Endpoint catalog row for the site guest list | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1259 |
| R-64 | OpenAPI 3.1 organization guest list operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10096 |
| R-65 | OpenAPI 3.1 organization guest update operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10246 |
| R-66 | OpenAPI 3.1 site guest list operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32320 |
| R-67 | OpenAPI 3.1 site guest update operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32509 |
| R-68 | OpenAPI 3.1 site minutes maximum 259200 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80995 |
| R-69 | OpenAPI 3.1 site minutes minimum 0 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80996 |
| R-70 | OpenAPI 3.1 site name is read-only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81002 |
| R-71 | OpenAPI 3.1 site wlan_id is read-only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81020 |
| R-72 | OpenAPI 3.1 organization guest_org schema | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81023 |
| R-73 | OpenAPI 3.1 organization wlan_id is required | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81122 |
| R-74 | OpenAPI 3.0 JSON twin exists | documentation/mist-api-openapi3json.json | main | 8efb60f30b65b8044f86120e5a3ce8f6c306e5d4 | present | 1 |
| R-75 | MistHelper license is CC BY-NC-SA 4.0 | LICENSE | main | d115eeab9dbd6f61d0233b0894d3f8309bb976e8 | present | 1 |
| R-76 | Environment example names MIST_API_TOKEN | deploy/.env.example | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 11 |
| R-77 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-78 | requirements.txt pins python-arango 8.3.7 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 197 |
| R-79 | requirements.txt pins structlog 26.1.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 249 |
| R-80 | requirements-dev.txt pins playwright 1.65.2 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 272 |
| R-81 | pyproject.toml requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-82 | Legacy spec.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/spec.md | main | c54db8de9e10647e1936731946135566fca8faf5 | present | 1 |
| R-83 | Legacy plan.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/plan.md | main | af27f93ce43873f6e6e8e3b7f0630192a529abf2 | present | 1 |
| R-84 | Legacy tasks.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/tasks.md | main | 98ac4d983661f8434190d23611281a7a2cac750c | present | 1 |
| R-85 | Legacy design/research.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/research.md | main | fcbbf71c1cbc2f223ee3bba5e2932a967793c540 | present | 1 |
| R-86 | Legacy design/data-model.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/data-model.md | main | e1224b5e1b4901b66a7a2f6acc6d1841901f7ecb | present | 1 |
| R-87 | Legacy design/quickstart.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/quickstart.md | main | 8030a8172b88a35ca6175f2d8dcbf86a887feb08 | present | 1 |
| R-88 | Legacy design/contracts/mist-api.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/contracts/mist-api.md | main | f0efcca2c752a420448ed91f9f70f65dd0e9a683 | present | 1 |
| R-89 | Legacy design/contracts/portal.md exists | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/design/contracts/portal.md | main | 36104f81924dfab56a954f276655f9f11228f13b | present | 1 |
| R-90 | Legacy checklists/requirements.md exists at the feature root | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/checklists/requirements.md | main | d6051f435188f6cda6efd0d1fade152c87122318 | present | 1 |
| R-91 | Legacy analysis.md is absent | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/analysis.md | main | none | absent | 0 |
| R-92 | Checkpoint commit 20cf234e2 is absent | commit 20cf234e2 | 20cf234e2 | none | absent | 0 |
| R-93 | Commit 1e9b280dd exists | commit 1e9b280dd | 1e9b280dd | 1e9b280ddb0285048e515cb837f6802ac38ceb0e | present | 0 |
| R-94 | Site guest list accepts a wlan_id filter | .venv\Lib\site-packages\mistapi\api\v1\sites\guests.py | local-venv | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 17 |
| R-95 | searchSiteGuestAuthorization function | .venv\Lib\site-packages\mistapi\api\v1\sites\guests.py | local-venv | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 148 |
| R-96 | getSiteGuestAuthorization function | .venv\Lib\site-packages\mistapi\api\v1\sites\guests.py | local-venv | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 224 |
| R-97 | deleteSiteGuestAuthorization function | .venv\Lib\site-packages\mistapi\api\v1\sites\guests.py | local-venv | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 252 |
| R-98 | updateSiteGuestAuthorization function | .venv\Lib\site-packages\mistapi\api\v1\sites\guests.py | local-venv | 708f633d8a8a038117ebad17f391ee51a8d093ae | present | 280 |
| R-99 | Organization guest list has no WLAN parameter | .venv\Lib\site-packages\mistapi\api\v1\orgs\guests.py | local-venv | 398490dbcefef76c86ab6750af51bd21e6d98cb2 | present | 17 |
| R-100 | updateOrgGuestAuthorization function | .venv\Lib\site-packages\mistapi\api\v1\orgs\guests.py | local-venv | 398490dbcefef76c86ab6750af51bd21e6d98cb2 | present | 225 |
| R-101 | deleteOrgGuestAuthorization function | .venv\Lib\site-packages\mistapi\api\v1\orgs\guests.py | local-venv | 398490dbcefef76c86ab6750af51bd21e6d98cb2 | present | 197 |
| R-102 | Retry limit _MAX_429_RETRIES equals 3 | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 59 |
| R-103 | _request_with_retry returns an APIResponse | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 203 |
| R-104 | mist_put sends HTTP PUT | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 303 |
| R-105 | APIResponse records status_code | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 48 |
| R-106 | listSiteWirelessClientsStats function | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | local-venv | bce91c2c8ff2c793190c2afb3548ae83e15322c2 | present | 960 |
| R-107 | listSiteWlans function | .venv\Lib\site-packages\mistapi\api\v1\sites\wlans.py | local-venv | 45f2572e4e3b23ee8e4df9a7a061abef2423dcd4 | present | 17 |
| R-108 | listOrgWlans function | .venv\Lib\site-packages\mistapi\api\v1\orgs\wlans.py | local-venv | a48dee04d758e68108cbf19d2f9a597c3ac99e8b | present | 17 |
| R-109 | listOrgSites function | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 17 |
| R-110 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| R-111 | Source pins mistapi 0.64.0 | requirements.txt | 0213240cb9edfa237f763acd156b90a6049363cb | e3c62ee4fd6bd48c8cb94af0c8d6d0fdb5df01a7 | present | 2 |
| R-112 | Source README names MIST_APITOKEN in .env | README.md | 0213240cb9edfa237f763acd156b90a6049363cb | f92e7f65b8215d30cade46c58046ff0367514b9d | present | 25 |
| R-113 | Source license is CC BY-NC-SA 4.0 | LICENSE | 0213240cb9edfa237f763acd156b90a6049363cb | bbea5fed78ca98720c6590d4151de423714ea6de | present | 1 |
| R-114 | Source compose service mistguestauth | docker-compose.yml | 0213240cb9edfa237f763acd156b90a6049363cb | 7a9206c460da9cda84f708c3e8f54694840aa4bb | present | 6 |
| R-115 | Source compose port defaults to 5000 | docker-compose.yml | 0213240cb9edfa237f763acd156b90a6049363cb | 7a9206c460da9cda84f708c3e8f54694840aa4bb | present | 11 |
| R-116 | Source guide claims a five-year maximum | docs/guide.md | 0213240cb9edfa237f763acd156b90a6049363cb | 439dfae00662a1ba2297aa45123e14570fa66f7a | present | 27 |
| R-117 | Source guide lists read-write WLAN and guest permissions | docs/guide.md | 0213240cb9edfa237f763acd156b90a6049363cb | 439dfae00662a1ba2297aa45123e14570fa66f7a | present | 170 |
| R-118 | Source guide says DELETE does not remove guests | docs/guide.md | 0213240cb9edfa237f763acd156b90a6049363cb | 439dfae00662a1ba2297aa45123e14570fa66f7a | present | 238 |
| R-119 | Source authorize route uses POST | app.py | 0213240cb9edfa237f763acd156b90a6049363cb | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | present | 171 |
| R-120 | Source authorize defaults to 1440 minutes | app.py | 0213240cb9edfa237f763acd156b90a6049363cb | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | present | 195 |
| R-121 | Source deauthorize route uses DELETE | app.py | 0213240cb9edfa237f763acd156b90a6049363cb | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | present | 210 |
| R-122 | Source update route uses PUT | app.py | 0213240cb9edfa237f763acd156b90a6049363cb | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | present | 234 |
| R-123 | Source bulk import defaults to 1440 minutes | app.py | 0213240cb9edfa237f763acd156b90a6049363cb | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | present | 407 |
| R-124 | Source get_wlan_guests lists site guests | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 399 |
| R-125 | Source falls back to the organization-wide guest list | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 423 |
| R-126 | Source authorize_guest function | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 487 |
| R-127 | Source authorize writes at organization scope | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 592 |
| R-128 | Source deauthorize PUT sends minutes 0 | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 652 |
| R-129 | Source deauthorize checks for a 2xx status | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 659 |
| R-130 | Source client search calls listSiteWirelessClientsStats | mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 797 |
| R-131 | Source UI allows 2628000 minutes | templates/index.html | 0213240cb9edfa237f763acd156b90a6049363cb | ef954198c1768b4e2d57cddd3aeaf93c6caddf95 | present | 736 |
| R-132 | Source UI defaults minutes to 1440 silently | templates/index.html | 0213240cb9edfa237f763acd156b90a6049363cb | ef954198c1768b4e2d57cddd3aeaf93c6caddf95 | present | 1409 |
| R-133 | Source UI sends DELETE | templates/index.html | 0213240cb9edfa237f763acd156b90a6049363cb | ef954198c1768b4e2d57cddd3aeaf93c6caddf95 | present | 1673 |
| R-134 | Source UI has no confirm call | templates/index.html | 0213240cb9edfa237f763acd156b90a6049363cb | ef954198c1768b4e2d57cddd3aeaf93c6caddf95 | absent | 0 |

## 9. Sources

- Repository files: MistHelper remote main and local views of matching blobs (section 8, R-01 to R-90 and R-93).
- Installed SDK: `.venv\Lib\site-packages\mistapi`, read with views and `git hash-object --no-filters` (R-94 to R-110).
- Pinned source: remote blobs at `0213240cb9edfa237f763acd156b90a6049363cb` (R-111 to R-134).
- GitHub reads: `gh issue view`, `gh issue list`, `gh api` tree and blob calls, all read-only.
- No `web_fetch` call was made. No upstream URL is cited.

## 10. Unverified

- U-8: Template and site-group WLAN inheritance. The source resolves it in `mist_connection.py` lines 245 to 283. Mist behavior is unverified.
- U-9: The projection test case total of 22 (L-25).
- U-10: GitHub license metadata for the source (L-26).
- U-11: Commit `1e9b280dd` tree contents (L-24).
- U-12: The local source checkout differs from its remote. Only remote blobs support source claims.
- G5 items: the site list response shape, WLAN binding on grant, and the effect of minutes 0 on revoke. The team confirms these with an approved nonproduction run (analysis U-3).
