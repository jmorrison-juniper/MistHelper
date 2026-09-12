---
name: managing-mist-api
description: >-
  Use when you explain, discover, query, automate, implement, test, or troubleshoot
  the Juniper Mist API or the mistapi Python SDK. Use for authentication, API
  tokens, MSPs, organizations, sites, inventory, APs, switches, SSR/SRX gateways,
  Mist Edge, WLANs, templates, NAC, clients, SLEs, alarms, firmware upgrades,
  packet captures, WebSocket commands, webhooks, location, and API integrations.
  Use the local documentation as the authority for endpoints and schemas.
  Cover pagination, rate limits, permissions, safe changes, SDK-only entries,
  source conflicts, exports, and offline validation before a live request.
argument-hint: Describe the Mist operation, scope, and whether you need an explanation, code, or an authorized live request.
---

# Manage the Mist API

Use this skill to produce source-grounded Mist API answers and automation.
The skill covers the complete local API catalog, not only MistHelper menu operations.
It does not grant permission to access or change a network.

## 1. Load the correct reference

Read only the references that the task needs. Each guide contains a contents list.
The source documents stay in `documentation/`. This skill does not replace or copy their complete schemas.

| Task | Reference | Required result |
| - | - | - |
| Establish sources, cloud, credentials, scope, and schema rules. | [Source authority](./references/source-authority.md) | A verified operation contract. |
| Find an operation in any API category or source edition. | [Endpoint catalog](./references/endpoint-catalog.md) | The exact method, path, and source page. |
| Send requests, paginate, handle errors, or collect asynchronous results. | [Request lifecycle](./references/request-lifecycle.md) | Complete results or an explicit incomplete result. |
| Select a workflow for a network or account operation. | [Domain workflows](./references/domain-workflows.md) | A bounded procedure with verification. |
| Implement an integration, test the skill, or refresh its sources. | [Verification](./references/verification.md) | Evidence that the contract and safety checks hold. |

### Source entry points

- [The primary OpenAPI 3.1 JSON](../../../documentation/mist-api-openapi31json.json) defines 1,013 operations in the verified snapshot.
- [The endpoint index](../../../documentation/api/INDEX.md) links those operations and 61 SDK-only stubs.
- [The saved overview](../../../documentation/Overview%20_%20API%20_%20Mist.html) explains shared request behavior.
- [The saved authentication guide](../../../documentation/Auth%20_%20API%20_%20Mist.html) explains identity and privileges.
- [The catalog](./references/endpoint-catalog.md) also routes the organization, site, MSP, older-specification, and location references.

The verified snapshot date is 2026-09-09. These counts describe local documents, not the current cloud service.
Read the source-authority guide when dates, methods, paths, fields, or examples disagree.

## 2. Establish the task and authority

1. Determine whether the user requests documentation, code, an offline test, or a live operation.
2. Identify the requested outcome and the smallest required API scope.
3. Confirm the regional cloud host before you attach credentials.
4. Resolve the organization, site, device, and related resource identifiers from authorized evidence.
5. Classify the operation by its actual effects, not its HTTP method alone.

For documentation or code tasks, do not call the live Mist API to establish context.
Use synthetic identifiers in examples. Example identifiers in the documentation do not identify the user's resources.

For live tasks, establish the permitted target set, time range, output location, and request budget.
If an ambiguous name matches multiple resources, ask the user to select the target.
Do not select the first result or broaden the search to another tenant without permission.

### Risk classes

These classes are skill safety policy. They are not Mist API response fields.

| Class | Examples | Required control |
| - | - | - |
| Read-only | Read inventory, statistics, or bounded event history. | Confirm scope and data handling. |
| Active diagnostic | Send ping traffic, run a synthetic test, or collect a capture. | Confirm the target, load, duration, and cleanup. |
| Configuration change | Change a WLAN, template, assignment, webhook, or alarm state. | Show the planned difference and obtain approval. |
| Disruptive or irreversible | Reboot, upgrade, zeroize, delete, revoke, disconnect, or change a cluster. | Obtain explicit typed confirmation and define recovery. |

Warning: a destructive request can delete configuration or interrupt service. Do not send it without explicit user confirmation.

`GET /api/v1/installer/sites/{site_name}/optimize` starts radio optimization.
Treat this GET as an active change, not as a safe inventory request.
Read the [installer operation](../../../documentation/api/installer/GET_installer_sites_site_name_optimize.md) before use.

