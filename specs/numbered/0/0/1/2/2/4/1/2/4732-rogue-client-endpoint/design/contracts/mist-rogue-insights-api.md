# Contract: Mist rogue insights API shape

This contract names the Mist REST operations that the rogue exports call. It cites the local OpenAPI file and the installed mistapi SDK. The record does not call the live API.

## Client operation

- **Method and path**: `GET /api/v1/sites/{site_id}/insights/rogues/clients` (`documentation/mist-api-openapi31yaml.yaml:32830`).
- **operationId**: `listSiteRogueClients` (`documentation/mist-api-openapi31yaml.yaml:32833`).
- **Tag**: `Sites Rogues`.
- **Path parameter**: `site_id`.
- **Query parameters**: `limit`, `start`, `end`, `duration`, and `interval` (`documentation/mist-api-openapi31yaml.yaml:32834-32839`).
- **Response 200**: the component `InsightRogueClients` (`documentation/mist-api-openapi31yaml.yaml:62798`). The response schema `response_insight_rogue_client` holds the `results` array (`documentation/mist-api-openapi31yaml.yaml:94841-94857`). Each item uses the schema `insight_rogue_client` (`documentation/mist-api-openapi31yaml.yaml:94868-94871`).
- **Error responses**: 400, 401, 403, 404, and 429 (`documentation/mist-api-openapi31yaml.yaml:32843-32852`). The 200 response references `InsightRogueClients` at `documentation/mist-api-openapi31yaml.yaml:32841-32842`.

### Item schema `insight_rogue_client`

Properties: `annotation`, `ap_mac`, `avg_rssi`, `band`, `bssid`, `client_mac`, and `num_aps` (`documentation/mist-api-openapi31yaml.yaml:81833-81857`).

Required properties: `bssid`, `ap_mac`, `client_mac`, `num_aps`, `band`, `avg_rssi`, and `annotation` (`documentation/mist-api-openapi31yaml.yaml:81858-81866`).

The schema sets `additionalProperties: false`. The primary key fields `client_mac` and `bssid` are both required.

## AP operation

- **Method and path**: `GET /api/v1/sites/{site_id}/insights/rogues` (`documentation/mist-api-openapi31yaml.yaml:32801`).
- **operationId**: `listSiteRogueAPs` (`documentation/mist-api-openapi31yaml.yaml:32804`).
- **Item schema**: `insight_rogue_ap` (`documentation/mist-api-openapi31yaml.yaml:81788`).
- **Required properties**: `ap_mac`, `avg_rssi`, `bssid`, `channel`, and `num_aps` (`documentation/mist-api-openapi31yaml.yaml:81826-81831`).

## Query limit

The `limit` parameter defaults to 100 and has a minimum of 0. The component sets no maximum (`documentation/mist-api-openapi31yaml.yaml:59742-59749`). The code sends `limit=1000` (`org_client_security_exporter.py:165`). The live response to that value is not verified (research item U-B).

## SDK call

- **Installed function**: `mistapi.api.v1.sites.insights.listSiteRogueClients` with the parameters `mist_session`, `site_id`, `limit`, `start`, `end`, `duration`, and `interval` (`.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py:495-503`).
- **AP function**: `listSiteRogueAPs` at `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py:434`.
- **Call in MistHelper**: `fetch_callable(mh.apisession, site_id, duration=rogue_duration, limit=1000)` (`org_client_security_exporter.py:163-165`). The collector passes the function at `org_client_security_exporter.py:88`. The call passes explicit arguments, as the constitution requires.
- **Documentation drift**: The SDK page names `mistapi.api.v1.sites.rogues.listSiteRogueClients()` (`documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md:136`). Phase 1 corrects this line (FR-010).
