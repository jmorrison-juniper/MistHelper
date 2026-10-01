# Research: Mist Edge Lifecycle Operation

## Skill evidence

- `juniper-mist-wireless/01-architecture-and-ap-platforms/01-wireless-assurance-architecture-and-sles.md`: Mist Edge supplies the centralized on-site data path while Mist cloud keeps control and management functions.
- `juniper-mist-aiops/02-insights/05-wan-edge-mist-edge-and-cellular-edge-insights.md`: Mist Edge Insights shows `Mist Edge Events`, `Port Charts`, `AP Tunnel Bounce by User`, `AP Tunnel Bounce Success`, `Tunnel Interface Bounced by User`, and LACP tunnel events.
- `juniper-mist-management/04-subscriptions-and-orders/01-wireless-and-wired-subscriptions.md`: Mist Edge data tunneling uses `S-ME-S-1|3|5`, and the subscription count must match APs tunneling to Mist Edges.
- `juniper-hw-mist-edge/02-ports-oobm-idrac.md`: The `MIST` port is out-of-band management, and data ports terminate `AP` tunnels and carry tunneled user `VLAN` traffic.
- `juniper-hw-mist-edge/11-upgrades-and-events.md`: A tunnel service upgrade can take up to `5 minutes`, and a service plus OS upgrade can take about `30 minutes` per appliance.
- `juniper-hw-mist-edge/12-troubleshooting-capture-and-marvis.md`: Operators should use events before service restart, and should not restart service first for `OOBM`, firewall, `LACP`, or hardware faults.
- `juniper-mist-management/02-organization-sites-and-inventory/03-inventory-claims-autoprovisioning-and-firmware.md`: Inventory actions include claim, assign, rename, and release from `Organization > Admin > Inventory`.
- `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`: The portal is the API, and `POST` or `PUT` calls represent saves.

## Existing read operations

- Menu 50 uses `src/export/org_config_exporter.py` and calls `mistapi.api.v1.orgs.mxedges.listOrgMxEdges` to export `OrgMxEdges.csv`.
- Menu 71 and related read-only exporters use `listOrgMxEdgeUpgrades` and `getOrgMxEdgeUpgradeInfo` in `src/export/simple_endpoint_exporter.py` and `src/org_data_collector.py`.

## OpenAPI and SDK findings

| Operation | Method and path | Parameters | Request body | SDK |
| - | - | - | - | - |
| `listOrgMxEdges` | `GET /api/v1/orgs/{org_id}/mxedges` | `org_id`, optional `for_site`, `limit`, `page` | none | `mistapi.api.v1.orgs.mxedges.listOrgMxEdges(session, org_id, for_site=None, limit=None, page=None)` |
| `claimOrgMxEdge` | `POST /api/v1/orgs/{org_id}/mxedges/claim` | `org_id` | `{"code": "135-546-673"}` | `claimOrgMxEdge(session, org_id, body)` |
| `assignOrgMxEdgeToSite` | `POST /api/v1/orgs/{org_id}/mxedges/assign` | `org_id` | `{"mxedge_ids": ["<id>"], "site_id": "<site-id>"}` | `assignOrgMxEdgeToSite(session, org_id, body)` |
| `unassignOrgMxEdgeFromSite` | `POST /api/v1/orgs/{org_id}/mxedges/unassign` | `org_id` | `{"mxedge_ids": ["<id>"]}` | `unassignOrgMxEdgeFromSite(session, org_id, body)` |
| `bounceOrgMxEdgeDataPorts` | `POST /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/tunterm/bounce_port` | `org_id`, `mxedge_id` | `{"ports": ["0", "2"]}` or `{"hold_time": 0, "ports": ["string"]}` | `bounceOrgMxEdgeDataPorts(session, org_id, mxedge_id, body)` |
| `upgradeOrgMxEdges` | `POST /api/v1/orgs/{org_id}/mxedges/upgrade` | `org_id` | `{"mxedge_ids": ["<id>"], "versions": {"tunterm": "default"}, "strategy": "serial"}` plus optional fields | `upgradeOrgMxEdges(session, org_id, body)` |
| `listOrgMxEdgeUpgrades` | `GET /api/v1/orgs/{org_id}/mxedges/upgrade` | `org_id` | none | `listOrgMxEdgeUpgrades(session, org_id)` |
| `getOrgMxEdgeUpgrade` | `GET /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}` | `org_id`, `upgrade_id` | none | `getOrgMxEdgeUpgrade(session, org_id, upgrade_id)` |

## Decisions

### Decision 1: Use the SDK functions directly

The installed SDK contains each required function in `mistapi.api.v1.orgs.mxedges`. The client calls those functions directly instead of raw `mist_post` or `mist_get`.

### Decision 2: Redact claim codes at the model boundary

The claim request body contains the code, but log rows and logger messages use the fixed redaction value `REDACTED`. This keeps the claim code out of logs before the request reaches the client.

### Decision 3: Poll one upgrade identifier

The upgrade response can return an upgrade identifier. If it does not, the operation reads the upgrade list and selects the newest upgrade that mentions a requested Mist Edge. Polling then calls `getOrgMxEdgeUpgrade` until a terminal status or timeout.

### Decision 4: Defer menu wiring

The fleet contract forbids edits to `MistHelper.py`, `OperationRegistry`, and primary key strategy files. The exact menu wiring appears in `wiring.md` for the integration pull request.
