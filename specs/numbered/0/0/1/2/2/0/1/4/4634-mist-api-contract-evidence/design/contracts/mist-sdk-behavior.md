# Contract: Mist SDK Behavior

This contract records the behavior of the pinned mistapi 0.64.1 source that the write operations use. The source sits in `.venv\Lib\site-packages\mistapi`, which the repository tree does not hold. Each line number below comes from a read-only view of that file. The tests pin each behavior named here.

## Retry and Session Behavior

| ID | Behavior | Source (mistapi 0.64.1) | Value | Test |
| --- | --- | --- | --- | --- |
| SB-01 | Retry limit for HTTP 429 | `__api_request.py` line 59 | `_MAX_429_RETRIES = 3` | Test 13 |
| SB-02 | Base wait when no `Retry-After` header exists | `__api_request.py` line 60 | `_DEFAULT_RETRY_AFTER = 5` | Test 14 |
| SB-03 | Wait formula after HTTP 429 | `__api_request.py` lines 186 to 194 | numeric `Retry-After` seconds, otherwise 5 times 2 to the power of the attempt | Test 14 |
| SB-04 | Attempt loop | `__api_request.py` line 209 | `range(_MAX_429_RETRIES + 1)`, so four attempts in total | Test 13 |
| SB-05 | Retry branch | `__api_request.py` line 229 | retry only for HTTP 429 while attempts remain | Tests 13 and 15 |
| SB-06 | Token rotation before a retry | `__api_request.py` line 237 | `_next_apitoken()` runs, and a single token is tolerated | Test 13 |
| SB-07 | Success exit | `__api_request.py` line 220 | `break` after `raise_for_status` passes | Test 16 |
| SB-08 | Proxy and connection errors | `__api_request.py` lines 221 to 227 | `break` with no retry | Test 15 |
| SB-09 | Other HTTP errors | `__api_request.py` line 249 | `break` with no retry | Test 16 |
| SB-10 | Other exceptions | `__api_request.py` line 255 | `break` with no retry | Test 15 |
| SB-11 | Shared loop for every verb | `__api_request.py` lines 203 and 277 | `mist_get` and the write verbs call the same `_request_with_retry` | Tests 11 and 13 |
| SB-12 | Write verbs | `__api_request.py` lines 279, 303, and 327 | `mist_post`, `mist_put`, and `mist_delete` | Test 11 |
| SB-13 | Session calls for writes | `__api_request.py` lines 300, 324, and 343 | `post` and `put` send `json` and `headers`, and `delete` sends only the URL | Test 11 |
| SB-14 | No timeout on writes | `__api_request.py` lines 300, 324, and 343 | no `timeout` argument | Test 11 |
| SB-15 | Session object | `__api_session.py` line 129 | `requests.session()` with no default timeout | Test 11 |
| SB-16 | Only literal timeout in the session module | `__api_session.py` line 576 | `timeout=30` belongs to `_get_api_token_data`, not to a REST write | Test 11 |
| SB-17 | Response wrapper | `__api_response.py` line 22 | `APIResponse` holds `status_code`, `data`, `headers`, and `next` | Test 16 |

Caution: The SDK retries HTTP 429 for each write verb (SB-05 and SB-11). A repeated create can duplicate an object if the service applied the first request. Decision D-5 counts each repeat as one attempt. The executor reads back before any retry.

Caution: No timeout bounds a REST write call in the SDK (SB-14). An executor must set its own bound. Record 4644 (D-8) sets 90 seconds for each write.

## Logging Behavior

| ID | Behavior | Source (mistapi 0.64.1) | Value | Test |
| --- | --- | --- | --- | --- |
| SB-18 | Request body log for POST | `__api_request.py` line 296 | `logger.debug` with the body | Redaction evidence is not in this change |
| SB-19 | Request body log for PUT | `__api_request.py` line 320 | `logger.debug` with the body | Redaction evidence is not in this change |
| SB-20 | Header redaction | method `_remove_auth_from_headers` | replaces the `Authorization`, `X-CSRFToken`, and `Cookie` values | Not tested in this change |

