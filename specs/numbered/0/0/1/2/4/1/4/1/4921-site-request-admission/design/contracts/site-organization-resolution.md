# Contract: Site Organization Resolution

This contract defines the input, output, and order of the site organization rule in `RequestLedger`. The rule runs inside `AdmittedAdapter.send` and `RequestLedger.admit`.

## Inputs

### Organization listing response

- **Request**: `GET /api/v1/orgs/{org_id}/sites`. The path has exactly six segments: an empty segment, `api`, `v1`, `orgs`, the organization identifier, and `sites`.
- **Status**: HTTP 200. Any other status gives no mapping.
- **Body**: A JSON list. Each item is a site record. The record holds a string field `id`.
- **Source**: `operationId: listOrgSites` (`documentation\mist-api-openapi31yaml.yaml` line 20022). The response schema is `sites` (line 102622).

### Site request

- **Request**: Any method. The path is `/api/v1/sites/{site_id}` or a sub-path of it.
- **Site identifier**: The path segment at index 4. The rule uses no other request field.

## Output

The rule returns one organization identifier, or it raises `ConnectionError`.

- **Success**: The organization identifier string.
- **Refusal**: `ConnectionError` with the text `Site API request admission requires a selected organization.`

## Resolution Order for a Site Request

1. **Site organization map**: Return the organization that a successful listing stored for the site.
2. **Ledger organization**: Return the value that the ledger received at construction, when the value is set.
3. **Session organization**: Call the session organization callable. Return its value, when the value is set.
4. **Refusal**: Raise the refusal.

## Learning Rules

1. The learning step runs for each admitted response. It runs after the HTTP 429 check.
2. The step writes nothing unless each condition holds: the method is GET, the path matches the listing shape, the status is 200, and the body is a JSON list.
3. Each item with a string `id` writes one entry. The entry value is the path organization.
4. The step never raises. A body that is not valid JSON gives a debug record and no entry.
5. The step writes counts only to the log. It never writes a site identifier or an organization identifier at info level.

## Bounds and Concurrency

- The map holds at most 50,000 entries. The oldest entry leaves first.
- The map uses one lock for each read and each write.
- Each lock hold covers one lookup or one page of entries.

## Non-Requirements

- The rule adds no Mist request.
- The rule does not change organization requests under `/api/v1/orgs/{org_id}`. Their attribution is the path organization.
- The rule does not change requests without an organization or site segment, such as `/api/v1/self`. Their attribution is the ledger organization, as before.
- The rule does not read the `org_id` field of each site record. The path organization is the value.
