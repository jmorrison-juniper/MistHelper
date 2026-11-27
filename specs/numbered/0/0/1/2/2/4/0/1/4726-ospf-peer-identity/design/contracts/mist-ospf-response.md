# Contract: Mist OSPF Search Response

This contract defines the API shape that the change reads. The change does not alter any request. It reads the response records that the existing exporters pass to the writers.

## SDK Calls

| Menu | SDK function | Installed source | Required path argument |
| - | - | - | - |
| 70 and 225 | `searchSiteOspfStats` | `.venv\Lib\site-packages\mistapi\api\v1\sites\stats.py`, definition at line 1868 (RV-83) | `site_id` |
| 55 | `searchOrgOspfStats` | `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py`, definition at line 867 (RV-84) | `org_id` |

Each signature accepts the optional query arguments `mac`, `vrf_name`, `peer_ip`, `start`, `end`, `limit`, `sort`, and `search_after`. The org signature also accepts `site_id`. The installed package version is 0.64.1 (RV-85).

## Documented Operations

- `searchOrgOspfStats` is documented at line 21735 of `documentation\mist-api-openapi31yaml.yaml` (RV-46).
- `searchSiteOspfStats` is documented at line 40123 of the same file (RV-47).
- Each OSPF search operation returns the component `OspfPeersStatsSearch`, which is defined at line 64492 (RV-101).
- That component uses the paginated schema `ospf_peer_stats_search_result`, defined at line 91223 (RV-102).

## Record Shape

The record is one entry of the search result. The item schema lives at lines 91259 to 91310 of the OpenAPI file (RV-49).

| Property | Type | Used by this change |
| - | - | - |
| `mac` | string | Yes. Required identity component. |
| `neighbor` | string | Yes. Neighbor identity component (RV-50). |
| `peer_ip` | string, deprecated | Yes. Fallback neighbor component (RV-51). |
| `port_id` | string | Yes. Scope component (RV-52). |
| `vrf_name` | string | Yes. Scope component (RV-53). |
| `timestamp` | number | Yes. Required identity component, epoch seconds (RV-54). |
| `state`, `up`, `priority`, `dead_time`, `neighbor_id`, `site_id`, `org_id` | mixed | No. These fields pass through to the outputs unchanged. |

The item schema forbids additional properties (RV-48). The schema declares no required field (RV-49). The writer therefore checks each identity component itself.

## Failure Behavior

- A response that the exporter cannot write keeps the existing error handling. This change does not alter that handling.
- A record that lacks a required identity component causes a rejected batch. The rejection rule is defined in `design/contracts/ospf-peer-identity.md`.
