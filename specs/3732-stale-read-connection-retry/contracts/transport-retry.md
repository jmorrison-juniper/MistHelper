# Contract: Shared Mist transport retry

## Purpose

The shared Mist session can recover a stale safe read.
It cannot repeat a write.

## Request method contract

| Method | Transport retry permitted |
| - | - |
| GET | Yes, within the category and total limits |
| HEAD | Yes, within the category and total limits |
| POST | No |
| PUT | No |
| PATCH | No |
| DELETE | No |
| Any other method | No |

## Failure category contract

| Failure | GET or HEAD | Other method |
| - | - | - |
| Stale pooled read reset | One retry | No retry |
| Connection establishment failure | Two retries, with three total attempts | No retry |
| HTTP response status | No retry | No retry |
| Redirect retry | No retry | No retry |
| Unclassified transport failure | No retry | No retry |

## Requests integration contract

- Mount one configured adapter on `https://`.
- Mount the same adapter policy on `http://` for local diagnostics and tests.
- Preserve a caller-supplied timeout.
- Add the default timeout only when the caller supplies no timeout.
- Keep mistapi authentication on the existing session.
- Do not add a direct Mist REST request.

## Upgrade write-session contract

- Keep `OrgUpgradeSession._MAX_429_RETRIES` equal to zero.
- Keep each upgrade transport adapter retry total equal to zero.
- Reject the shared read adapter at the upgrade write boundary.
- Do not change the upgrade portal source in this feature.

## Test evidence

- A local reset followed by a GET success uses exactly two attempts.
- A local reset followed by a HEAD success uses exactly two attempts.
- A local POST reset uses exactly one attempt.
- Each other tested write method uses exactly one attempt.
- A local HTTP 500 answer uses exactly one attempt.
- An exhausted stale read stops after its second attempt.
- An eligible connection failure never exceeds three total attempts.
- The upgrade write-session validator accepts only a zero-retry adapter.