An API token with write permission does not constitute approval for a change.
An instruction to create this skill does not authorize any live Mist operation.

## 3. Build the operation contract

1. Find the operation in the endpoint catalog or the local index.
2. Read its exact method and path in the primary specification.
3. Resolve the referenced parameters, request body, responses, and security requirements.
4. Read the matching saved HTML section for narrative behavior and conditions.
5. Record any conflict or missing requirement before you choose an execution path.

Capture these contract fields before implementation or execution:

| Field | Required evidence |
| - | - |
| Source | The file, source edition, and heading or JSON Pointer. |
| Operation | The exact `operationId`, HTTP method, and path template. |
| Target | The cloud host and each verified scope identifier. |
| Authorization | The authentication method, privileges, and approved target set. |
| Request | The path fields, query fields, headers, media type, and body constraints. |
| Result | The success status, response shape, pagination, and asynchronous identifier. |
| Safety | The effects, confirmation, retry policy, cleanup, and completion test. |

Do not infer a route from an SDK name. A category label can differ from the path scope.
For example, an operation with an organization label can still require `site_id` in its path.

Do not copy an example as a valid request without validation.
Some saved examples contain comments, missing commas, placeholders, or field combinations that require additional conditions.
An empty schema does not prove that arbitrary input is safe.

### Non-negotiable request rules

- Use `Authorization: Token <key>` for API-token authentication, not `Bearer`.
- Keep secrets outside code, chat, logs, screenshots, and version control.
- Do not treat a CSRF header as an alternative API token.
- Use the documented device type filter when a listing must include switches or gateways.
- Keep the exact distinction between `device_id`, `device_mac`, `client_mac`, and `site_name`.
- Preserve `false`, `0`, `null`, empty values, and absent values as distinct cases.
- Preserve documented arrays and their order. Do not assume a PATCH-style merge for PUT.
- Validate response media type and shape before you process data.
- Do not treat a successful HTTP status as proof that every item succeeded.
- Do not retry an uncertain write until you reconcile the remote state.

## 4. Execute the bounded workflow

### Read-only work

1. Use the smallest documented query that satisfies the task.
2. Fix the time window when you read historical data across pages.
3. Retrieve every required page through the documented pagination mechanism.
4. Preserve the scope and source metadata when you combine results.
5. Report completeness, empty results, skipped scopes, and failed scopes separately.

An empty list is not automatically a failure. A failed request is not an empty list.
If the API returns only access points by default, an empty switch result does not prove that no switches exist.

### Configuration and disruptive work

1. Read the present state and the dependent resources.
2. Prepare a protected recovery record and a redacted difference.
3. Obtain approval for the exact target set and intended effects.
4. Submit the smallest approved change once.
5. Verify the resulting configuration and operational state through documented reads.

For disruptive work, require the user to type the stated confirmation text.
If the target set or payload changes after confirmation, obtain confirmation again.
Do not assume that cancellation restores devices that already changed.

### Asynchronous work

Use the request-lifecycle guide for commands, captures, tests, upgrades, and imports.
Record the returned job, session, or capture identifier. Correlate every result with that identifier and its scope.
Keep `accepted`, `completed`, `failed`, `cancelled`, and `unknown` distinct in the report.
These are report classifications unless the endpoint defines the same status strings.

Unsubscribe from a stream when collection ends. Stop a capture only when this task owns it and approval permits the stop.
Do not stop another operator's work to make a new operation succeed.

## 5. Implement, verify, and report

For Python integration, verify the installed `mistapi` signature before you write the call.
The OpenAPI `operationId` is a discovery key, not a promise about an installed SDK module.
Use the repository's existing session, pagination, input, exporter, and firmware facilities when they fit the contract.
The verification guide explains how to find those facilities without relying on old menu numbers.

For an available Mist MCP tool, read its current input schema before use.
Confirm that the tool preserves the required scope, filters, and pagination.
Do not invent a write tool or claim that a filtered preview is a complete export.

Run offline contract and safety tests before a live test. Do not make a production request to test an uncertain route.

Return a concise result with:

1. The requested outcome and the exact scope.
2. The source file and operation that support the answer.
3. The actions actually performed, including whether any live request occurred.
4. The completion evidence, item counts, and unresolved limitations.
5. The artifact location or the next safe action, when required.

Do not claim success from a plan, a printed command, an unexecuted example, or an accepted asynchronous request.
If a source conflict blocks safe execution, report the conflict and stop that operation.
