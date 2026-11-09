# Research

## Decision

Use the collected-result count as the successful count.
Calculate the skipped or failed count as the input count minus the successful count.

## Rationale

The existing batch collector appends only after the runner returns and its result is unpacked.
Missing IDs and runner exceptions do not append results.
This boundary also preserves successful empty results.

## Alternatives Considered

Do not count loop iterations because they include excluded records.
Do not add coverage columns or metadata files because the reserved repair must preserve export schemas.
Do not use mutable global heading state because later runs could inherit a partial label.

## Evidence

The issue reproduction reports three processed organizations for one successful result.
The three report renderers each contain an unconditional `All Orgs` heading.
Existing tests inject dependencies with `_configure_msp` and patch organization discovery with `monkeypatch`.
