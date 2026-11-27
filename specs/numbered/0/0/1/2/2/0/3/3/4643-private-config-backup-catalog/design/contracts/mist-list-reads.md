# Contract: Mist List Reads for Backup Capture

## Scope

This contract covers three read-only list operations. The capture uses them to read the complete object set for one organization and one object family. The contract names no write operation. It forbids each write call in this change (FR-022).

The evidence comes from two sources: the OpenAPI file on `main` (`documentation/mist-api-openapi31yaml.yaml`) and the installed pinned package `mistapi==0.64.1`. Research rows R-45 to R-59 and R-75 record the checks.

## Operations

| Family | SDK function | SDK module | HTTP operation | OpenAPI lines | Arguments after the session | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `service-policy` | `listOrgServicePolicies` | `mistapi.api.v1.orgs.servicepolicies` | GET `/api/v1/orgs/{org_id}/servicepolicies` | 18340 (path), 18345 (operation ID), 18351 (response) | `org_id`, `limit`, `page` | R-46, R-58, R-77 |
| `service` | `listOrgServices` | `mistapi.api.v1.orgs.services` | GET `/api/v1/orgs/{org_id}/services` | 18489 (path), 18494 (operation ID), 18500 (response) | `org_id`, `limit`, `page` | R-47, R-57, R-78 |
| `network` | `listOrgNetworks` | `mistapi.api.v1.orgs.networks` | GET `/api/v1/orgs/{org_id}/networks` | 15118 (path), 15128 (response) | `org_id`, `limit`, `page` | R-45, R-56, R-79 |

Each SDK function takes the session first, typed as `mistapi.APISession`. It then takes `org_id` as a string. It takes `limit` and `page` as optional integers (R-56 to R-58, lines 17, 20, and 21). For the networks function, the body adds each query value only when the value is set (R-56).

The GET operation for each family returns an array response. The response names are `NetworksArray`, `ServicePoliciesArray`, and `ServicesArray` (R-77, R-78, R-79).


## Parameters

| Parameter | OpenAPI rule | Capture rule |
| --- | --- | --- |
| `limit` | Integer. Default 100. Minimum 0. No maximum (R-48). | Send `1000` on every call. |
| `page` | Integer. Default 1. Minimum 1 (R-49). | Send `1` for the first page, then `2` and so on until the reported total is reached. |

The value 1000 matches the repository page limit (R-28). The repository clamps the environment setting to the range 1 to 1000 at startup (R-76), so the capture uses the same bound.

## Response Headers

The OpenAPI file documents no pagination header (R-50). The installed SDK reads three headers when it builds the next link: `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` (R-59, line 76).

The capture uses only `X-Page-Total`:

- A missing header refuses the capture (FR-008).
- A value that does not parse as a non-negative integer refuses the capture (FR-008).
- A value that changes between pages refuses the capture (FR-008).
- Presence and meaning remain unverified until issue 4634 records live evidence (U-01).

## Response Body

- Each page must hold a JSON array of objects. A non-array body refuses the page (FR-009).
- Each object must hold an `id` string. The `id` property appears in the network schema (R-51), the service schema (R-55), and the service policy schema (R-75).
- A repeated `id` across pages refuses the capture (FR-008).
- The complete object body is stored in the file. Live evidence that each list item holds the complete body remains open (U-02).

## Request Admission and Status

Each page read follows this sequence:

1. `PolicyAdmission.request` admits the call through shared pacing and quota (R-19).
2. `PolicyResponse.request` checks the HTTP status (R-20). A status outside 200 to 299 refuses the page.
3. `PolicyResponse.rows` checks that the body is a list of objects (R-21).
4. The converter checks the `id` values, the reported total, and the count.

An SDK exception refuses the page. The converter maps each refusal to `StateRefused`. The message names the action and the status code. The message never contains a response body.

Caution: the capture never retries a refused page automatically. A retry can read a changed set of objects, so the operator starts a new capture after the cause is removed.

## Call Pattern

The capture makes this sequence of calls for one family:

1. Call page 1 with `limit=1000` and `page=1`. Read `X-Page-Total`.
2. If the reported total is zero, stop. The capture holds zero objects.
3. Otherwise, call pages 2 to ceil(total / 1000). Check the total on each page.
4. Stop after the page that makes the captured count equal the reported total.

A page after the last page that the total requires is not requested. A short page before the total refuses the capture.

## Forbidden Patterns

- A call that forwards `*args` or `**kwargs` into an SDK function. The SDK compatibility guard checks this rule (R-42).
- A `get` call for one object. Decision D-6 excludes it.
- The `PolicyResponse.collect` helper. Decision D-3 excludes it (R-22).
- Any write function from the mistapi package in this change (FR-022).
- A direct HTTP request to a Mist endpoint. The constitution forbids it when a working mistapi method exists.

## Test Mapping

| Test | Contract rule |
| --- | --- |
| `test_capture_reads_every_page_with_explicit_page_numbers` | Page sequence and the boundary totals 0, 1, 1000, and 1001. |
| `test_capture_refuses_absent_or_invalid_reported_total` | Header rules. |
| `test_capture_refuses_empty_page_before_reported_total` | Short page rule. |
| `test_capture_refuses_repeated_object_identifier` | Repeated `id` rule. |
| `test_capture_refuses_total_change_between_pages` | Total consistency rule. |
| `test_capture_refuses_failed_or_malformed_page` | Status and body rules, for 401, 403, 429, 500, and a malformed body. |
| `test_capture_refuses_family_outside_scope` | Family scope (D-5). |
| `test_capture_calls_only_list_functions_with_explicit_arguments` | Operation and argument rules. |
| `test_capture_opens_no_network_socket` | No live call. |
| `test_capture_refuses_ambiguous_or_missing_relationship_target` | Relationship rule (D-7). |
