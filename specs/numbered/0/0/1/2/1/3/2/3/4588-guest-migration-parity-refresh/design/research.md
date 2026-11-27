# Research: Refresh guest migration parity planning

Issue: [#4588](https://github.com/jmorrison-juniper/MistHelper/issues/4588). Record: `specs\numbered\0\0\1\2\1\3\2\3\4588-guest-migration-parity-refresh`. Evidence date: 2026-11-26.

## 1. Method and limits

- The run read the brief, `AGENTS.md`, the repository instructions, the constitution, and the four Spec Kit templates. It also read reference record 4920, legacy record 4588, record 4231, and the source files at the pinned commit. No skill was loaded. The issue asks no Podman internals or Juniper device question.
- The run read local target files. Each cited target file has the same Git blob hash as GitHub main.
- The run ran no build, test, linter, formatter, package install, container, or repository script.
- The run made read-only GitHub calls only. It made no comment, label, edit, merge, or branch change.
- The run read the account variable only to set the GitHub host and token. No variable value appears in this record.
- The local source clone is stale. Its HEAD is `61f6a48f`. Source evidence uses GitHub blob reads at the pinned commit `0213240c`.
- The SDK checks read the local `.venv` copy. Third-party packages are outside the repository tree.
- The brief forbids branch commands. The app-managed branch is not checked. See U09.

## 2. Pins and freshness

| Item | Value | Evidence |
| --- | --- | --- |
| Target main | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local checkout is the same commit. | R01, R02 |
| Target baseline of the legacy record | `772fc927761b61dea8beb7f708fbbe78c2a38d86`. Main is 117 commits ahead. | R13 |
| Source main | `0213240cb9edfa237f763acd156b90a6049363cb`. This value matches the issue. | R03 |
| Source local clone | `61f6a48f3a4e87a77069201879f81443d088ef16`. The clone is stale. | R04 |
| Planning PR for the legacy record | PR 4589 merged at `5d444bda23ea50de131d67b6e6fcf37055adfa77`. | R05 |
| Offline projection PR | PR 4279 merged at `1e9b280ddb0285048e515cb837f6802ac38ceb0e`. | R06 |
| Earlier refresh PR | PR 4290 merged on 2026-10-20. | R07 |
| Open shared-file PR | PR 4208 is open. It changes `web_portal/app.py` and `web_portal/templates/base.html`. | R08 |
| Issue states | Issue 4588 is open. Issue 4231 is open. Issue 4278 is open. Issue 4869 is closed. | R09 to R12 |

## 3. Legacy record verification

The legacy record has 13 files on main at `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/`. The local copy of each file matches its blob SHA (R14 to R26). The run read every legacy file. The ledger tests each legacy claim against current evidence.

| ID | Status | Legacy claim and result | Evidence |
| --- | --- | --- | --- |
| L01 | verified | Legacy record files exist on main with matching blob SHAs. | R14 to R26 |
| L02 | verified | The source pin equals GitHub main. | R03 |
| L03 | verified | The source Git tree has 39 blobs, with 32 text files and 7 PNG files. | R68 |
| L04 | verified | The source app defines 13 route handlers. | S01 |
| L05 | verified | The source calls 12 distinct mistapi functions. | S02 |
| L06 | verified | The installed SDK signatures and def lines match for 13 guest functions. | R69, R70 |
| L07 | verified | The checked-in JSON schema version is 2609.1.0. | R54 |
| L08 | verified | The checked-in OpenAPI guest paths and operation IDs match the endpoints. | R54, R55 |
| L09 | verified | The duration schema is an integer from 0 to 259200 with default 1440. | R54 |
| L10 | verified | The schema marks name, mac, wlan_id, and related fields read-only. | R54 |
| L11 | verified | The guest schema has no notify property. | R54 |
| L12 | verified | The site guest PUT body references the guest schema. | R54 |
| L13 | verified | Source presets run from 60 to 525600 minutes. The source maximum is 2628000. | S03 L736 to L747 |
| L14 | verified | The source guide promises a duration of up to five years. | S09 L27 |
| L15 | verified | The source revocation sends PUT with `minutes` set to 0. | S02 L649 to L652 |
| L16 | verified | The source fills `field4` from the API token name. | S02 L550 to L552 |
| L17 | verified | The source sends `notify` when the value is true. | S01 L196, S02 L554 to L555 |
| L18 | verified | The source CSV template has ten headers. | S01 L293 to L303 |
| L19 | verified | The target projection has one class and 22 test cases. | T01, T02 |
| L20 | verified | The target portal registers no guest blueprint. | T03 L200 to L207 |
| L21 | verified | The target navigation has no guest link. | T04 L51 to L78 |
| L22 | verified | The target portal has no user authentication. | T05 L12 to L13 |
| L23 | verified | The target pins mistapi 0.64.1. | T10 L129, R71 |
| L24 | verified | The source pins mistapi 0.64.0. | S08 L2 |
| L25 | verified | The source Compose file has one application service and no database service. | S06 L6 |
| L26 | verified | PR 4208 remains open and overlaps the shared portal files. | R08 |
| L27 | stale | The target evidence files are unchanged since 772fc927. Compose and requirements changed. | R13, R50, R51 |
| L28 | stale | The target requires Python 3.13 or newer. The repository requires Python 3.15. | T17 L20 |
| L29 | stale | Issue 4278 is closed. GitHub reports it open. | R11 |
| L30 | stale | The source LICENSE citation is L1 to L26. The file has 39 lines. | R61, S04 |
| L31 | stale | The source development Compose citation is L1 to L16. The file has 17 lines. | R64, S07 |
| L32 | stale | Only projection P063 is existing guest functionality. Menu 200 also exists. | T06 L118 |
| L33 | stale | The legacy analysis reports 42 of 42 requirements. The spec defines 35 functional requirements. | Legacy spec and analysis |
| L34 | absent | The pyproject constraint permits mistapi 0.64.1 below 0.65. The run did not read `pyproject.toml`. | None |
| L35 | absent | Official HPE API pages were fetched on 2026-11-05. The run did not fetch them. | None |
| L36 | absent | A fresh screenshot manifest and 12 captures exist in session files. The run did not check session files. | None |
| L37 | absent | The legacy validation commands passed. The run did not run them. | None |
| L38 | absent | PR 4290 merged nine 4231 planning files. The merge is verified, but the file list is not checked. | R07 |
| L39 | absent | Upstream mistapi tag `0544d85b` matches the installed SDK. The run did not check upstream. | None |
| L40 | absent | Upstream source pin commit `66a57a64` exists. The run did not check upstream. | None |

Ledger totals: 26 verified, 7 stale, and 7 absent.

## 4. Source evidence (MistGuestAuthorizations at 0213240c)

Base link: `https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/`. Append the path and `#L<start>-L<end>`.

| ID | File and blob SHA | Lines used |
| --- | --- | --- |
| S01 | `app.py` (`270eb700e43fed1fae6ccdf8a28e7f57c9d316f8`) | L85 to L88 index. L91 to L99 test connection. L123 to L128 sites. L147 to L152 site WLANs. L159 to L164 WLAN guests. L171 to L184 authorize. L193 to L196 payload fields. L210 to L231 revoke. L234 to L255 update. L270 to L276 client search. L285 to L334 CSV template. L349 to L362 sites-WLAN map. L377 to L407 bulk import. L423 to L424 health |
| S02 | `mist_connection.py` (`72d6226a6bfb5cf85178108b94e6bde8495b4d0f`) | L38 exception. L42 `normalize_mac`. L68 `mac_to_api_format`. L89 class. L102 session. L118 `getSelf`. L127 `test_connection`. L134 `getOrg`. L160 first organization selected. L176 `get_sites`. L198 `listOrgSites`. L245 to L282 templates and site groups. L283 to L296 WLAN site IDs. L321 `get_guest_wlans`. L330 `listSiteWlans`. L342 `listOrgWlans`. L399 `get_wlan_guests`. L406 `listSiteAllGuestAuthorizations`. L423 `listOrgGuestAuthorizations`. L487 `authorize_guest`. L523 `field4` parameter deleted. L538 to L547 optional fields. L550 to L552 token name in `field4`. L554 to L555 notify. L558 `wlan_id` in payload. L563 site update. L592 org update. L621 `deauthorize_guest`. L649 to L652 `minutes` set to 0 with PUT. L659 to L660 2xx success. L672 `update_guest`. L758 to L772 site-or-org update. L780 `search_wireless_clients`. L797 `listSiteWirelessClientsStats` |
| S03 | `templates/index.html` (`ef954198c1768b4e2d57cddd3aeaf93c6caddf95`) | L6 title. L10 to L25 theme variables. L30 font. L483 and L516 media rules. L534 toast container. L542 to L547 connection status and test button. L555 to L572 banner. L580 to L597 selectors. L611 to L617 actions. L626 to L647 statistics. L654 to L666 guest section. L674 to L676 empty state. L686 to L736 add dialog. L737 to L747 presets. L754 to L758 client search. L765 to L767 cancel and submit. L776 to L848 edit dialog. L843 to L845 revoke. L858 to L924 import dialog. L1038 failed sites toast. L1060 to L1063 site search. L1101 `(Org)` label. L1122 guest load error log. L1137 guest search fields. L1149 to L1150 time badges. L1305 preview slice. L1381 to L1382 lowercase mapping. L1409 minutes default. L1485 to L1489 duration text. L1512 two-character minimum. L1591 submit spinner. L1639 edit payload. L1680 to L1682 revoke toast. L1775 debounce. L1792 test on load |
| S04 | `LICENSE` (`bbea5fed78ca98720c6590d4151de423714ea6de`) | L1 license title. L3 copyright line |
| S05 | `Dockerfile` (`439d32810479f4eca790622a4a3777ebab02a51d`) | L4 base image. L12 license label. L48 user. L51 to L53 environment. L56 port. L59 health check. L63 command |
| S06 | `docker-compose.yml` (`7a9206c460da9cda84f708c3e8f54694840aa4bb`) | L6 service. L7 image. L8 container name. L10 to L11 port mapping. L16 port variable. L20 volumes. L23 health check |
| S07 | `docker-compose.dev.yml` (`229d1a0d30e23605b243ba839df45ca918bada3a`) | L2 service. L6 container name. L7 to L8 port mapping. L15 volumes. L17 restart policy |
| S08 | `requirements.txt` (`e3c62ee4fd6bd48c8cb94af0c8d6d0fdb5df01a7`) | L2 mistapi 0.64.0. L3 Flask 3.1.3. L4 python-dotenv 1.2.4 |
| S09 | `docs/guide.md` (`439dfae00662a1ba2297aa45123e14570fa66f7a`) | L25 revoke feature. L27 five-year duration claim. L195 to L197 edit and statistics text. L238 revoke note |
| S10 | `README.md` (`f92e7f65b8215d30cade46c58046ff0367514b9d`) | L1 title. L6 purpose. L11 dashboard image. L74 maintainer line. L77 license link |
| S11 | `tests/test_application.py` (`eb879e2a1f7f0923fdd749a476827f149452e6ec`) | Present. The run did not read its contents. |
| S12 | `.github/workflows/quality-gates.yml` (`f80fbd4192fa71e275a8fec871503e801997f9ec`) | Present. The run did not read its contents. |
| S13 | `docs/screenshots/*.png` (seven blobs) | Present. The run did not inspect the images. |

Key source facts:

- The source app exposes 13 route handlers. Its `mist_connection` module calls 12 distinct mistapi functions.
- The grant path uses `updateSiteGuestAuthorization` with an organization fallback at S02 L592.
- The revoke path uses PUT with `minutes` set to 0 (S02 L649 to L652). It does not use DELETE.
- The grant payload includes `name` (S02 L538) and `wlan_id` (S02 L558). The schema marks both read-only.
- The grant payload includes `field4` from the API token name (S02 L550 to L552).
- The source has one application service, no database, no Redis, and port 5000 (S06 and S05).

## 5. Target evidence (MistHelper at f03c6c9b)

Base link: `https://github.com/jmorrison-juniper/MistHelper/blob/f03c6c9b36d612a48d7b9652998c2fd87dd777ca/`. Append the path and `#L<start>-L<end>`.

| ID | File and blob SHA | Lines used |
| --- | --- | --- |
| T01 | `src/interfaces/portals/guest_authorizations.py` (`7101772d492af0a340b88d3cd3c2e221db9e7d31`) | L1 to L7 docstring. L17 class. L21 `project`. L36 `_masked_mac`. L46 `_authorized`. L54 `_expiration` |
| T02 | `tests/unit/web_portal/test_guest_authorization_read_model.py` (`464c999daefa9d77ff451778e5228aa9a9033e38`) | L11 to L12 (three cases). L43 to L44 (three cases). L53 to L69 (12 cases). L83 to L84 (three cases). L91 (one case) |
| T03 | `web_portal/app.py` (`0fb25df1732815d18ff30d1823cbbdd30608aed6`) | L37 `create_app`. L53 registration call. L182 `_register_blueprints`. L200 to L207 registrations. L235 webhook registration |
| T04 | `web_portal/templates/base.html` (`351cc44aeeae0a6fd61d4205af2de6777d066b2f`) | L35 to L37 navigation and brand. L51 to L78 navigation links |
| T05 | `web_portal/services/config.py` (`c198505a43bbd2faadfcffee6c8685c6ab5df17c`) | L12 to L13 access statement. L65 loader. L80 accent color. L81 theme. L82 web port. L83 to L84 allowlist defaults. L159 middleware. L166 CSP policy. L297 to L303 CSRF setup |
| T06 | `web_portal/menu_registry.py` (`ad7b102a62949be55e553b71fc4f24b8b261cc65`) | L118 menu 200 entry |
| T07 | `web_portal/services/row_sorter.py` (`4a11f8e331ba9b2a5b44f54ebf1d8b3d278d7f2e`) | L35 `MAX_SORT_ROWS = 50_000` |
| T08 | `src/operations/exporting/export/site_guest_authorization_exporter.py` (`4d4c500b56ed9932611fe0d7ad837b8af8d03677`) | L41 class. L95 info log. L115 HTTP status message |
| T09 | `compose.yml` (`b3944fc9f994ca149974072b1a9c8f13797d7924`) | L23 to L27 port table note. L53 service. L80 to L88 image and ports. L105 to L115 port variables. L140 ArangoDB host. L148 Redis port. L169 health check. L191 to L199 ArangoDB. L231 to L238 Redis. L270 to L273 optional Observium profile. L344 to L362 volumes |
| T10 | `requirements.txt` (`50fe63d4cf5e6071612c62c288e965190c60b969`) | L129 `mistapi==0.64.1` |
| T11 | `documentation/mist-api-openapi31json.json` (`5f9f4ce94f812f0e818ee65f99f032118a28f56c`) | Line 1 holds the minified document. JSON pointers identify the paths and the schema. |
| T12 | `documentation/mist-api-openapi31yaml.yaml` (`b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`) | L10092, L10115, L10149, and L10199 hold organization guest paths. L32317, L32346, L32382, L32418, and L32465 hold site guest paths |
| T13 | `documentation/MIST_API_MISSING_ENDPOINTS.md` (`e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0`) | L151 sites guests coverage row. L549 to L555 organization guest section |
| T14 | `documentation/MIST_API_GET_ENDPOINTS.md` (`6281c11b46f22b9814a1948a96df9be4945fb8fd`) | L54 and L148 summary links. L561 to L568 organization guest list. L1253 site guest section |
| T15 | `documentation/container-deployment.md` (`f06228bc6bbe77cc009f956403872a06462466ea`) | L20 compose services. L141 test and debug containers |
| T16 | `documentation/architecture.md` (`b4cab54be36d223b7eba879ca99b838f508938ce`) | L160 directory and runtime layout. L202 source layout |
| T17 | `.github/copilot-instructions.md` (`f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179`) | L20 Python 3.15. L50 local gates. L153 architecture. L159 to L160 managed spec roots. L309 to L353 safety section and data table. L350 page limit. L354 containers and ports. L473 container build trigger |
| T18 | `.specify/memory/constitution.md` (`4584997a264c5a7ade2ca7441246e1f067083aa1`) | L38 principle I. L113 principle III. L143 principle IV. L204 principle VI. L235 principle VII. L274 technology constraints. L279 mistapi floor. L315 to L316 operational store |
| T19 | `.specify/scripts/powershell/spec-route.ps1` (`37293a255f9b5de20ccb2b3ef0ad15717bab2826`) | L4 radix function. L34 path resolver. L54 timestamp function. L76 destination guard. L100 directory count |
| T20 | `README.md` (`331a4567f72156fe2a3e3ee91005d2cbbcaed6d0`) | L134 to L136 license section |
| T21 | `LICENSE` (`d115eeab9dbd6f61d0233b0894d3f8309bb976e8`) | L1 license title |
| T22 | `documentation/quality-gates.md` (`6776d334cca5d9b43273473a06da367a65605c6d`) | L18 citation and task audit tools. L66 citation gate row. L283 STE command |
| T23 | `documentation/operator-guide.md` (`60d28f9ea461fc8798973d1d1b7e40491c27c248`) | L72 to L73 menu 284 SMS note. This menu is adjacent and out of scope. |
| T24 | `AGENTS.md` (`44a9afffb5bd6f774973a845d27343e4e528b6ad`) | Sections for writing style, specifications, Git flow, and safety |
| T25 | `documentation/development-setup.md` (`1733975a7e0a0962fe5367e165a21f5831f8c3e5`) | Searched for guest content. None found. |

Key target facts:

- The offline projection (T01) exposes three fields: `masked_mac`, `authorized`, and `expires_at`. It has no route, session, storage, or SDK call.
- The projection tests (T02) contain 22 cases. The count is 3, plus 3, plus 12, plus 3, plus 1.
- The portal registers eight blueprints at L200 to L207 and one webhook at L235. No guest blueprint exists (T03).
- The portal navigation has seven links. No guest link exists (T04).
- The portal has no user authentication. Access uses an address allowlist. CSRF protection uses `flask-wtf` (T05).
- The default theme is `magenta` with accent `#E20074` (T05 L80 to L81). The source uses the same magenta value (S03 L12).
- The existing CLI and operation registry include menu 200, a per-site guest authorization CSV export (T06 L118 and T08 L41).
- The existing SQLite store is `data/mist_data.db` (T17 L309 to L353).
- The target runs one `misthelper` service with web port 8055 and capture port 8056. ArangoDB uses 9529 and Redis uses 9379 (T09).

## 6. SDK and API schema evidence

The installed package is `mistapi` 0.64.1 (R71). The source pins 0.64.0 (S08 L2). The target pins 0.64.1 (T10 L129). The run did not install or run either package.

| Function | Module (local `.venv`) | Def line | HTTP call and URI | Source use |
| --- | --- | --- | --- | --- |
| `listOrgGuestAuthorizations` | `mistapi/api/v1/orgs/guests.py` | 17 | GET L36 to L38 | S02 L423 |
| `countOrgGuestAuthorizations` | same | 42 | GET L82 to L94 | None |
| `searchOrgGuestAuthorization` | same | 98 | GET L147 to L165 | None |
| `getOrgGuestAuthorization` | same | 169 | GET L191 to L193 | None |
| `deleteOrgGuestAuthorization` | same | 197 | DELETE L219 to L221 | None |
| `updateOrgGuestAuthorization` | same | 225 | PUT L252 to L253 | S02 L592 and L772 |
| `listSiteAllGuestAuthorizations` | `mistapi/api/v1/sites/guests.py` | 17 | GET L43 to L47 | S02 L406 |
| `countSiteGuestAuthorizations` | same | 51 | GET L91 to L103 | None |
| `listSiteAllGuestAuthorizationsDerived` | same | 107 | GET L138 to L144 | None |
| `searchSiteGuestAuthorization` | same | 148 | GET L200 to L220 | None |
| `getSiteGuestAuthorization` | same | 224 | GET L246 to L248 | None |
| `deleteSiteGuestAuthorization` | same | 252 | DELETE L274 to L276 | None |
| `updateSiteGuestAuthorization` | same | 280 | PUT L307 to L308 | S02 L563, L651, and L766 |

The site update signature is `(mist_session, site_id, guest_mac, body)`. The body has type `dict`. The site delete signature is `(mist_session, site_id, guest_mac)`.

Checked-in schema facts (T11 and T12):

- The `info.version` value is `2609.1.0`. The OpenAPI version is 3.1.0.
- Organization paths cover list, count, search, and the MAC path with GET, PUT, and DELETE.
- Site paths cover list, count, derived, search, and the MAC path with GET, PUT, and DELETE.
- `guest.minutes` is an integer. Its minimum is 0, its maximum is 259200, and its default is 1440.
- Read-only fields are `name`, `mac`, `wlan_id`, `ssid`, `auth_method`, `random_mac`, `access_code_email`, `ap_mac`, `authorized_time`, and `authorized_expiring_time`.
- Writable fields are `authorized` (boolean, default true), `minutes`, `company`, `email` (format email), and `field1` to `field4`.
- The guest schema has no `notify` property.

Warning: the source guide and the source code disagree about revocation. The guide says DELETE does not remove the guest (S09 L238). The source code uses PUT with `minutes` set to 0 (S02 L649 to L652). This run verified neither method against live cloud behavior.

## 7. Decision register

Each decision records the options, the chosen option, the reason, the risk, and whether a human decision is required.

### D-1 Record location

- Options: (a) overwrite the legacy folder, (b) use a new number, or (c) use a new slug at the same route.
- Chosen: (c). The record path is `specs\numbered\0\0\1\2\1\3\2\3\4588-guest-migration-parity-refresh`. The legacy folder is retired, backed up outside the repository, and listed in the pull request body.
- Reason: One canonical record for issue 4588 avoids two folders with one number. The issue fixes the number and the route.
- Risk: Acceptance criterion 1 of the issue forbids changes to old planning drafts. Retiring the legacy folder changes one such draft.
- Human decision: Yes. The batch coordinator relayed the retirement decision.

### D-2 Implementation tracker

- Options: (a) use #4278, as the issue body states, (b) use #4231, as the owner comment of 2026-11-08 states, or (c) create a new issue.
- Chosen: (b). Issue #4231 is the single tracker for the full migration. Issue #4278 stays open as the workflow child until the owner closes it.
- Reason: The later owner comment names #4231. GitHub reports both issues open. The owner asked for no duplicate issue.
- Risk: The owner comment says #4278 is closed. GitHub does not agree. The owner must reconcile the two states.
- Human decision: No. The owner closes issues.

### D-3 Source pin

- Options: (a) the local clone at `61f6a48f`, or (b) GitHub main at `0213240c`.
- Chosen: (b). Source citations use the immutable commit `0213240c`.
- Reason: The local clone is older than GitHub main. The truth order requires GitHub evidence.
- Risk: Future source commits may change the baseline. T001 repeats the pin check before implementation.
- Human decision: No.

### D-4 Target pin and shared-file ownership

- Options: (a) keep the 772fc927 baseline, (b) pin GitHub main `f03c6c9b`, or (c) edit shared files now.
- Chosen: (b). Target evidence cites main blob SHAs. No shared file changes until PR 4208 closes or the owner hands over the files.
- Reason: Compose and requirements changed after 772fc927 (R50 and R51). PR 4208 is open and overlaps `web_portal/app.py` and `web_portal/templates/base.html` (R08).
- Risk: PR 4208 may take time to close. Implementation waits on it.
- Human decision: No.

### D-5 Licensing and attribution

- Options: (a) relicense the derived work, (b) keep CC BY-NC-SA 4.0 with attribution and share-alike, or (c) build from the API schema and observed behavior. Option (c) copies no text, markup, styles, or images.
- Chosen: (b) for every derived document, and (c) for every code and asset change.
- Reason: The source license is CC BY-NC-SA 4.0 (S04 L1). MistHelper also uses CC BY-NC-SA 4.0 (T20 L134 to L136 and T21 L1). The share-alike term keeps the same license for derived work.
- Risk: The noncommercial term may not fit internal use by Juniper. A legal reading is required. HUMAN-DECISION-REQUIRED: confirm the noncommercial reading and approve the attribution text.
- Human decision: Yes.

### D-6 Operator access and write authority

- Options: (a) keep the address allowlist and typed confirmation, (b) add operator authentication with roles before writes, or (c) keep every guest function read-only.
- Chosen: Read-only review stays behind the address allowlist. Writes stay disabled until the owner approves operator identity. Option (b) is recommended before any write.
- Reason: The portal has no user authentication (T05 L12 to L13). A write changes device access in the cloud. Writes need a named operator for audit.
- Risk: Option (c) does not complete the migration. Option (a) lets any allowed address write.
- HUMAN-DECISION-REQUIRED: approve the operator identity and role model for writes.
- Human decision: Yes.

### D-7 Duration bounds and presets

- Options: (a) copy all source presets and the 2628000 maximum, (b) clamp silently to the schema maximum, or (c) enforce the schema range. Option (c) shows each limit.
- Chosen: (c). Accept integer minutes from 0 to 259200. Default new grants to 1440. Offer presets 60, 480, 1440, 2880, 4320, 10080, 43200, and 129600. Do not offer 262800 or 525600.
- Reason: The schema maximum is 259200 (T11). The source five-year promise (S09 L27) and its 2628000 maximum (S03 L736) exceed that bound.
- Risk: Operators cannot grant access longer than 180 days. The owner can revise the bound with new evidence.
- Human decision: No.

### D-8 Revocation

- Options: (a) PUT with `minutes` set to 0, (b) DELETE, (c) PUT with `authorized` set to false, or (d) keep revoke unavailable until verified.
- Chosen: (d). Enable revoke only after a contract test shows the authoritative state after the call. Option (c) is the candidate for that test.
- Reason: The source uses option (a) and treats a 2xx response as success (S02 L649 to L660). The guide says option (b) does not remove the guest (S09 L238). The schema lists `authorized` as writable (T11).
- Risk: Warning: a wrong revoke can keep device access without a visible error. Keep the control disabled until the contract test passes.
- Human decision: No.

### D-9 Read-only and unsupported payload fields

- Options: (a) copy the source payload, (b) send `name` and `wlan_id` and rely on the server to ignore them, or (c) omit read-only fields. Option (c) applies to every request body.
- Chosen: (c). Never send `name`, `wlan_id`, `ssid`, or other read-only schema fields in a request body. The MAC stays in the path.
- Reason: The source sends `name` (S03 L1639) and `wlan_id` (S02 L558). The schema marks both read-only (T11).
- Risk: The edit form shows a disabled name. Operators cannot change the name in the portal.
- Human decision: No.

### D-10 Notification

- Options: (a) keep the source `notify` option, (b) add a notification control, or (c) never send `notify`.
- Chosen: (c). The portal shows no notification control. The payload omits `notify`.
- Reason: The checked schema does not declare `notify` (T11). The source sends `notify` only when the value is true (S02 L554 to L555).
- Risk: A future approved workflow may need notification. It needs schema evidence first.
- Human decision: No.

### D-11 CSV bounds and duplicates

- Options: (a) no limits, (b) 50000 rows, the sorter cap in T07, or (c) 1 MiB, 1000 data rows, and exact headers.
- Chosen: (c). Reject a file above 1,048,576 bytes. Accept at most 1000 data rows in one batch. Require the ten declared headers after trimming. Reject an unknown header. Reject a row with missing or invalid `minutes`. Reject a duplicate MAC in one batch. Require an explicit ID for an ambiguous site name or SSID.
- Reason: The source defaults invalid minutes to 1440 (S03 L1409), which is unsafe. The repository default page size is 1000 (T17 L350). The 50000 row cap in T07 bounds sorting, not API work.
- Risk: Large sites need several batches. The owner can revise the limits with a new decision.
- Human decision: No.

### D-12 Audit and recovery store

- Options: (a) ArangoDB transactions, (b) Redis keys, or (c) the SQLite store `data/mist_data.db`.
- Chosen: (c). Store durable intent and outcome records in the SQLite store. Write intent before every dispatch. Never delete records automatically. Manual deletion needs a typed confirmation.
- Reason: The constitution names a declared operational store for transactions and locks (T18 L315 to L316). The repository names `data/mist_data.db` as the SQLite store (T17 L309 to L353). Redis is ephemeral. The docs do not name the operational store explicitly.
- Risk: SQLite locking under the web workers is untested. T030 tests it before any write.
- Human decision: No. The decision does not delete data.

### D-13 Visual integration

- Options: (a) copy the source CSS, (b) use an unrelated theme, or (c) use the target theme tokens with the source layout and control order.
- Chosen: (c). Use the target magenta theme tokens (T05 L80 to L81). Keep the source order of selectors, statistics, the guest list, and three dialogs. Record each deviation.
- Reason: The source and target use the same magenta value (S03 L12). Copying source CSS adds license risk and no functional gain.
- Risk: Pixel comparison needs reviewer tolerances. T006 records them. The planning run captured no screenshots.
- Human decision: No.

### D-14 Typed confirmation words

- Options: (a) one word for every write, (b) click-only confirmation, or (c) one exact word for each action.
- Chosen: (c). The words are GRANT, UPDATE, EXTEND, REVOKE, and IMPORT. The batch confirmation binds to a digest of the reviewed rows.
- Reason: Constitution principle III requires typed confirmation for changes to the cloud (T18 L113 to L141). The repository safety section uses typed words (T17 L309 to L353).
- Risk: Operators must type each word exactly. The UI shows the word and the scope.
- Human decision: No.

### D-15 Scope of the first implementation slice

- Options: (a) implement writes first, (b) implement read-only review first, or (c) move the offline projection first.
- Chosen: (c), then (b). The move keeps the 22 projection tests green. Read-only review follows after D-6 and D-7 approval. Writes come last.
- Reason: The projection is the only existing guest code (T01 and T02). Read-only review needs fewer decisions than writes.
- Risk: Read-only review still needs approved access under D-6.
- Human decision: No.

## 8. Remote verification table

Prefix for rows R14 to R26: `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/`. Prefix for rows R27 and R28: `specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/`. Forward slashes name the same files as the Windows paths.

| # | Claim | Path | Ref | Blob SHA or object | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | Target main commit exists | commit main (MistHelper) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R02 | Local target HEAD equals main | local HEAD (MistHelper) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R03 | Source main commit matches the issue pin | commit main (MistGuestAuthorizations) | main | 0213240cb9edfa237f763acd156b90a6049363cb | present | 0 |
| R04 | Source local clone is older than main | local HEAD (MistGuestAuthorizations) | 61f6a48f3a4e87a77069201879f81443d088ef16 | 61f6a48f3a4e87a77069201879f81443d088ef16 | stale | 0 |
| R05 | Planning PR 4589 merge commit exists | commit 5d444bda23ea50de131d67b6e6fcf37055adfa77 | main | 5d444bda23ea50de131d67b6e6fcf37055adfa77 | present | 0 |
| R06 | PR 4279 merge commit exists | commit 1e9b280ddb0285048e515cb837f6802ac38ceb0e | main | 1e9b280ddb0285048e515cb837f6802ac38ceb0e | present | 0 |
| R07 | PR 4290 merged on 2026-10-20 | pull/4290 | main | n/a (pull request) | present | 0 |
| R08 | PR 4208 is open and changes app.py and base.html | pull/4208 | main | n/a (pull request) | present | 0 |
| R09 | Issue 4588 is open | issues/4588 | main | n/a (issue) | present | 0 |
| R10 | Issue 4231 is open | issues/4231 | main | n/a (issue) | present | 0 |
| R11 | Issue 4278 is closed according to the owner comment | issues/4278 | main | n/a (issue) | stale | 0 |
| R12 | Issue 4869 is closed | issues/4869 | main | n/a (issue) | present | 0 |
| R13 | Baseline 772fc927 is 117 commits behind main and watched files changed | compare 772fc927 to main (MistHelper) | 772fc927761b61dea8beb7f708fbbe78c2a38d86 | 772fc927761b61dea8beb7f708fbbe78c2a38d86 | stale | 0 |
| R14 | Legacy spec.md exists on main | spec.md | main | 1abe8eb89d62178063764a22be66c1902a570967 | present | 1 |
| R15 | Legacy plan.md exists on main | plan.md | main | 8d55ffbaa4cf0f82c0dbb52d44d061f3fe08b868 | present | 1 |
| R16 | Legacy tasks.md exists on main | tasks.md | main | 1fc5daf1b62b303e8fa8fad93ba584f2c5a63d41 | present | 1 |
| R17 | Legacy analysis.md exists on main | analysis.md | main | c22a73cb209b787e9fa156abc60d078362943981 | present | 1 |
| R18 | Legacy design/research.md exists on main | design/research.md | main | 5b65dfc349c28f4404f1685f128e9b223fcb0fd1 | present | 1 |
| R19 | Legacy design/data-model.md exists on main | design/data-model.md | main | 47c02826b6f28cea8162d2f0e3536afc03ce3207 | present | 1 |
| R20 | Legacy design/quickstart.md exists on main | design/quickstart.md | main | d76b3320171d5ff189b7dca3d10101a00c911f0e | present | 1 |
| R21 | Legacy checklists/requirements.md exists on main | design/checklists/requirements.md | main | 45211a5da766e85dd52d8afea48025f9d4f3086c | present | 1 |
| R22 | Legacy checklists/migration.md exists on main | design/checklists/migration.md | main | 22327de478b32b60bd12d204b5b00bf4c5a83e93 | present | 1 |
| R23 | Legacy contracts/api.md exists on main | design/contracts/api.md | main | e8740d6cbf2bf4115afe412bab97fa64ea5fd3af | present | 1 |
| R24 | Legacy contracts/e2e.md exists on main | design/contracts/e2e.md | main | 635ffb1fcf9d2e55f09c089185fe4360c593c2e3 | present | 1 |
| R25 | Legacy contracts/parity.md exists on main | design/contracts/parity.md | main | 27c03468ccf33c285eb117ca0d9789da4f7688cb | present | 1 |
| R26 | Legacy contracts/source-files.md exists on main | design/contracts/source-files.md | main | 19e7f6df2106619ff16623490577874a57c8eaaf | present | 1 |
| R27 | Record 4231 spec.md exists on main | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/spec.md | main | c54db8de9e10647e1936731946135566fca8faf5 | present | 1 |
| R28 | Record 4231 plan.md exists on main | specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/plan.md | main | af27f93ce43873f6e6e8e3b7f0630192a529abf2 | present | 1 |
| R29 | Spec route functions exist | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R30 | Constitution names the operational store and the mistapi floor | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| R31 | Repository instructions state Python 3.15 and local gates | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R32 | AGENTS.md states writing and Git rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 1 |
| R33 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| R34 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| R35 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| R36 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R37 | Quality gates name citation and task audit tools | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 18 |
| R38 | Architecture names the directory layout | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 160 |
| R39 | Container policy names test and debug containers | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R40 | Operator guide notes adjacent menu 284 | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 72 |
| R41 | Development setup holds no guest content | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 1 |
| R42 | Offline projection class exists | src/interfaces/portals/guest_authorizations.py | main | 7101772d492af0a340b88d3cd3c2e221db9e7d31 | present | 17 |
| R43 | Projection tests contain 22 cases | tests/unit/web_portal/test_guest_authorization_read_model.py | main | 464c999daefa9d77ff451778e5228aa9a9033e38 | present | 11 |
| R44 | App registers no guest blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 200 |
| R45 | Navigation has no guest link | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 51 |
| R46 | Access model has no user authentication | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 12 |
| R47 | Menu 200 site guest CSV entry exists | web_portal/menu_registry.py | main | ad7b102a62949be55e553b71fc4f24b8b261cc65 | present | 118 |
| R48 | Row cap constant exists | web_portal/services/row_sorter.py | main | 4a11f8e331ba9b2a5b44f54ebf1d8b3d278d7f2e | present | 35 |
| R49 | Site guest CSV exporter class exists | src/operations/exporting/export/site_guest_authorization_exporter.py | main | 4d4c500b56ed9932611fe0d7ad837b8af8d03677 | present | 41 |
| R50 | Compose names one application and the ports | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 53 |
| R51 | Target pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R52 | MistHelper README states the license | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 134 |
| R53 | MistHelper LICENSE title is CC BY-NC-SA 4.0 | LICENSE | main | d115eeab9dbd6f61d0233b0894d3f8309bb976e8 | present | 1 |
| R54 | Checked-in JSON schema holds version 2609.1.0 and the guest schema | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 1 |
| R55 | Checked-in YAML holds the guest paths | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10092 |
| R56 | Missing endpoint table holds the guest row | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 151 |
| R57 | Get endpoint list holds guest entries | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 561 |
| R58 | Source app holds 13 routes | MistGuestAuthorizations: app.py | 0213240cb9edfa237f763acd156b90a6049363cb | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | present | 85 |
| R59 | Source SDK calls, field4, notify, and revoke exist | MistGuestAuthorizations: mist_connection.py | 0213240cb9edfa237f763acd156b90a6049363cb | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | present | 550 |
| R60 | Source UI IDs, presets, and labels exist | MistGuestAuthorizations: templates/index.html | 0213240cb9edfa237f763acd156b90a6049363cb | ef954198c1768b4e2d57cddd3aeaf93c6caddf95 | present | 583 |
| R61 | Source license title is CC BY-NC-SA 4.0 | MistGuestAuthorizations: LICENSE | 0213240cb9edfa237f763acd156b90a6049363cb | bbea5fed78ca98720c6590d4151de423714ea6de | present | 1 |
| R62 | Source Dockerfile holds the base image and labels | MistGuestAuthorizations: Dockerfile | 0213240cb9edfa237f763acd156b90a6049363cb | 439d32810479f4eca790622a4a3777ebab02a51d | present | 4 |
| R63 | Source Compose holds one service and port 5000 | MistGuestAuthorizations: docker-compose.yml | 0213240cb9edfa237f763acd156b90a6049363cb | 7a9206c460da9cda84f708c3e8f54694840aa4bb | present | 6 |
| R64 | Source development Compose holds one service | MistGuestAuthorizations: docker-compose.dev.yml | 0213240cb9edfa237f763acd156b90a6049363cb | 229d1a0d30e23605b243ba839df45ca918bada3a | present | 2 |
| R65 | Source pins mistapi 0.64.0 | MistGuestAuthorizations: requirements.txt | 0213240cb9edfa237f763acd156b90a6049363cb | e3c62ee4fd6bd48c8cb94af0c8d6d0fdb5df01a7 | present | 2 |
| R66 | Source guide holds the five-year claim and the revoke note | MistGuestAuthorizations: docs/guide.md | 0213240cb9edfa237f763acd156b90a6049363cb | 439dfae00662a1ba2297aa45123e14570fa66f7a | present | 27 |
| R67 | Source README states the license | MistGuestAuthorizations: README.md | 0213240cb9edfa237f763acd156b90a6049363cb | f92e7f65b8215d30cade46c58046ff0367514b9d | present | 77 |
| R68 | Source tree holds 39 blobs and 7 trees | MistGuestAuthorizations: tree | 0213240cb9edfa237f763acd156b90a6049363cb | tree listing | present | 0 |
| R69 | Installed SDK organization guest functions exist | .venv/Lib/site-packages/mistapi/api/v1/orgs/guests.py (local) | local | not in repository | present | 17 |
| R70 | Installed SDK site guest functions exist | .venv/Lib/site-packages/mistapi/api/v1/sites/guests.py (local) | local | not in repository | present | 17 |
| R71 | Installed mistapi version is 0.64.1 | .venv/Lib/site-packages/mistapi-0.64.1.dist-info/METADATA (local) | local | not in repository | present | 3 |

Row count: 71. The `remote_checks` array in the STATUS file holds the same 71 rows.

## 9. Sources

- Issue 4588: https://github.com/jmorrison-juniper/MistHelper/issues/4588
- Issue 4231: https://github.com/jmorrison-juniper/MistHelper/issues/4231
- Issue 4278: https://github.com/jmorrison-juniper/MistHelper/issues/4278
- Issue 4869: https://github.com/jmorrison-juniper/MistHelper/issues/4869
- PR 4589: https://github.com/jmorrison-juniper/MistHelper/pull/4589
- PR 4279: https://github.com/jmorrison-juniper/MistHelper/pull/4279
- PR 4290: https://github.com/jmorrison-juniper/MistHelper/pull/4290
- PR 4208: https://github.com/jmorrison-juniper/MistHelper/pull/4208
- Source repository: https://github.com/jmorrison-juniper/MistGuestAuthorizations
- Checked-in JSON schema: `documentation/mist-api-openapi31json.json` at main (T11)
- Checked-in YAML schema: `documentation/mist-api-openapi31yaml.yaml` at main (T12)
- Installed SDK: `.venv/Lib/site-packages/mistapi` (local, read only)
- Spec route script: `.specify/scripts/powershell/spec-route.ps1` (read only, not executed)

## 10. Unverified

- U01: The contents of source test file S11 and quality workflow S12 were not read.
- U02: The source screenshots were not inspected. No browser rendered the source or the target.
- U03: Visual parity is UNVERIFIED. The run did not render the source app, because the brief forbids repository scripts and containers.
- U04: The run did not check live Mist behavior for revoke, extension, name editing, or zero-minute expiry.
- U05: The mistapi 0.64.0 source is not installed. Signatures for the source pin are UNVERIFIED.
- U06: The SQLite store behavior under concurrent web workers is UNVERIFIED.
- U07: The constitution names a declared operational store. No document in the checked tree names it.
- U08: The run did not read `pyproject.toml`. The mistapi constraint in that file is UNVERIFIED.
- U09: The app-managed branch was not checked. The brief forbids branch commands.
- U10: The prefilled client selection and its writable fields (P031) were not re-read in the source. The legacy claim is UNVERIFIED.
- U11: The source CSV parser details (P043) and sort behavior (P052) were not re-read in the source.
- U12: The contents of PR 4290 (nine files) were not checked. The legacy claim is UNVERIFIED.
- U13: No local gate was run. The results of the STE, citation, link, and task-audit checks are UNVERIFIED.
