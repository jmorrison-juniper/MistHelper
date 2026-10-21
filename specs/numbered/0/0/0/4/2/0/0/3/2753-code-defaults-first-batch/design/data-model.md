# Data Model: Code Defaults First Batch

## Candidate

| Field | Contract |
| --- | --- |
| Identity | Repository-relative path, enclosing symbol, syntax shape, input key, and occurrence within that symbol |
| Location | Current line and column for review, not the sole identity |
| Empty kind | String, list, dictionary, tuple, or set |
| Consumer role | Selector, identity, comparison, filter, path, required collection, optional value, or display-only |
| Classification | High, display-only, valid-optional, already-validated, excluded-ownership, or unresolved |
| Ownership | Issue or scope that may change the consumer |
| Evidence | Producer and consumer contract that supports the classification |

Missing fields, duplicate identities, and unknown classification values invalidate the inventory.
Line movement alone must not manufacture a new candidate.
A changed input key or consumer requires review even if the aggregate count does not increase.
Every current in-scope candidate must have a matching reviewed disposition. A newly added
high-severity identity is reported as a regression before the missing-disposition check; a new
non-high candidate still requires review before the guard can pass.

## Scan Result

Record criterion version, source revision, selected paths, discovered count, parsed count, failures, ordered candidates, and separate severity and classification totals.
Each selected tracked source file is parsed once.
An explicit scope must contain all five expected files before the guard can pass.
Repository-wide discovery does not allocate ownership or set the first-batch baseline.

The five syntactic shapes are dictionary `get`, dictionary `pop`, environment reads, attribute reads, and parameter defaults.
Only the assessment's empty literals and empty set construction qualify.
Exclude non-empty defaults and test, cache, virtual-environment, and untracked inputs.

## Accepted Baseline

Record schema version, scan criterion version, reviewed revision, the exact five-file scope, and every reviewed candidate disposition.
Derive the high-severity total from those records and verify any stored total matches it.
No accepted numeric value exists during planning.
The historical total of 59 must never be inserted as an unverified current baseline.

Record dispositions for historical targets: repaired, already repaired, valid optional input, display-only, or excluded ownership.
An exclusion requires a named ownership boundary and evidence.
Do not turn a defect into an exclusion merely to make the guard pass.
Store the accepted high-severity identity list separately from candidate dispositions.
The guard compares identities so a removed candidate cannot hide a new candidate.
Each disposition records the identity, classification, non-empty evidence, and ownership.
At guard time, every current candidate must match a reviewed disposition and the current
policy classification. Deleted candidates are visible through removed accepted-high identities.

## Failure Result

Use the existing workflow's error or failed-record shape.
The result identifies the missing field and caller without storing a private payload.
A record transitions from pending to validated before any dependent action.
Validation failure transitions to failed, never completed or successfully empty.
Earlier completed records remain intact.

## Guard Decision

The guard returns passed, regression, or invalid-input status with parsed-file counts.
Invalid input includes unreadable files or policy, parse errors, zero selection, missing expected paths, and unclassified in-scope candidates.
Regression includes new high-severity candidate identities or a high-severity count above the accepted baseline.
Removed candidates produce a visible decrease. They cannot offset a new candidate.
