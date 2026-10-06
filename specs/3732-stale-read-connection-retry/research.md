# Research: Safe read transport retry

## R1. Requests and urllib3 retry ownership

**Decision**: Configure the retry policy on the existing Requests `HTTPAdapter`.

**Rationale**: Requests passes `adapter.max_retries` to urllib3 for each transport call.
The existing session configurator already mounts one adapter for HTTP and HTTPS.
The change can preserve the timeout seam and the authenticated mistapi session.

**Alternatives considered**:

- Add a retry loop around each mistapi call.
  This duplicates policy and can repeat a write at a call site.
- Add direct HTTP calls.
  This would bypass mistapi authentication and endpoint contracts.
- Change mistapi.
  This repository does not own the installed SDK.

## R2. Method safety for connection errors

**Decision**: Add a method guard before urllib3 classifies every retry.

**Rationale**: urllib3 applies `allowed_methods` to read errors and status retries.
Its connection-error branch does not test the method.
A plain `Retry(connect=2, allowed_methods={"GET", "HEAD"})` can therefore repeat a POST connection attempt.
The explicit guard prevents that unsafe result.

**Alternatives considered**:

- Use `allowed_methods` without a guard.
  This does not protect a POST from a connection retry.
- Set `connect=0`.
  This protects writes but removes bounded connection recovery for safe reads.
- Mount adapters by HTTP method.
  Requests selects adapters by URL prefix, not by request method.

## R3. Retry counts

**Decision**: Use `total=2`, `connect=2`, `read=1`, `status=0`, and `other=0`.

**Rationale**: A stale pooled reset is a read failure after request transmission.
One read retry gives exactly two attempts for that failure.
Two connection retries permit at most three attempts for an eligible safe read.
The total counter prevents any category combination from exceeding three attempts.

**Alternatives considered**:

- Use unlimited totals with category limits.
  A category interaction could exceed the required total bound.
- Use two read retries.
  The observed stale connection needs one retry, and an extra repeat adds delay.
- Use one total retry.
  This removes the specified three-attempt connection ceiling.

## R4. HTTP status handling

**Decision**: Do not retry an HTTP response status at the transport layer.

**Rationale**: A status is an application result.
The portal must classify that result instead of hiding it through a transport retry.
An empty `status_forcelist`, `status=0`, and disabled retry-header handling preserve this rule.

**Alternatives considered**:

- Retry HTTP 429 or 5xx responses.
  This changes application behavior and can hide a refusal.
- Honor `Retry-After`.
  This can enable a response-driven retry outside the feature requirement.

## R5. Pick-list success boundary

**Decision**: Accept only a usable HTTP 2xx status as a successful picker response.

**Rationale**: `None` means that the SDK received no HTTP answer.
HTTP 4xx and 5xx responses are failures.
A final 3xx answer is not the requested picker result.
An empty 2xx response is valid and must keep the no-rows meaning.

**Alternatives considered**:

- Read `response.data` before the status.
  The SDK can provide an empty object after a transport failure.
- Treat every empty data object as no rows.
  This reproduces the reported defect.
- Raise for each invalid status.
  The route contract already returns a `PickList` with an operator reason.

## R6. Response validation owner

**Decision**: Put the shared response-status rule on the existing `PickList` class.

**Rationale**: The class already owns picker success and failure meaning.
This choice avoids a new standalone wrapper and a new top-level module child.
Each fetch function can validate before it extracts data.

**Alternatives considered**:

- Add one standalone validation function.
  Repository rules require behavior in a named class.
- Add a new module.
  The user bounded production changes to two existing files.
- Add a new result type.
  `PickList` already preserves list compatibility for all callers.

## R7. Client source aggregation

**Decision**: Keep valid rows when one client source succeeds.

**Rationale**: The existing merger can return useful rows from one source.
The failed source still writes an error log.
If both sources fail, the merger must return the fixed reachability reason.
If both sources return valid empty 2xx responses, the merger must return a valid empty result.

**Alternatives considered**:

- Fail the whole picker when one source fails.
  This discards valid rows from the other source.
- Always return an empty success after one failure.
  This hides a failure when the other source has no rows.

## R8. Upgrade write-session isolation

**Decision**: Leave the upgrade portal write session unchanged.

**Rationale**: `OrgUpgradeService.check_write_session` requires zero SDK retries and zero adapter retries.
The shared read policy has a nonzero total and must fail that write-session check.
This is the required safety boundary.

**Alternatives considered**:

- Share the read adapter with the upgrade session.
  The write-session validator would reject it, and a bypass could repeat an upgrade.
- Relax the validator for allowed methods.
  The validator protects the write boundary and must remain strict.

## R9. Test transport

**Decision**: Use a local HTTP server for attempt counts and fake SDK responses for picker status tests.

**Rationale**: A local server exercises Requests and urllib3 together.
Fake SDK responses exercise portal classification without credentials.
Both methods make zero live Mist API calls.

**Alternatives considered**:

- Use a production Mist credential.
  This is unsafe and non-deterministic.
- Mock only `Retry.increment`.
  This does not prove Requests mounts and uses the policy.
- Use only a socket fake for every test.
  Picker classification does not need a transport.
