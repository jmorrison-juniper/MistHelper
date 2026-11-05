# Source and target evidence

## Baselines and ownership

The inspection date is 2026-11-05.
Current source HEAD is `0213240cb9edfa237f763acd156b90a6049363cb`.
The GitHub compare result against the previous pin is `identical`, with zero commits ahead or behind.
The inspected target baseline is `772fc927761b61dea8beb7f708fbbe78c2a38d86`.
Before submission, current main advanced to `c57c9b704c1ce23976228cd72cad80b9d99926be`.
All eight target evidence files below are unchanged between these commits.
The newer bootstrap instruction uses `uv sync --locked --extra dev`.
The first bootstrap ran the previously inspected script. Final validation must use the rebased current script and environment.

[PR #4279](https://github.com/jmorrison-juniper/MistHelper/pull/4279) merged the independent offline projection.
[PR #4290](https://github.com/jmorrison-juniper/MistHelper/pull/4290) merged nine old planning files on 2026-10-20.
The current bodies of #4231 and #4278 still contain older rights assumptions.
The user-confirmed authorship and use authorization supersede those planning assumptions, but do not change the declared license.
This change does not edit those issues or their old record.

The current target still uses `src/interfaces/portals/guest_authorizations.py`.
Its public record contains only `masked_mac`, `authorized`, and `expires_at`.
No guest blueprint, route, navigation item, client search, or write workflow exists.
The projection docstring still mentions a license gate. Future maintenance must align that text with the resolved authorization.

PR #4208 currently owns `web_portal/app.py`, `web_portal/templates/base.html`, and other shared files.
This planning record changes none of them. T007 requires a new ownership inspection before future edits.
The declared current file set is this unique managed record and its planning documents.
It also includes one unique planning release-note fragment.
No product, shared instruction, feature selector, dependency, Compose, or baseline file changes.

## Immutable evidence index

All source links use the current source commit, not a moving branch.
Line ranges identify inspected source, not a claim of tested cloud semantics.

| ID | Source evidence |
| --- | --- |
| S01 | [Application routes and response handling, app.py L86-L286](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/app.py#L86-L286) |
| S02 | [CSV download, mapping, import, health, app.py L289-L436](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/app.py#L289-L436) |
| S03 | [Session, connection, site discovery, mist_connection.py L93-L321](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/mist_connection.py#L93-L321) |
| S04 | [WLAN and guest discovery, mist_connection.py L322-L488](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/mist_connection.py#L322-L488) |
| S05 | [Grant, revoke, update, mist_connection.py L489-L781](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/mist_connection.py#L489-L781) |
| S06 | [Client search, mist_connection.py L783-L845](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/mist_connection.py#L783-L845) |
| S07 | [Theme and responsive CSS, templates/index.html L1-L531](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L1-L531) |
| S08 | [Dashboard, selectors, actions, stats, templates/index.html L534-L687](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L534-L687) |
| S09 | [Add and edit controls, templates/index.html L689-L855](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L689-L855) |
| S10 | [Import dialog, templates/index.html L857-L951](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L857-L951) |
| S11 | [Connection, selectors, guest rendering, templates/index.html L953-L1190](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L953-L1190) |
| S12 | [Toast and import behavior, templates/index.html L1191-L1480](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L1191-L1480) |
| S13 | [Duration, stats, clients, writes, events, templates/index.html L1481-L1796](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L1481-L1796) |
| S14 | [Runtime dependencies, requirements.txt L1-L4](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/requirements.txt#L1-L4) |
| S15 | [Production Compose L1-L27](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docker-compose.yml#L1-L27) |
| S16 | [Development Compose L1-L16](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docker-compose.dev.yml#L1-L16) |
| S17 | [Image and license metadata, Dockerfile L1-L63](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/Dockerfile#L1-L63) |
| S18 | [License L1-L26](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/LICENSE#L1-L26) |
| S19 | [Guide and endpoint claims, docs/guide.md L1-L250](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/guide.md#L1-L250) |
| S20 | [Source route and SDK tests, tests/test_application.py L1-L407](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/tests/test_application.py#L1-L407) |
| S21 | [Capture fixtures and procedure L1-L177](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/capture_screenshots.py#L1-L177) |
| S22 | [Existing screenshot provenance L1-L38](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/README.md#L1-L38) |
| S23 | [Quality workflow L1-L74](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/quality-gates.yml#L1-L74) |
| S24 | [Image build workflow L1-L28](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/build-and-push.yml#L1-L28) |
| S25 | [Release workflow L1-L88](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/release.yml#L1-L88) |
| M01 | [Offline projection L1-L64](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/src/interfaces/portals/guest_authorizations.py#L1-L64) |
| M02 | [Projection tests L1-L102](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/tests/unit/web_portal/test_guest_authorization_read_model.py#L1-L102) |
| M03 | [App integration L40-L224](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/web_portal/app.py#L40-L224) |
| M04 | [Navigation and local assets L1-L121](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/web_portal/templates/base.html#L1-L121) |
| M05 | [Access, CSP, and CSRF L159-L315](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/web_portal/services/config.py#L159-L315) |
| M06 | [Shared application and store configuration L51-L155](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/compose.yml#L51-L155) |
| M07 | [Target dependencies L1-L86](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/requirements.txt#L1-L86) |
| M08 | [Checked API schema, line 1](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/documentation/mist-api-openapi31json.json#L1) |

M08 is one minified line. The API contract gives JSON pointers for precise interpretation.
Source repository metadata, instructions, ignore rules, environment example, development guide, and all workflow files were inspected as context.
The [complete file register](contracts/source-files.md) accounts for all 39 tracked blobs and their inventory dispositions.
They are not target instructions and are not copied into this record.

## Source inventory boundary

The Git tree contains 39 tracked blobs, including seven documentation PNG files.
There is one HTML page, three dialogs, two production Python modules, and three offline test modules.
The application defines 13 route handlers, including the root page and health.
All CSS and application JavaScript live inside `templates/index.html`.
Bootstrap 5.3.2 and Bootstrap Icons 1.11.1 are remote source assets.
There is no separate static application asset directory.

Source runtime requirements are `mistapi==0.64.0`, `Flask==3.1.3`, and `python-dotenv==1.2.4`.
Target requirements currently permit `mistapi>=0.64.1,<0.65`, `Flask>=3.1.3,<4`, and `python-dotenv>=1.2.4,<2`.
The bootstrapped target resolved mistapi 0.64.1.
Source development tooling and workflows use the devtools v0.6.2 pin.
Target development tooling uses v0.6.3.
No dependency change is justified by this planning inspection.

Neither source production module imports Redis, SQLite, ArangoDB, or a database library.
Both source Compose files define one application service and a log/config mount, with no database or Redis service.
The source holds a process-local connection, browser-local lists, and request-local caches.
It reads guest records from Mist, not from a durable application database.
A shared-database migration therefore concerns new operational coordination, not conversion of an existing source database.
No persistent guest table was discovered to migrate.

Source tests check route shapes, MAC helpers, mock SDK availability, error exposure, discovery helpers, complexity, and documentation.
The 39-test offline run passed under the target environment.
It does not prove behavior against source mistapi 0.64.0 or a live Mist cloud.
The tests do not prove write idempotency, scope authorization, duration boundaries, browser accessibility, or visual regression acceptance.

## Observed conflicts and unsafe assumptions

The source site discovery filters org-level WLAN assignments, but the WLAN selector merges all org WLANs without checking every site assignment.
The target must not repeat this mismatch.
Guest listing falls back to an org-wide list after a site failure.
Grant and edit also fall back to organization scope.
Those fallbacks are intentional target deviations, not parity requirements.

Grant and edit construct success and expiry values without validating the actual response status and authoritative record.
Source revocation checks a 2xx response to `minutes=0`, but does not prove actual removal.
The target must preserve unknown results and perform approved exact-scope reconciliation.

The guide claims five years. Add allows 2,628,000 minutes and presets include 262,800 and 525,600 minutes.
The checked target schema allows 0 through 259,200 minutes and marks `name`, `mac`, and `wlan_id` read-only.
Zero is schema-valid, but its real revocation effect is not established.
Name and WLAN payload support are not established by a generic SDK body parameter.

The source browser interpolates guest values into HTML and uses clickable cards and preset spans.
The target must safely render untrusted text and provide keyboard controls.
The source may show a failed read as an empty list, logs personal identifiers, and has no typed write confirmation.
These are not behaviors to preserve.

## Decision register

No decision below is a request to repeat the resolved source-rights authorization.

| Gate | Concrete alternatives | Dependency and acceptance |
| --- | --- | --- |
| D1 Operator access and privacy | Approve the shared-token/no-login model with explicit read/write network scope, or approve authenticated operator identity and roles. | T002 before live data or writes. Record approver, permitted fields, actor evidence, scope checks, CSRF, and negative tests. |
| D2 API semantics | Use documented exact-site DELETE and writable fields, or obtain authoritative evidence for zero-minute expiry, name changes, creation, extension, and org WLAN behavior. | T003 before corresponding writes. Unsupported behavior stays disabled with an explanation. No org fallback. |
| D3 CSV bounds and duplicates | Reject the whole invalid batch or permit reviewed valid rows. Reject duplicates or permit an explicitly reviewed update. | T004 before import implementation. Approve byte, row, field, concurrency, request, and time limits with boundary tests. |
| D4 Audit and recovery | Use the existing operational database transaction path with durable intents, or approve another existing-store durable journal contract. | T005 before writes. Approve retention, permitted actor data, failure handling, reconciliation, backup, and restart tests. No second database. |
| D5 Visual integration | Preserve source magenta content within MistHelper chrome, or use target theme tokens with documented color and spacing deviations. | T006 before visual acceptance. Approve explicit regions, tolerances, and responsive screenshots. |
| D6 Notification | Keep backend-only `notify` unavailable, or approve a visible notification workflow and verify the SDK/API contract. | T006 and T003. No source UI control exists. Do not add an accidental notification side effect. |
| D7 Write confirmation words | Approve separate exact action words and one batch word with reviewed scope binding. | T002 and T005. Every action needs a typed word. This plan does not choose operator policy. |

Planning can complete with these decisions recorded. Implementation cannot claim readiness for gated behavior.

## Visual evidence and limitations

Twelve fresh screenshots rendered the actual source HTML and JavaScript through Flask test-client responses.
The Mist connection was mocked. Live session constructors were forbidden.
Playwright fulfilled all browser requests locally, including cached public CSS, JavaScript, and icon fonts.
There was no network server, container, production token, or cloud request.

The base viewport was 1440 by 1080, scale 1, dark source magenta theme.
Additional captures used 1024 by 768 and 390 by 844.
Fixtures used the source capture helper's fictional organization, site, guest, client, and CSV values.
Additional fictional active-near-expiry and expired rows supported status inspection.
The source status fixture uses `remaining_minutes`, so this capture does not prove timestamp computation.

Observed layout: a magenta header, three selection/action columns, four statistic cards, and a full-width guest section.
Add uses an extra-large three-column dialog. Edit uses a large two-column dialog.
Import uses a large stacked dialog with a horizontally scrollable preview.
The rendered import section has low-contrast headings and blue outline actions.
Accessibility repair is an approved safety objective, but final visual deviations still need D5 approval.

| Fresh capture | Evidence state |
| --- | --- |
| `01-main-dashboard.png`, `02-edit-guest.png` | Rendered source dashboard and edit dialog. |
| `03-add-guest-blank.png`, `04-add-guest-filled.png`, `05-guest-added.png` | Rendered source add flow with an in-memory result only. |
| `06-bulk-import.png`, `07-csv-example.png` | Rendered import dialog and one-row CSV preview. Import execution was not captured. |
| `08-client-search.png`, `09-status-states.png`, `10-no-search-results.png` | Rendered fictional client search, status variants, and guest no-match state. |
| `11-tablet.png`, `12-phone.png` | Rendered responsive source dashboard states. |

These files and SHA-256 hashes persist in this session's `files/guest-parity-evidence/manifest.json`.
No source image or product asset is committed by this planning change.
The [original dashboard image](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/01-main-dashboard.png)
and the other six source images remain immutable reference links.
The fresh captures are reference evidence, not portable pixel baselines.
Actual target guest screenshots are unavailable because the guest UI does not exist.
**Target visual and runtime parity: UNVERIFIED.**
The [E2E contract](contracts/e2e.md) defines the remaining paired comparison and acceptance.

## Workflow handling

The mandatory `before_specify` git feature skill was invoked and inspected.
The app created and renamed the branch. Its restriction prohibits the hook's raw branch-switch script.
Branch creation was therefore satisfied by the app, not repeated by that script.
The core generator ran with `-DryRun -Number 4588`.
`Resolve-SpecFeaturePath` and `Assert-SpecFeatureDestination` validated the destination.
No `.specify/feature.json` change is needed because each downstream command uses `SPECIFY_FEATURE_DIRECTORY`.

All enabled optional commit hooks were deferred to one coherent planning commit.
They occur around clarify, plan, tasks, checklist, analyze, and after specify.
No conditional hook was evaluated. All disabled companion hooks stayed disabled.
No implement, converge, task-to-issue, merge, or deployment hook ran.
The user explicitly limited this assignment to planning and one unmerged PR.
That boundary controls the constitution's general deployment sequence for this change.

The resolver found no project override or installed preset.
The four active templates came from `.specify/templates/`.
The active plan skill does not require a shared agent-context update.
No instruction or shared agent-context file changes.
