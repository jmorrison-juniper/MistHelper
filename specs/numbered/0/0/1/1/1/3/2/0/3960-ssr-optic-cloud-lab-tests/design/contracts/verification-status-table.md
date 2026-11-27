# Contract: Verification status table

This contract sets the format of the section 14 verification table in documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, at lines 358 to 365.

## Table structure

- The header row reads `Statement`, `Source`, and `Lab test`. The header text does not change.
- The table holds six rows, at rows 360 to 365. The table adds no row unless the owner decides so (D-6).
- The Statement cell and the Source cell do not change. Exception: row 361 names the new section 11 row for H-2 (D-7).

## Lab test cell format

- A cell that holds a recorded output starts with `Run on` and then the release string, copied from the output.
- The cell adds one sentence that states the result. The sentence uses the words from the sanitized output.
- A cell that holds no output keeps the text `Not run`, followed by its reason.

## Checks

- Each cell in rows 360 to 365 starts with `Run on` when the final pull request opens (TEST-07, SC-002).
- No cell names a release that the output does not show (FR-005).
- No cell reports a result without a sanitized output (FR-016).
