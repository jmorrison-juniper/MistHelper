# Contract: Mist API calls for site application list and system events

## Scope

This contract names the SDK functions, the REST paths, and the pagination call that the two site exports use. The repair changes none of these calls. The source of each claim is the local OpenAPI file or the installed `mistapi` package.

## Application list (menu 213)

| Item | Value | Source |
| - | - | - |
| Repository call | `mistapi.api.v1.sites.wxtags.getSiteApplicationList(mh.apisession, site_id)` | `site_application_list_exporter.py` lines 91-93 |
| SDK signature | `getSiteApplicationList(mist_session: _APISession, site_id: str) -> _APIResponse` | `.venv\Lib\site-packages\mistapi\api\v1\sites\wxtags.py` line 89 |
| REST method and path | `GET /api/v1/sites/{site_id}/wxtags/apps` | `documentation\mist-api-openapi31yaml.yaml` lines 43213-43214 |
| Operation identifier | `getSiteApplicationList` | `documentation\mist-api-openapi31yaml.yaml` line 43216 |
| Coverage row | `getSiteApplicationList` | `documentation\MIST_API_GET_ENDPOINTS.md` line 1661 |
| Primary key strategy | `auto_increment_with_unique`, key `misthelper_internal_id` | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 483-489 |

## System events (menu 214)

| Item | Value | Source |
| - | - | - |
| Repository call | `mistapi.api.v1.sites.events.searchSiteSystemEvents(mh.apisession, site_id)` | `site_system_events_exporter.py` lines 91-93 |
| SDK signature | `searchSiteSystemEvents(mist_session, site_id, type=None, limit=None, start=None, end=None, duration=None, sort=None, search_after=None)` | `.venv\Lib\site-packages\mistapi\api\v1\sites\events.py` lines 134-144 |
| REST method and path | `GET /api/v1/sites/{site_id}/events/system/search` | `documentation\mist-api-openapi31yaml.yaml` lines 32015-32016 |
| Operation identifier | `searchSiteSystemEvents` | `documentation\mist-api-openapi31yaml.yaml` line 32020 |
| Coverage row | `searchSiteSystemEvents` | `documentation\MIST_API_GET_ENDPOINTS.md` line 1245 |
| Primary key strategy | `composite_pk`, keys `type` and `timestamp` | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 520-526 |

The repository call passes no filter. The SDK defaults for `type`, `limit`, `start`, `end`, `duration`, `sort`, and `search_after` apply.

## Pagination

| Item | Value | Source |
| - | - | - |
| Repository call | `mistapi.get_all(response=response, mist_session=mh.apisession)` | both exporters, line 94 |
| SDK signature | `get_all(mist_session: _APISession, response: _APIResponse) -> list` | `.venv\Lib\site-packages\mistapi\__pagination.py` line 39 |
| Export | `get_all` is exported from the package | `.venv\Lib\site-packages\mistapi\__init__.py` line 15 |

The keyword names match the SDK signature. The repository call does not forward `*args` or `**kwargs`, which the SDK compatibility rule forbids.

## Transport rules

- The exports use the SDK only. No direct HTTP request is made.
- No owned WebSocket transport exists. The owned-transport contract tests are not applicable.
- The SDK installed is version 0.64.1. `requirements.txt` line 129 pins that version. `pyproject.toml` line 29 allows `>=0.64.1,<0.65`.

## Failure behavior

An SDK or network error inside the menu handler is caught by `except Exception as e` (exporter lines 96-98). The handler logs the error with the site name and returns. The repair does not change this path.
