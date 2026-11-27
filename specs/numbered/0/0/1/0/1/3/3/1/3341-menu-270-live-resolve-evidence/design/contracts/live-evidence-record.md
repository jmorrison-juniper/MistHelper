# Contract: Owner Evidence Record

The owner evidence record is one comment on issue #3341. The repository holds no copy of it. The owner posts it after the live check, using the fields below in this order.

## Fields

1. **Date**: the UTC start time of the run, in ISO 8601 form.
2. **Approval reference**: the date or the comment identifier of the written approval.
3. **Lab organization**: the label of the organization. Do not give the organization identifier.
4. **Action**: the topic name and the count of selected actions. The count must be 1.
5. **Resolution code**: the code that the run sent.
6. **HTTP status**: the number from the `http_status` column.
7. **Outcome**: one value from the outcome list in `results-csv.md`.
8. **Verified status**: the text from the `verified_status` column.
9. **Acknowledge step**: `skipped` when the answer was blank.
10. **Next step**: accepted (T006 follows), refused (no retry, issue #4389 keeps the cause), or unverified (check the action in the Mist UI).

## Rules

- Do not include a credential, a token, or a raw response body (FR-010).
- Do not paste the full results row. Quote only the outcome, the HTTP status, and the verified status.
- Write each date in UTC.

## Acceptance Rule

The record shows acceptance only when all three conditions hold:

- The HTTP status is in the 2xx range.
- The outcome is `resolved`.
- The verified status is not one of the open statuses (`open`, `inprogress`, or `reoccured`).

Only an accepted record permits the change in task T006.
