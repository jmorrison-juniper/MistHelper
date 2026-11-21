# Data Model: Site Lock Safety for Uncertain Upgrade Replies

## Submission Outcome

One stored child result for an organization, site, or SSR upgrade.

| Field | Meaning | Validation |
|---|---|---|
| `status` | The state of the child submission or job. | An uncertain returned result uses `submission_unknown`. |
| `raw_status` | The HTTP status from the existing SDK call. | Only an exact integer in 400, 401, 403, or 404 can prove refusal. |
| `upgrade_id` | The cloud identifier of the accepted child job. | Acceptance and proven refusal both require a consistent identifier state. |
| `error` | The response error or uncertainty message. | Keep the existing message. Do not include secrets. |

### State Rules

- `accepted`: The existing success rule passes and the reply includes an upgrade identifier.
- `rejected`: The reply has no upgrade identifier and its HTTP status is 400, 401, 403, or 404.
- `submission_unknown`: The response does not prove acceptance or refusal.
- `not_submitted`: The service proves that no request was sent for this child.
- `completed`, `cancelled`, and `failed`: Existing final job states remain unchanged.

## Site Lock

An operation-owned lock prevents a second firmware operation at a selected site.

- Keep all operation locks while any child outcome is unknown.
- Release locks only when every child is final or has proven refusal evidence.
- Keep the existing phase-watch release condition for accepted jobs.
- Do not change the lease, lock token, compare-and-set behavior, or recovery route.

## Cancellation Result

A cancellation result holds the device lists for one child job.

- Use the stored complete cancellation lists when they exist.
- If no complete result exists, list devices as possibly writing unless the child was not submitted or has proven refusal evidence.
- Apply the same refusal status and identifier check used by lock release.

## Legacy Records

Do not migrate stored records. A legacy `rejected` child releases locks only when its saved HTTP status is 400, 401, 403, or 404 and it has no upgrade identifier. Other legacy rejected records remain uncertain.
