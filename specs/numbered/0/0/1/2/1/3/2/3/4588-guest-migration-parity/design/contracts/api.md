# SDK and portal contracts

## Pinned contract evidence

The target environment resolved mistapi 0.64.1.
Its upstream tag points to `0544d85b6e123fe5850dce4177bfa1a3bd1086e6`.
The source pin uses mistapi 0.64.0, upstream `66a57a64f2cae222da36c3a45a639c2a70c54156`.

[Target SDK site guests](https://github.com/tmunzer/mistapi_python/blob/0544d85b6e123fe5850dce4177bfa1a3bd1086e6/src/mistapi/api/v1/sites/guests.py)
and [org guests](https://github.com/tmunzer/mistapi_python/blob/0544d85b6e123fe5850dce4177bfa1a3bd1086e6/src/mistapi/api/v1/orgs/guests.py)
provide method evidence.
Installed functions were inspected with `inspect.signature` and `inspect.getsource`.
The methods pass a generic body to the SDK session and do not validate every guest field.

The [target schema](https://github.com/jmorrison-juniper/MistHelper/blob/772fc927761b61dea8beb7f708fbbe78c2a38d86/documentation/mist-api-openapi31json.json#L1)
reports version `2609.1.0`, dated September 7, 2026.
Precise JSON pointers are `/components/schemas/guest` and
`/paths/~1api~1v1~1sites~1{site_id}~1guests~1{guest_mac}`.

| Contract | Reverified local evidence | Remaining acceptance |
| --- | --- | --- |
| List | `listSiteAllGuestAuthorizations(mist_session, site_id, wlan_id=None)` | TEST-003/005 proves exact filtering, response shape, and malformed/denied/unavailable outcomes. |
| Derived list | `listSiteAllGuestAuthorizationsDerived(mist_session, site_id, wlan_id=None, cross_site=None)` exists. | No cross-site expansion is permitted without a separate explicit scope decision. |
| Record read | `getSiteGuestAuthorization(mist_session, site_id, guest_mac)` | TEST-022 verifies authoritative reconciliation and normalized path MAC. |
| Update | `updateSiteGuestAuthorization(mist_session, site_id, guest_mac, body)` sends SDK `mist_put`. | TEST-011/012/013/022 must verify creation, writable fields, extension semantics, and result observation. |
| Delete | `deleteSiteGuestAuthorization(mist_session, site_id, guest_mac)` sends SDK `mist_delete`. | TEST-014 verifies exact scope and resulting observation. A 200 alone does not prove removal. |
| Duration | Integer `minimum: 0`, `maximum: 259200`, default 1440. | TEST-011 covers -1,0,1,259199,259200,259201,262800,525600,2628000 and nonintegers. Zero is not proven revocation. |
| Read-only fields | `name`, `mac`, `wlan_id`, `ssid`, `authorized_time`, `authorized_expiring_time`, `auth_method`, `ap_mac`, `random_mac`, `access_code_email`. | Never send read-only body fields without authoritative new contract evidence. MAC remains a path parameter. |
| Candidate writable fields | `authorized`, `minutes`, `company`, `email`, `field1` through `field4`. | D1/D2 controls permitted use and empty-field semantics. Generic body support proves no additional field. |
| Notification | Source accepts `notify`, but checked guest schema does not declare it. | D6 disables notification unless authoritative contract and explicit approval exist. |

Official update and delete documentation URLs were fetched on 2026-11-05.
They redirected to `networkingdocs.hpe.com` and returned only the API reference shell.
Context7 returned status-code guidance, not the disputed field or revocation semantics.
Neither result resolves D2. No live API request was made.

## Complete source SDK inventory

These twelve source methods were discovered in `mist_connection.py`.
Each future use must pass explicit named arguments and inspect status and response shape.

| Source method suffix under `mistapi.api.v1` | Future disposition | Acceptance |
| --- | --- | --- |
| `self.self.getSelf` | Reuse only if needed by shared session/identity discovery. Never auto-select an organization or treat token name as actor identity. | TEST-002,TEST-010,TEST-020 |
| `orgs.orgs.getOrg` | Explicit selected org validation through the existing session. | TEST-002,TEST-020 |
| `orgs.sites.listOrgSites` | Approved org scope, bounded pagination, sorted site summaries. | TEST-003 |
| `orgs.wlans.listOrgWlans` | Apply org WLAN assignment checks before display. | TEST-003,TEST-022 |
| `orgs.templates.getOrgTemplate` | Verify site and sitegroup assignments. Failure is unavailable. | TEST-003 |
| `orgs.sitegroups.getOrgSiteGroup` | Resolve permitted site membership without expanding scope. | TEST-003 |
| `sites.wlans.listSiteWlans` | Combine applicable site and org WLANs by verified ID. | TEST-003 |
| `sites.guests.listSiteAllGuestAuthorizations` | Exact site and WLAN read. | TEST-005,TEST-022 |
| `orgs.guests.listOrgGuestAuthorizations` | Exclude as a fallback. Use only a separately approved explicit org workflow, if later required. | TEST-022 |
| `sites.guests.updateSiteGuestAuthorization` | Conditional grant/edit/extend operation after D2/D4/D7. | TEST-009,TEST-012,TEST-013,TEST-022 |
| `orgs.guests.updateOrgGuestAuthorization` | Exclude as a fallback. No current requirement approves an org-wide write. | TEST-022 |
| `sites.stats.listSiteWirelessClientsStats` | Explicit site, bounded pages, permitted client details. Signature also accepts `wired`, `limit`, `start`, `end`, and `duration`. | TEST-008 |

The source also uses `mistapi.APISession` and `mistapi.get_all`.
The target must reuse its session rather than construct a second one.
The installed org delete/get/search methods exist but do not authorize scope expansion.
Future mocks must test nonexception 400/401/403/404/429 and 5xx responses as well as raised errors.
Inspect the SDK's own retry behavior before writes. Application-level no-retry rules cannot override an unseen SDK retry.

## Proposed portal surface

The source's 13 route handlers account for these interfaces.
The exact target URL namespace below is a design proposal inside one blueprint.
T007 confirms registration ownership. D1 controls route availability.

| Source surface | Proposed target surface | Contract |
| --- | --- | --- |
| `/` | `/guest-authorizations/` | Existing portal shell, stable guest tab and scoped content. |
| `POST /api/test-connection` | `GET /guest-authorizations/api/connection` | Read-only shared-session status. No source token setup or implicit org selection. |
| `GET /api/sites` | `GET /guest-authorizations/api/sites` | Approved org binding and accurate absence versus failure. |
| `GET /api/sites/<site_id>/wlans` | `GET /guest-authorizations/api/sites/<site_id>/wlans` | Exact applicable guest WLAN list. |
| `GET /api/sites/<site_id>/wlans/<wlan_id>/guests` | Scoped guest review API in the feature namespace. | Verified scope, observation revision, and permitted projection. |
| `POST` source guests | Review/confirm grant within the scoped feature API. | CSRF, approved actor, typed confirmation, durable intent, exact payload. |
| `PUT` source guest | Review/confirm edit or extension for exact record identity. | Separate detail and duration actions. No implicit extension. |
| `DELETE` source guest | Review/confirm revoke for exact record identity. | D2 controls the SDK operation. Browser verb does not establish cloud semantics. |
| `GET /api/sites/<site_id>/clients/search` | Scoped client search in the feature API. | Permit only exact-site search and approved client fields. |
| `GET /api/csv-template` | `/guest-authorizations/api/csv-template` | Fictional examples, supported header aliases, no secret payload. |
| `GET /api/sites-wlans-map` | Scoped import validation service. | Server-side unambiguous ID resolution. No unbounded browser-global mapping authority. |
| `POST /api/bulk-import` | Batch preview, confirmation, execution, and status APIs. | Reviewed immutable rows, D3 limits, D4 audit, no per-row blind replay. |
| `/health` | Existing MistHelper health surface. | No second application health server. |

Source payloads and URLs do not become public target compatibility promises.
Target response categories include unavailable, denied, invalid, stale, rejected, success, unknown, and unstarted.
Bind all responses to an opaque operation or revision reference and exact permitted scope.
Never place a credential or private rejected payload in a URL, error, log, or screenshot.

## Confirmation and audit contract

Before dispatch, validate the action, actor, scope, payload, observed revision, and exact typed word.
A new revision, changed payload, or changed scope invalidates confirmation.
Persist the approved intent before sending a write.
After dispatch, classify the actual response and reconcile through approved exact-scope reads.
Do not broaden scope, invent expiry, or automatically repeat an ambiguous write.
If audit persistence fails, apply D4 and report the failure explicitly.
The plan does not claim a durable audit implementation exists.
