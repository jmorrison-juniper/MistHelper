# Submission Certainty Contract

**Feature**: [spec.md](../../spec.md)

## Input evidence

The shared rule consumes the raw HTTP status and existing submission fields. It does not make another request.

## Classification

| Response evidence | Required child status |
|---|---|
| Accepted response and required upgrade identity | `accepted` |
| HTTP 400, 401, 403, or 404 with no conflicting evidence | `rejected` |
| Documented refusal status with a job identity or accepted target | `submission_unknown` |
| Documented refusal status with a malformed or unretained response body | `submission_unknown` |
| Local proof that no cloud request was sent | `not_submitted` |
| Transport exception, HTTP 408, 429, 499, any 5xx, or undocumented status | `submission_unknown` |
| Malformed response body or missing required upgrade identity | `submission_unknown` |

## Consumer behavior

- Lock release checks the child status with the shared settlement helper.
- Retry eligibility uses the same settlement decision and stays blocked for uncertain children.
- Cancellation reporting calls the same refusal predicate before claiming that no cloud job exists.
- A prior `rejected` record remains uncertain when its status is undocumented or its saved response names a job or accepted target.
- A discarded or malformed response body cannot prove a refusal.
- An empty decoded object without raw JSON cannot prove refusal. The SDK can retain that default after JSON parsing fails.
- A retained `{}` JSON body remains valid. An empty cancellation response keeps its separate existing behavior.
- Device and organization normalizers use the same body check before a refusal can settle.
- Each new child stores `response_data_valid`. Only exact `true` proves that its response body passed the normalizer check.
- A legacy rejected child without this proof remains uncertain after reload, even with a documented refusal status.
- A decoded success identity that disagrees with the raw body cannot become a tracking or cancellation identity.
- A prior `rejected` record with a job identity must not skip cancellation as an already-ended child.
- Summary counts do not count an uncertain rejected child as fully failed.
- No path retries a destructive submission because the response is uncertain.
- Organization target lists require exact `status_data_valid=true` before they affect public counts or device states.
- Invalid new responses store empty progress data. Legacy bodies without progress proof remain unverified.
- A valid subsequent status read establishes its own progress proof without changing submission proof.
- Preserve verified reconciliation counts, nested target precedence, public fields, and all settlement decisions.

## Status evidence

The local OpenAPI lists HTTP 400, 401, 403, 404, and 429 for the upgrade endpoints. Only 400, 401, 403, and 404 can prove refusal. HTTP 429 remains uncertain. Do not treat other statuses as refusal without supporting evidence.

## Test contract

Tests replace all network and lock boundaries with local stand-ins. They prove accepted responses, documented refusals, conflicting identities and targets, malformed and unretained response bodies, uncertain response classes, legacy records, lock release, and retry blocking. The test suite makes zero live Mist API calls and no production lock changes.