Caution: The SDK writes write bodies to the debug log (SB-18 and SB-19). A secret-bearing field can reach a debug log. Decision D-13 keeps secret-bearing families disabled until redaction evidence exists. The SDK redacts headers only (SB-20), not bodies.

## Signature Contract

Each write wrapper takes `mist_session` as the first argument. Each wrapper takes explicit path arguments and a body argument. The source annotates the body argument with a dictionary or a list for the create and assign functions. The other body arguments accept a dictionary only. Each wrapper has no variadic argument (test 8).

| ID | Function | Arguments after the session |
| --- | --- | --- |
| W-01 | `createOrgSite` | `org_id: str`, `body` (dictionary or list) |
| W-02 | `updateSiteInfo` | `site_id: str`, `body` (dictionary) |
| W-03 | `updateOrgInventoryAssignment` | `org_id: str`, `body` (dictionary) |
| W-04 | `updateSiteDevice` | `site_id: str`, `device_id: str`, `body` (dictionary) |
| W-05 | `createOrgGatewayTemplate` | `org_id: str`, `body` (dictionary or list) |
| W-06 | `updateOrgGatewayTemplate` | `org_id: str`, `gatewaytemplate_id: str`, `body` (dictionary) |
| W-07 | `deleteOrgGatewayTemplate` | `org_id: str`, `gatewaytemplate_id: str` |
| W-08 | `createOrgDeviceProfile` | `org_id: str`, `body` (dictionary or list) |
| W-09 | `updateOrgDeviceProfile` | `org_id: str`, `deviceprofile_id: str`, `body` (dictionary) |
| W-10 | `deleteOrgDeviceProfile` | `org_id: str`, `deviceprofile_id: str` |
| W-11 | `assignOrgDeviceProfile` | `org_id: str`, `deviceprofile_id: str`, `body` (dictionary or list) |
| W-12 | `unassignOrgDeviceProfile` | `org_id: str`, `deviceprofile_id: str`, `body` (dictionary or list) |
| W-13 | `updateSiteSettings` | `site_id: str`, `body` (dictionary) |
| W-14 | `createOrgNetwork` | `org_id: str`, `body` (dictionary or list) |
| W-15 | `updateOrgNetwork` | `org_id: str`, `network_id: str`, `body` (dictionary) |
| W-16 | `deleteOrgNetwork` | `org_id: str`, `network_id: str` |
| W-17 | `createOrgService` | `org_id: str`, `body` (dictionary or list) |
| W-18 | `updateOrgService` | `org_id: str`, `service_id: str`, `body` (dictionary) |
| W-19 | `deleteOrgService` | `org_id: str`, `service_id: str` |
| W-20 | `createOrgServicePolicy` | `org_id: str`, `body` (dictionary or list) |
| W-21 | `updateOrgServicePolicy` | `org_id: str`, `servicepolicy_id: str`, `body` (dictionary) |
| W-22 | `deleteOrgServicePolicy` | `org_id: str`, `servicepolicy_id: str` (excluded, no caller) |

Each DELETE wrapper passes a query argument to `mist_delete`. For example, `orgs/networks.py` line 140 builds an empty dictionary and line 141 passes it. The URI and the verb match the OpenAPI path and verb for each row (test 12).

## Forwarding Contract

Each write wrapper passes the body object it received, without a copy or a change, to the session call. Test 10 checks that the object identity is the same. Test 11 checks that the wrapper makes one session call.

## Test Mechanics

- Build a real mistapi session object with a synthetic token constant. The tests set no credential variable.
- Replace the `requests` object of the session with a test double. The double returns response objects with the status code under test.
- Patch `time.sleep` in the tests for HTTP 429. The sleep calls record the waits (SB-02 and SB-03).
- Block socket connections in the conftest for each test (test 17).
- Verify the constructor arguments of the session object before writing the double (task T009).
