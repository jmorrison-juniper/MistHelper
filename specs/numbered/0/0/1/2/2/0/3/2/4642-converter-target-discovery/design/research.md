# Research: Read-only Mist target discovery for converter proposals

Issue: #4642. Record: `specs\numbered\0\0\1\2\2\0\3\2\4642-converter-target-discovery`.

## Method

- The issue text and its comments came from `gh issue view 4642`. The comment named "Task-map correction" dates 2026-11-09. It names PR #4596 as open.
- A linked-PR search for "4642" returned no pull requests. PR #4596 is cited by the issue. It was read with `gh pr view 4596`. Its state is MERGED, merged 2026-11-13.
- Each claim cites `main`. The GitHub API returns the tree blob SHA and the decoded line number. Local files match `main` by git blob SHA before their line numbers are used.
- Files in `.venv\Lib\site-packages\mistapi` are read-only evidence. Their git-style blob SHA is computed locally. Their ref is `local-venv`.
- No legacy record exists. A glob and a tree search found no folder whose name starts with `4642-`.
- No skill was loaded. The scope is Mist cloud reads and portal session state. No listed skill matches that scope.
- No web source was fetched. This record holds no URL.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. Evidence IDs (R##) point to the remote verification table.

### D-1 Place the Mist check client in `src/mist/access/targets/`

- Alternatives: (a) A new package under the converter root. Rejected, because the root already holds five children (R75) and a sixth child breaks R30. (b) New methods on `ConverterRoutes`. Rejected, because the class already holds five members (R15). (c) `src/mist/resources/org/`. Rejected, because that folder already holds five children (R74). (d) `src/mist/access/targets/`. Chosen, because the new package holds four children (R73 shows `src/mist/access` holds four).
- Reason: The client calls Mist through mistapi only. The package sits beside the existing access modules (R73).
- Risk: The label "access" is broad. A reviewer can move the package before merge. A move needs no shim.

### D-2 Put the route handlers in `routes.py` as a new class

- Alternatives: (a) Add handlers to `ConverterRoutes`. Rejected, because the class holds five members (R15). (b) A new blueprint module. Rejected, because it adds a child to the converter root (R30). (c) Chosen: a new class `ConverterDiscoveryRoutes` in `routes.py`.
- Reason: Route handlers belong to the interface layer. The blueprint already registers the converter routes (R16).
- Risk: `routes.py` reaches the limit of five top-level names: `logger` and four classes. Issues #4636 and #4641 also edit `routes.py`. Merge this issue after both.

### D-3 Use `identity.current_session()` as the existing credential and session service

- Alternatives: (a) `MistSessionInitializer`. Rejected, because it reads the CLI entry point context (R27) and holds no browser operator. (b) `identity.session_privileges()`. Rejected, because it returns a list cached at sign-in or None (R26), so membership can go stale. (c) A converter token reader. Rejected, because it duplicates the credential path and conflicts with the browser-storage rule. (d) Chosen: `identity.current_session()`. It returns the operator record (R25 shows the None path). The record holds `cloud_session`, a reference to the mistapi object (R24).
- Reason: The parent issue #4224 requires the existing credential configuration. The identity module checks the signed session (R25) and holds the operator record (R24).
- Risk: Discovery answers `no_session` until the shared portal supplies a session (#4648). The converter then imports the upgrade portal runtime. The change adds that cross-portal import. Review must accept it.

### D-4 Use four states, reasons, and HTTP 200 for every check outcome

- Alternatives: (a) HTTP 403 for denied and HTTP 503 for unavailable. Rejected, because the page cannot tell a request error from a check outcome. (b) Chosen: HTTP 200 with `state`, `reason`, and `items`. HTTP 400 appears only for an invalid `org_id`, before any SDK call.
- Reason: The page renders each outcome the same way. `items` is null for every state except verified (FR-003).
- Risk: A client that reads only the HTTP status misreads the result. The contract file `design/contracts/discovery-http.md` states the rule.
- The label "Not checked" is the page state before the first check. The API never returns it. The parity map names five states (R04). The issue names four states. This record keeps four API states and one page label.

### D-5 Map each HTTP status to one state

- Mapping: 401 and 403 give denied (`unauthorized`, `forbidden`). 404 gives failed (`not_found`). Other 4xx give failed (`client_error`). 500 and other 5xx give failed (`server_error`). 429, 502, 503, and 504 give unavailable (`rate_limited` or `service_unavailable`). No status gives unavailable (`no_response`). An unexpected exception gives failed (`exception`).
- Alternatives: (a) 429 as failed. Rejected, because the operator should retry later, which matches unavailable (R04). (b) 500 as unavailable. Rejected, because a 500 means that Mist failed a served request.
- Risk: The SDK returns no status for a connection failure and for some generic exceptions (U5). The mapping treats both as unavailable. That split is unverified.

### D-6 Prove completeness before a list is verified

- Rule: A list is verified only when the last page has no `next` value. The last page must also hold fewer than 1000 rows, or the response must carry `X-Page-Total`. A full last page without that header gives failed (`completion_unproven`).
- Alternatives: (a) Trust a missing `next` value alone. Rejected, because a missing header can hide rows (U1). (b) Chosen: the proof rule above.
- Risk: If Mist omits `X-Page-Total`, every full list fails. The failure is safe and visible. U1 records the live check that remains open.

### D-7 Read later pages with `mistapi.get_next` and fixed bounds

- Rule: The first page uses an explicit call with `limit` 1000 and `page` 1. Later pages use `mistapi.get_next` (R68 shows it calls `mist_get` only when `next` is set). The page size 1000 matches the repository precedent (R28). The bound is 50 pages.
- Alternatives: (a) Manual `page` increments on each call. Rejected, because the repository already uses the helper (R29). (b) `mistapi.get_all`. Rejected, because the helper hides page status and gives no completion proof.
- Risk: The 50-page bound is a design choice. An organization above 50,000 rows gives failed (`page_limit_exceeded`). A later issue can raise the bound with evidence.

### D-8 Use the SDK retry for rate limits only

- Rule: The SDK retries a 429 up to three times and honors `Retry-After` (R70 shows `_MAX_429_RETRIES` and `_DEFAULT_RETRY_AFTER`). The converter adds no retry loop. A final 429 maps to unavailable (D-5).
- Alternatives: (a) A converter backoff. Rejected, because it duplicates SDK logic. (b) Disable SDK retries. Rejected, because a read repeats safely and the retry helps the operator.
- Risk: Three waits of 5, 10, and 20 seconds can delay a check by about 35 seconds. The page shows a running state during the check.

### D-9 Read membership on every check

- Rule: Each site check and gateway check calls `getSelf` first (R65). It reads the privilege list in that response. An organization without a matching `org_id` gives denied (`not_member`).
- Alternatives: The cached session privileges (D-3, R26). Rejected, because they can be None and can be stale.
- Risk: Each check makes one extra read. The cost is acceptable for an interactive page.

### D-10 Place the discovery tests in the converter integration folder

- Alternatives: (a) `tests/contract/cisco_config_converter/`. Rejected, because `tests/contract` already holds 17 children (R76), and the constitution forbids a new child in that parent (R31). (b) `tests/e2e/cisco_config_converter/`. Rejected, because `tests/e2e` holds five children (R77). (c) Chosen: `tests/integration/web_portal/cisco_config_converter/test_discovery.py`. The folder holds two children now (R78).
- This choice follows the state-test placement in issue #4636.
- Risk: The folder reaches five children after #4636 and #4641 land. A later child breaks the rule.

### D-11 Put the panel in the existing page and emit one event

- Rule: The discovery section and its script stay in the converter presentation folder (R19 and R20 show the current page). A target change dispatches the `cisco-target-changed` event on `document`. Issue #4641 owns the listener and the review reset (R21 shows the current reset method).
- Alternatives: (a) A new page and route. Rejected, because it adds a second surface before shared registration (#4648). (b) A direct call to the review reset. Rejected, because it couples this issue to code that #4641 owns.
- Risk: Until #4641 lands, no listener handles the event. A target change then leaves the review state unchanged. The merge order closes that gap.

### D-12 Use three read calls only

- Rule: The calls are `getSelf`, `listOrgSites`, and `getOrgInventory` with `type` set to `gateway`. Gateway assignment comes from the `site_id` field of each item (R62). The `unassigned` filter (R55) is not used.
- Alternatives: (a) Two calls with `unassigned` true and false. Rejected, because two lists can drift between reads. (b) `searchOrgInventory`. Rejected, because it adds a second read family with different arguments.
- Risk: The meaning of an empty `site_id` is unverified (U2).

### D-13 Use stable identities and flag duplicate names

- Rule: Site selection uses the site `id` (R63). Gateway selection uses the device `id` (R61). Names are display text (R64). A name that matches another site after trimming spaces sets `duplicate_name` to true (R12 gives the rule).
- Alternatives: Use the name as the key. Rejected, because names repeat (R12).
- Risk: A hostname can match a site. The page shows such a match as a suggestion only. The page never selects by hostname.

### Parity map deviations

- The parity map names `tests/contract/cisco_config_converter/test_discovery.py` for T019 (R01) and `routes.py` for T020 (R02). This record changes three paths: the client goes to `src/mist/access/targets/` (D-1), the handlers stay in `routes.py` as a new class (D-2), and the tests go to the integration folder (D-10). Each change follows a constitution rule.

## Remote verification table

Rows R01 to R94 match the `remote_checks` array in `_meta\4642-STATUS.json` one for one. A row holds one check. The ref `main` means the GitHub tree. The ref `local-venv` means a file in `.venv`. For commit rows, the blob SHA holds the commit SHA. For absent rows, the blob SHA states the absence.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | T019 names the discovery tests and the contract test path | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 74 |
| R02 | T020 names routes.py and the existing credential or session service | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 75 |
| R03 | C19 keeps the no-credentials preview available | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 103 |
| R04 | C20 distinguishes unavailable, denied, failed, pending, and verified states | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 104 |
| R05 | C21 uses stable IDs and separates empty inventory from a failed lookup | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 105 |
| R06 | Every SDK call supplies mist_session first | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 19 |
| R07 | List calls use explicit limit and page when available | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 20 |
| R08 | The orgs.sites row names listOrgSites | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 26 |
| R09 | The orgs.inventory row names getOrgInventory with type, site_id, or unassigned | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 28 |
| R10 | Discovery states stay different: unavailable, denied, failed, pending, stale, and verified | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 110 |
| R11 | Lists paginate fully before a result is final | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 111 |
| R12 | Duplicate names need explicit conflict resolution | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 114 |
| R13 | No preview or lookup may create objects | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 115 |
| R14 | The issue comment says PR 4596 is open and behind main, but its merged artifact is on main | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | stale | 0 |
| R15 | ConverterRoutes holds five members: blueprint, page, preview, review, and export | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 45 |
| R16 | ConverterRoutes.blueprint registers the offline routes | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 61 |
| R17 | models.py holds five classes, and the last is ReviewState | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 84 |
| R18 | IOSDnsConverter performs offline DNS conversion | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R19 | The converter page section carries data-testid cisco-converter | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 4 |
| R20 | CiscoProposalPage owns the preview state | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 2 |
| R21 | reset() clears the proposal and disables review and export | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 19 |
| R22 | The integration client fixture mounts only the converter blueprint | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 19 |
| R23 | The browser smoke class TestCiscoOfflinePreview exists | tests/e2e/web_portal/test_portal_smoke.py | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 23 |
| R24 | The cloud_session field holds a reference to the mistapi object | src/interfaces/portals/upgrade_portal/runtime/identity.py | main | 07098e4fb4510c295f385c037ef5230ec6509bf0 | present | 488 |
| R25 | current_session returns None when the signed session holds no owner key | src/interfaces/portals/upgrade_portal/runtime/identity.py | main | 07098e4fb4510c295f385c037ef5230ec6509bf0 | present | 776 |
| R26 | session_privileges returns a privilege list cached on the cloud session, or None | src/interfaces/portals/upgrade_portal/runtime/identity.py | main | 07098e4fb4510c295f385c037ef5230ec6509bf0 | present | 913 |
| R27 | MistSessionInitializer reads the CLI entry point context | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 158 |
| R28 | The upgrade portal sets MAX_PAGE_LIMIT to 1000 | src/interfaces/portals/upgrade_portal/capture/devices.py | main | 82515c6dc619fbc1d7aad50ee8ea7607840c18bd | present | 59 |
| R29 | The upgrade portal walks later pages with mistapi.get_next | src/interfaces/portals/upgrade_portal/capture/devices.py | main | 82515c6dc619fbc1d7aad50ee8ea7607840c18bd | present | 354 |
| R30 | Constitution: each new hierarchy level holds five children or fewer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| R31 | Constitution: a feature adds no direct child to a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 43 |
| R32 | Constitution: no direct HTTP request to a Mist REST endpoint when mistapi works | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 281 |
| R33 | Constitution Principle III: safety-first input and destructive confirmation | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R34 | Constitution Principle IV: full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R35 | Constitution Principle V: ASCII-only log output | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 184 |
| R36 | Constitution Principle VI: inline comments on each executable line | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R37 | Constitution Principle VII: action logging before and after each action | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R38 | Constitution: test containers join the compose group | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 302 |
| R39 | Constitution: product outputs stay in the data directory | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 326 |
| R40 | Repository guide: new Spec Kit records use the managed roots | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R41 | Repository guide: each structural directory holds five children or fewer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| R42 | Repository guide: a new API client test module needs HTTP 4xx and 5xx tests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| R43 | AGENTS.md: an instruction holds 20 words or fewer, and a description holds 25 words or fewer | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| R44 | AGENTS.md: each executable line of generated code carries an inline comment | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 99 |
| R45 | The changelog guide names issue fragments issue-number-slug | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R46 | README.md holds no converter text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| R47 | spec-route.ps1 sets the route base to 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R48 | The nested-package guard sets MAX_CHILDREN to 5 | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R49 | The SDK compatibility test detects keyword expansion in calls | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 443 |
| R50 | requirements.txt pins mistapi to 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R51 | requirements.txt pins Flask to 3.1.3 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 49 |
| R52 | The getSelf operation exists at GET /api/v1/self | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25490 |
| R53 | The listOrgSites operation exists at GET /api/v1/orgs/{org_id}/sites | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20022 |
| R54 | The getOrgInventory operation exists at GET /api/v1/orgs/{org_id}/inventory | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10660 |
| R55 | The inventory query parameter unassigned exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10724 |
| R56 | The inventory query parameter type lists ap, gateway, and switch | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10684 |
| R57 | The shared query parameter limit defaults to 100 with minimum 0 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59742 |
| R58 | The shared query parameter page defaults to 1 with minimum 1 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59923 |
| R59 | The admin_privilege schema defines org_id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68164 |
| R60 | The admin_privilege schema defines scope | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68179 |
| R61 | The inventory item schema defines id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 82177 |
| R62 | The inventory item schema defines site_id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 82210 |
| R63 | The site item schema defines id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 100539 |
| R64 | The site item schema defines name | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 100548 |
| R65 | The getSelf function accepts mist_session only | .venv\Lib\site-packages\mistapi\api\v1\self\self.py | local-venv | 9a1c323fb1045478d923ebcb30436655c851a6e2 | present | 17 |
| R66 | The listOrgSites function accepts mist_session, org_id, limit, and page | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 17 |
| R67 | The getOrgInventory function accepts type, site_id, unassigned, limit, and page | .venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py | local-venv | 4632461c7eef0317f7c7810f018a6cc7b305f4a2 | present | 17 |
| R68 | The get_next function calls mist_get only when response.next is set | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 33 |
| R69 | APIResponse reads next from the response data | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 72 |
| R70 | _MAX_429_RETRIES is 3 and _DEFAULT_RETRY_AFTER is 5 | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 59 |
| R71 | The request loop returns APIResponse and does not raise for HTTP error statuses | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 258 |
| R72 | The installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| R73 | src/mist/access exists with four children | src/mist/access | main | 7e9b2c8135cead4c013a128c04d29a0bc2224093 | present | 0 |
| R74 | src/mist/resources/org holds five children | src/mist/resources/org | main | 094a9ac97e3e5ef51617a87ebc07a7bafb55fdd8 | present | 0 |
| R75 | The converter root holds five children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R76 | tests/contract holds seventeen children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| R77 | tests/e2e holds five children | tests/e2e | main | 828f24a6106147d9263b550da13acfaa4866b3bf | present | 0 |
| R78 | The converter test folder holds two children | tests/integration/web_portal/cisco_config_converter | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| R79 | The path src/mist/access/targets is absent | src/mist/access/targets | main | none (absent on main) | absent | 0 |
| R80 | The discovery test module is absent | tests/integration/web_portal/cisco_config_converter/test_discovery.py | main | none (absent on main) | absent | 0 |
| R81 | The parity T019 contract folder is absent | tests/contract/cisco_config_converter | main | none (absent on main) | absent | 0 |
| R82 | The changelog fragment for issue 4642 is absent | changelog.d/issue-4642-converter-target-discovery.md | main | none (absent on main) | absent | 0 |
| R83 | The record folder is absent | specs/numbered/0/0/1/2/2/0/3/2/4642-converter-target-discovery | main | none (absent on main) | absent | 0 |
| R84 | Local HEAD f03c6c9b equals the main head | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R85 | Commit b4d61b84 cited by the issue comment exists | commit b4d61b84b5a7e11864bde42322da4d724308b7b4 | main | b4d61b84b5a7e11864bde42322da4d724308b7b4 | present | 0 |
| R86 | Commit 7f024aab is the merged PR 4596 head and exists | commit 7f024aab89e5e71d8f0a1cf41025ee5ff0a1d533 | main | 7f024aab89e5e71d8f0a1cf41025ee5ff0a1d533 | present | 0 |
| R87 | Constitution Principle II: all functionality lives in semantically named classes, with no wrapper functions | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 93 |
| R88 | Constitution Principle V: new services and modules use structured, machine-parseable log entries | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 193 |
| R89 | The local gates table has the columns Gate, Command, and Expected result. Its rows name the T-LOCAL-GATES commands. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 55 |
| R90 | The Tests row names python -m pytest tests with the changed file | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R91 | The Test quality row points to the analyzer procedure | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| R92 | ci.yml defines MYPY_PATHS at line 93, VULTURE_PATHS at 101, PYDOCSTYLE_PATHS at 104, and INTERROGATE_PATHS at 107 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R93 | The portal gate table names the SDK compatibility check with the test module | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 254 |
| R94 | The portal gate table names the output scan check with its test module | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 255 |

## Sources

- Issue #4642 text, labels, and comment, read with `gh issue view`.
- Prerequisites #4634 and #4641 and parent #4224, read with `gh issue view`. All three are OPEN.
- PR #4596, read with `gh pr view`. State MERGED. The files it added are under the parity folder named in R01.
- Repository files at `main`, read through the GitHub contents and blobs API.
- Local `.venv` files for mistapi 0.64.1, read-only.
- Local repository files whose git blob SHA matches `main`.
- No URL was fetched.

## Unverified

- U1. Live Mist sends `X-Page-Total` on `listOrgSites` and `getOrgInventory`. Reason: the OpenAPI file does not document the header (grep found no match in blob b7fc2bfb). The SDK reads it (R69). This record makes no live request.
- U2. An empty or null `site_id` means unassigned. Reason: the inventory schema at R62 does not state the meaning. The parity contract names `unassigned` as the filter (R09). Issue #4634 must confirm the meaning.
- U3. Live Mist accepts `limit` 1000. Reason: the shared schema at R57 states a default and a minimum only. The repository uses 1000 (R28). No live request is allowed.
- U4. The `admin` schema property list that holds `privileges` was not read in full. Reason: the example at the admin response shows the key. An example is not schema evidence.
- U5. A connection failure and a generic exception produce the same no-status response. Reason: the SDK catches exceptions and returns an APIResponse (R71). The mapping in D-5 treats both as unavailable, so a code defect can look like an outage.
- U6. Every sign-in mode gives a mistapi object in `cloud_session`. Reason: R24 describes the field. The browser-token path was not read in full.
- U7. The live effect of the SDK 429 retry. Reason: no live request is allowed. The timing in D-8 comes from the SDK source only.
- U8. A shared host supplies the operator session to the converter route. Reason: the registration belongs to issue #4648. The converter blueprint holds no shared registration (R15 states the feature-owned design).
