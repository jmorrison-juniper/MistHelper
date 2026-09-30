# Research: Synthetic Test Trigger

## Decision: Use the documented Mist synthetic test operation IDs

Rationale: `documentation/mist-api-openapi3json.json` defines these operations.

| operationId | Method and path | Parameters | Body schema | Success shape |
| - | - | - | - | - |
| `triggerSiteSyntheticTest` | `POST /api/v1/sites/{site_id}/synthetic_test` | path `site_id` | `synthetictest` with optional `email` | `response_synthetictest` with `id`, `message`, and `status` |
| `triggerSiteDeviceSyntheticTest` | `POST /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test` | path `site_id`, `device_id` | `synthetictest_device` with required `type` | Empty `200` response named `Scheduled` |
| `startSiteSwitchRadiusSyntheticTest` | `POST /api/v1/sites/{site_id}/devices/{device_id}/check_radius_server` | path `site_id`, `device_id` | `synthetictest_radius_server` with required `user` and `password`, and default `profile` `dot1x` | `websocket_session` |
| `searchSiteSyntheticTest` | `GET /api/v1/sites/{site_id}/synthetic_test/search` | path `site_id`; query `mac`, `port_id`, `vlan_id`, `by`, `reason`, `type`, `protocol`, and `tenant` | None | `response_synthetictest_search` with `results` array |
| `getSiteDeviceSyntheticTest` | `GET /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test` | path `site_id`, `device_id` | None | `synthetictest_info` |

Alternatives considered: A direct `apisession.mist_post` fallback was not selected, because the installed SDK exposes all five functions.

## Decision: Use the installed `mistapi` SDK functions

Rationale: Local inspection found `mistapi.api.v1.sites.synthetic_test.triggerSiteSyntheticTest`, `mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest`, `mistapi.api.v1.sites.devices.triggerSiteDeviceSyntheticTest`, `mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest`, and `mistapi.api.v1.sites.devices.startSiteSwitchRadiusSyntheticTest`.

Alternatives considered: Raw REST calls would duplicate SDK URL construction and would add risk without adding value.

## Decision: Poll the existing result endpoints

Rationale: Menus `33` and `34` already use `getSiteDeviceSyntheticTest` for synthetic test result reads. The site scope uses `searchSiteSyntheticTest` with the safe query values from the request.

Alternatives considered: A websocket session from the RADIUS endpoint was not selected for the MVP, because the assignment requires polling the result endpoint.

## Decision: Keep RADIUS password only in the trigger body

Rationale: The Marvis Minis wired validation uses a `RADIUS` authentication request from a switch. A reject can be a pass because it proves the server answered. The assignment requires the shared secret to be masked everywhere outside the Mist request body. Source: `juniper-mist-aiops/06-marvis-minis/02-wireless-and-wired-validation-steps.md`.

Alternatives considered: Exporting a masked password was rejected because the acceptance criteria require that the secret is never written to the output file.

## Decision: State operator context in the documentation

Rationale: WAN testing tools include on-demand checks and speed test limits from `1 Mbps` through `1 Gbps`. This feature starts synthetic tests, not WAN speed tests. Source: `juniper-mist-wan/10-monitoring-sles-and-troubleshooting/03-testing-tools-speed-tests-pcap-and-platform-troubleshooting.md`.

Alternatives considered: Adding speed test-specific validation was rejected because the API body supports multiple synthetic test types and the issue is broader than WAN speed tests.

## Decision: Follow the Mist REST API model

Rationale: Mist uses regional REST hosts and JSON payloads. `POST` creates or starts the action, and each request carries its own identity. Source: `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`.

Alternatives considered: No alternate transport is needed for this single-run operation.

## Decision: Reuse switch selection and site prompt helpers

Rationale: The switch utility page defines operator device selection around `Switches > Switch Name` and `Utilities`. The codebase already holds `PromptUtils.select_site_with_logging` and `PromptUtils.select_device_id_from_inventory` for this interactive flow. Source: `juniper-mist-wired/09-wired-visibility-and-switch-management/03-switch-utilities-roles-remote-shell-and-replacement.md`.

Alternatives considered: New prompt helpers were rejected because they would duplicate menu behavior and increase operator inconsistency.
