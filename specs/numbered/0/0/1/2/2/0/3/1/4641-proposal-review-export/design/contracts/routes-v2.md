# Contract: Version 2 Routes

The version 2 routes live in the converter blueprint. They use the converter prefix, so the request bound and the no-store header of version 1 apply to them. The shared portal registration stays out of scope (issue #4648).

## Routes

| Method | Path | Request | Success | Failure | Session effect |
| - | - | - | - | - | - |
| POST | `/cisco-config-converter/v2/preview` | Multipart form with `file`, `name`, `type`, and the CSRF token | HTTP 200 with the structured proposal | HTTP 400 with `error` for invalid input or a CSRF failure. HTTP 413 for a body above the limit. | Clears the two review keys and the two time keys first. Publishes the proposal digest and the UTC preview time on success. |
| POST | `/cisco-config-converter/v2/review` | JSON body with the structured proposal and the `X-CSRFToken` header | HTTP 200 with the same object | HTTP 400 for a non-object body, a wrong version, or a wrong key set. HTTP 409 for a digest that differs from the session, or for a preview recorded 15 minutes or more earlier. | Sets the reviewed digest and the UTC review time on success. |
| POST | `/cisco-config-converter/v2/export` | Same as review | HTTP 200 with the same object as an attachment | HTTP 400 for an invalid body. HTTP 409 when the proposal is not reviewed, differs from the session, or the review was recorded 15 minutes or more earlier. | No change |

The CSRF token may travel in the form field `csrf_token` or in the header `X-CSRFToken`. A missing token returns HTTP 400 with no traceback (test 15).

## Headers

- Each success response holds `Cache-Control: no-store`. The blueprint applies this header to every converter route.
- The export response sets the `Content-Disposition` header to an attachment named `cisco-proposal-v2.json`.

## Preview Order

1. Remove the keys `cisco_proposal`, `cisco_reviewed`, `cisco_proposal_at`, and `cisco_reviewed_at` from the session.
2. Validate the source with `ConverterInput.source`.
3. Read the suffix from the base name of the uploaded file. The base name was already validated.
4. Assemble the structured proposal with `ProposalAssembler.assemble`.
5. Publish the proposal digest with `ReviewState.publish`. Record the UTC preview time under `cisco_proposal_at`.
6. Return the structured proposal as JSON.

Step 1 runs before step 2. A failed preview therefore clears review, as version 1 does.

## Review and Export Order

1. Parse the request body as JSON. Reject a body that is not an object.
2. Check that `proposal_version` equals 2 and that the key set equals the ten keys in `proposal-v2.md`. Reject any other body with HTTP 400.
3. Compare the digest of the body with the session value. Reject a mismatch with HTTP 409.
4. For review, refuse when the current UTC time is `cisco_proposal_at` plus `REVIEW_LIFETIME` or later. Return HTTP 409 with the preview expiry message.
5. For review, set `cisco_reviewed` to the digest and `cisco_reviewed_at` to the current UTC time.
6. For export, require `cisco_reviewed` to equal the digest. Reject a mismatch with HTTP 409.
7. For export, refuse when the current UTC time is `cisco_reviewed_at` plus `REVIEW_LIFETIME` or later. Return HTTP 409 with the review expiry message.
8. Return the same object. Export adds the attachment header.

## Messages

The messages reuse the version 1 text:

- `Select one configuration file.` (HTTP 400, when the file is missing)
- `Submit a valid JSON proposal.` (HTTP 400, for an invalid body)
- `Create a new preview before review or export.` (HTTP 409, when the session does not match)
- `Review this proposal before export.` (HTTP 409, when export lacks a review)

Version 2 adds two messages for the lifetime:

- `The preview expired. Create a new preview before review.` (HTTP 409, when the preview is 15 minutes old or more)
- `The review expired. Review this proposal again before export.` (HTTP 409, when the review is 15 minutes old or more)

## Logging

- Before each action, log an `info` line. The messages are `Validating a versioned converter preview.`, `Validating a versioned converter review.`, and `Validating a versioned converter export.`
- After each success, log a `debug` line with the result. For example, `Completed a versioned converter export.`
- After a validation failure, log an `error` line with the exception class name only.
- No log line holds source text, the template name, an unsupported value, or a secret. Each log line uses ASCII text.

## Limits

- The request bound is 16 MiB plus 16 KiB for the converter prefix (research rows 6 and 76).
- A source above 16 MiB returns HTTP 400, as version 1 does.
- No route opens a network connection, sends a Mist request, or writes a file (FR-014).
