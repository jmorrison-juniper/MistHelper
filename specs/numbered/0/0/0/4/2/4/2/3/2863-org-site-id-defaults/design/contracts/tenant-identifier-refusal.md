# Contract: Tenant identifier refusal

## Scope

The public methods and private helpers in `src/mist/access/api/tenant_fetch.py` after batch 1. The contract covers the inputs, the SDK calls, the refusal output, the call order, and the unchanged results.

## Inputs and SDK Calls

| Method | Identifier inputs | Required | SDK calls on valid input |
|--------|-------------------|----------|--------------------------|
| `organization_tenants()` | Organization identifier from the injected resolver | Yes | `listOrgNetworks(session, org_id, limit=1000)` |
| `site_tenants(site_id)` | Site identifier | Yes | `listSiteNetworksDerived(session, site_id)` |
| `service_policy_tenants(site_id=None)` | Organization identifier. Optional site identifier. | Organization: yes. Site: optional. | `listOrgServicePolicies(session, org_id, limit=1000)`. Also `listSiteServicePoliciesDerived(session, site_id)` when a site is supplied. |
| `gateway_template_tenants(site_id=None)` | Organization identifier. Optional site identifier. | Organization: yes. Site: optional. | `listOrgGatewayTemplates(session, org_id, limit=1000)`. Also `listSiteGatewayTemplatesDerived(session, site_id)` when a site is supplied. |

The value `1000` is the existing `_API_PAGE_LIMIT` (`tenant_fetch.py:29`). The SDK function names match RC-41 to RC-46 in `research.md`.

## Refusal Rule

- A required identifier is refused when it is not a `str`, or when `value.strip()` is empty. `None` is refused.
- An optional site identifier is refused when it is not `None`, and it fails the same rule.
- Only `None` selects organization-only scope.

## Refusal Output

- Exception: `ValueError`.
- Message: exactly `org_id must be a non-empty string.` or exactly `site_id must be a non-empty string.`
- Log: one `logging.error` call. The format is `Refused tenant discovery because %s is missing or invalid.` The only argument is the field name.
- The input value never appears in the message, in the log record, or in any other output.

Warning: a message that includes the input value can expose private text. Use the field name only.

## Call Order

1. Call the organization resolver once. The resolver call is lazy.
2. Refuse an invalid optional site identifier before any SDK call.
3. Refuse an invalid organization identifier before any SDK call.
4. Call the organization SDK function.
5. Call the site SDK function only when a site identifier is supplied.

A refusal at step 2 or step 3 causes zero SDK calls. The public union methods run the refusal checks before the first SDK call.

## Unchanged Results

- An HTTP status of 400 or higher returns the empty result for that source (`_HTTP_ERROR_MIN`).
- A parse failure returns the empty result and reports the failure through `ResponseIntegrityChecker`.
- `AttributeError` and `requests.RequestException` return the empty result.
- An unexpected exception from the resolver propagates unchanged.
- Results are sorted and unique. Per-record names keep the existing collection rule.

## Discovery Output

`ServicePingManager.execute` catches `Exception` and prints `Error during Service Ping operation: <message>` (`service_ping_manager.py:467-468`). A refusal reaches that line. The printed text names the field. The manager does not print a "No tenants found" line for a refusal.
