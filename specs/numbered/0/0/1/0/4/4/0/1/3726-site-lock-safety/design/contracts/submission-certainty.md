# Submission Certainty Contract

**Feature**: [spec.md](../../spec.md)

## Input evidence

The shared rule consumes the raw HTTP status and existing submission fields. It does not make another request.

## Classification

| Response evidence | Required child status |
|---|---|
| Accepted response and required upgrade identity | `accepted` |
| HTTP 400, 401, 403, 404, 405, 409, 410, 413, 415, or 422 | `rejected` |
| Local proof that no cloud request was sent | `not_submitted` |
| Transport exception, HTTP 408, 429, 499, any 5xx, or unlisted status | `submission_unknown` |
| Malformed HTTP 200 or missing required upgrade identity | `submission_unknown` |

## Consumer behavior

- Lock release checks the child status with the shared settlement helper.
- Retry eligibility uses the same settlement decision and stays blocked for uncertain children.
- Cancellation reporting calls the same refusal predicate before claiming that no cloud job exists.
- A prior `rejected` record without allowlisted status evidence remains uncertain.
- No path retries a destructive submission because the response is uncertain.

## Test contract

Tests replace all network and lock boundaries with local stand-ins. They prove accepted responses, each refusal class, uncertain response classes, missing evidence, legacy records, lock release, and retry blocking. The test suite makes zero live Mist API calls and no production lock changes.
