# Data Model: Submission Certainty

**Feature**: [spec.md](../spec.md)

## Aggregate operation

An aggregate operation holds the selected child submissions, durable outcome evidence, and the site locks that protect those submissions.

| Field | Meaning | Validation |
|---|---|---|
| `children` | Child firmware requests in the operation | Each child status follows the outcome rules below. |
| `site_locks` | Locks held for sites in the operation | Keep each lock while a child can still write or its outcome is uncertain. |
| `phase_watch` | Optional post-upgrade observation stage | Keep site locks while the watch needs the site. |
| `state` | Aggregate operation state | An aggregate final state cannot override an uncertain child. |

## Child submission

| Field | Meaning | Validation |
|---|---|---|
| `status` | Accepted, rejected, not submitted, running, final, or uncertain state | `rejected` proves no cloud job only when `raw_status` is an allowlisted refusal. |
| `raw_status` | HTTP response status, when available | Only an integer in the explicit allowlist proves refusal. Other values remain uncertain. |
| `upgrade_id` | Cloud identity used to read or cancel an accepted job | An accepted-looking response without the required identity is uncertain. |
| `error` | Safe operator-facing reason | Do not include credentials or secret response content. |

## Outcome transitions

| Evidence | Child status | Can settle? | Can release a site? |
|---|---|---:|---:|
| Accepted response with a required identity | `accepted` | No | No |
| Explicit allowlisted refusal | `rejected` | Yes | Only after other children and any watch settle |
| Proven local stop before a cloud write | `not_submitted` | Yes | Only after other children and any watch settle |
| Transport error or timeout | `submission_unknown` | No | No |
| 408, 429, 499, 5xx, or unlisted response | `submission_unknown` | No | No |
| Malformed success or missing required identity | `submission_unknown` | No | No |
| Rejected legacy record with missing or unlisted status | `rejected`, treated as uncertain | No | No |

## Lock-release invariant

The portal releases site locks only when every child is final and every rejected child carries allowlisted refusal evidence. It also waits for any required phase watch. An uncertain recorded outcome cannot prove that the cloud job ended.
