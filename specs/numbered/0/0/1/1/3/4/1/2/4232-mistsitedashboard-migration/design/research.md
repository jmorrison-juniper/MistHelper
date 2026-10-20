# Research: Site health dashboard

## Evidence and provenance

Inspected source revision `eb3b7e47928a25b6a4e6b7a2756520208e962074` on 2026-10-18 UTC.
The inspection used an isolated source checkout outside the product worktree.
No source code, image, certificate, or template enters MistHelper.

Pinned source evidence:

- [License](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/LICENSE)
- [Operator guide](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/docs/user-guide.md)
- [Application routes](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/app.py)
- [SDK connection code](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/mist_connection.py)
- [Templates](https://github.com/jmorrison-juniper/MistSiteDashboard/tree/eb3b7e47928a25b6a4e6b7a2756520208e962074/templates)
- [Dependencies](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/requirements.txt)
- [Deployment](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/docker-compose.yml)
- [Screenshot provenance](https://github.com/jmorrison-juniper/MistSiteDashboard/blob/eb3b7e47928a25b6a4e6b7a2756520208e962074/docs/offline-screenshots.md)

## Workflow inventory

| Source evidence | Useful behavior to preserve | Requirements |
| --- | --- | --- |
| `app.py:292-332`, `templates/index.html:797-914` | Searchable site selection, category tabs, metric cards, worst-100 table, site links | FR-001 to FR-003 |
| `templates/site.html:248-435`, synthetic `offline-site.png` | Site heading, three health cards, three SLE cards, period selector, then device tables | FR-004, FR-005 |
| `templates/index.html:1037-1152` | AP SSIDs, clients, port speed, power, uptime, serial, notes. Switch AP/client counts. Gateway state. | FR-004 |
| `app.py:868-902`, `templates/ap_clients.html`, `templates/switch_clients.html` | Wireless sessions and wired history, sortable/filterable rows and table exports | FR-007 |
| `app.py:902-983`, `templates/gateway_wan.html:556-625` | WAN ports, expandable VPN and BGP peers, peer availability | FR-007 |
| `app.py:986-1156`, three SLE templates | Classifiers, impact bars, distribution dialogs, affected-item tables and dynamic columns | FR-005, FR-006 |
| `app.py:1157-1271` | Category CSV export | FR-006 |
| `templates/index.html` refresh controls, source route error handlers | Manual organization refresh, individual metric retry, visible errors | FR-008 |

The synthetic site screenshot confirms the information order directly.
It also shows low-contrast text on some cards.
Preserve the information hierarchy, not that contrast defect or protected branding.
VPN tables include latency, jitter, loss, MOS, and uptime.
BGP tables include neighbor, VRF, local and neighbor AS, state, route counts, and uptime.
Wireless client views include history summaries, unique clients, SSIDs, search, and client details.
The detailed SLE pages use responsive dialogs and category CSV controls.
No source template contains an automatic refresh timer.

## License and dependencies

**Decision**: Do not copy source expression or assets. Implement only independently specified behavior.

**Rationale**: `LICENSE` declares CC BY-NC-SA 4.0, copyright 2025 jmorrison-juniper.
It requires attribution, noncommercial use, and share-alike distribution for adaptations.
Repository ownership does not itself record a separate license grant.
Commercial use and adaptation compatibility remain unresolved.

**Alternatives considered**: Copying the Flask application, importing its templates, or embedding its container.
All require reuse approval and introduce an unwanted second application.

The runtime manifest declares `mistapi>=0.64.0,<1`, `requests>=2.34.2,<3`, `Flask>=3.1.3,<4`,
`Werkzeug>=3.1.9,<4`, `python-dotenv>=1.2.4,<2`, and `keyring>=25.7.0,<26`.
Templates load Bootstrap 5.3.2 and Bootstrap Icons 1.11.1 from jsDelivr.
Do not introduce these CDN dependencies or copy their bundled assets in this slice.
Use MistHelper's existing dependency constraints and theme in future UI work.
Source development tools include pytest, Ruff, Black, mypy, Bandit, pip-audit, Vulture, and pinned shared devtools.
`perf_monitor.py` instruments SDK request timing. Reuse existing MistHelper logging instead of copying that module.

## Deployment and data

**Decision**: Use the existing MistHelper application and configured store.

**Rationale**: Source Compose declares one application on port 5000 with a `config` mount.
It declares no database and no Redis service.
The source caches its API session in a process singleton.
There is no demonstrated source Redis dependency.

Source configuration reads `MIST_APITOKEN`, `MIST_HOST`, `MIST_ORG_ID`, legacy `org_id`, `TZ`, and `LOG_LEVEL`.
Reuse MistHelper's server-owned session and configured organization.
Do not select the first available organization automatically.
Retain cloud region configuration without passing credentials through the browser.
Source POST `/api/test-connection` performs read calls. No inspected source dashboard route changes Mist or devices.

**Alternatives considered**: A second container, separate SQLite file, or new Redis cache.
These add duplicate operational state without source evidence.

## API and behavioral discrepancies

Installed SDK inspection found 24 distinct source-referenced typed methods.
All 24 symbols import successfully, including five indirect affected-item methods.
The candidate `orgs.insights.getOrgSitesSle` also imports, but addresses `/insights/sites-sle`.
It is not proof of parity with the source `/insights/worst-sites-by-sle`.
The local OpenAPI paths contain no `worst-sites-by-sle` match.
See [API contracts](contracts/api.md) for the complete inventory.

Source `mist_connection.py:2298-2331` claims an undocumented `limit` and contains contradictory category/metric comments.
Source metric-specific collection uses the same private endpoint at lines 2484-2498.
These are exact contract gaps, not reasons to add direct HTTP.

Source `index.html:824` offers `5m`, while `app.py:653-666` accepts `10m` instead.
Source `site.html:307-312` offers `3h`, `6h`, `12h`, and `7d`.
The site summary route accepts `10m`, `1h`, `today`, `1d`, and `1w`.
Resolve these inconsistencies through explicit SDK contract fixtures before wiring periods.
Source `mist_connection.py:831-840` derives percentages from sample totals.
The new model accepts normalized counts only and does not copy that helper.

## Open blockers

| ID | Exact missing evidence | Affected work | Required decision or proof |
| --- | --- | --- | --- |
| B01 | No separate reuse grant in issue #4232 or its comment | Source code, screenshots, branding, templates | Owner-approved license path and compatibility review |
| B02 | Private worst-sites endpoint lacks a matching typed SDK method and local schema | Organization worst-100 parity | Supported SDK contract and fixture proof |
| B03 | Source templates and routes disagree on periods | Live site and organization time filters | Verified accepted periods and UTC semantics |
| B04 | Symbol imports do not prove payloads, scope permissions, pagination, or failure shape | All live collectors | Sanitized fixtures and SDK request contract tests |
| B05 | Portal has network controls, not user authentication | Per-user access and sensitive exports | Approved access model and permission matrix |
| B06 | PR #4208 owns `web_portal/app.py` and `web_portal/templates/base.html` | Navigation, registration, WAN reuse | Explicit file handover and bounded package decision |
| B07 | No deployment or live-access approval | Publication and production verification | Separate operator approval |

The offline model does not consume protected expression, live data, or scoped identifiers.
These blockers do not prevent its independent implementation.
