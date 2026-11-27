# Data Model: Organization and site identifier defaults

This record adds no database table, file format, or stored record. The entities below describe the values that the code checks and the batch state that the audit tracks.

## Required Identifier

- **Meaning**: An organization or site identifier that a tenant SDK call needs.
- **Natural key**: The Mist identifier itself. The OpenAPI file declares it as a UUID (RC-20, RC-21). The code treats it as an opaque string (D-4).
- **Valid form**: A `str` with at least one non-whitespace character. The value is kept unchanged.
- **Invalid forms**: `None`, an empty string, a whitespace-only string, and any other type.
- **States**:
  - `supplied` to `valid`: the value passes the check and reaches the SDK call.
  - `supplied` to `refused`: the check fails, and the refusal occurs before the SDK call.

## Optional Site Identifier

- **Meaning**: The site scope of a policy or template discovery call.
- **Natural key**: The Mist site identifier, or the absence of a site.
- **States**:
  - `none`: `None` was supplied. Only the organization SDK call runs (FR-003).
  - `valid`: a required identifier passed the check. The organization SDK call and the site SDK call run.
  - `refused`: the value is blank, non-string, or otherwise invalid. No SDK call runs (FR-004).

## Refusal

- **Meaning**: The record of a missing or invalid required identifier.
- **Fields**: `field` (`org_id` or `site_id`), `message` (one fixed string), and `log record` (one error record).
- **Redaction**: The record holds no input value (FR-005, FR-006).
- **States**:
  - `detected` to `raised`: the validator raises `ValueError`.
  - `raised` to `logged`: the validator writes one error record before the raise propagates.
  - `propagated` to `surfaced`: the service ping manager prints the message (`service_ping_manager.py:467-468`).

## Masking Default

- **Meaning**: A source default that turns a missing identifier into an empty or organization-only scope.
- **Natural key**: The tuple of repository path, enclosing function name, identifier key, default form, and occurrence index within that function. The key does not use the line number, because line numbers move.
- **Default forms** (D-10): a `.get` call with an identifier key and an empty default. A `str(` wrapper around such a call. An expression followed by `or ""`.
- **Classes**:
  - Class A: the value becomes an API scope, a write target, a lock key, or a required service input. Class A needs a repair.
  - Class B: the value is a display label, a record shape, a lookup result, or an optional filter. Class B needs no repair in this issue.
- **States**:
  - `found` to `classified`: the scan assigns Class A or Class B.
  - `classified-A` to `repaired`: the repair adds a refusal before the write or call.
  - `classified-A` to `accepted-debt`: the baseline records the occurrence, with a reason, and the count never rises on its own.
  - `classified-B` to `recorded`: the baseline records the occurrence as safe.

Warning: a masking default in Class A that stays unrepaired can send a write to an empty scope.

## Baseline Entry

- **Meaning**: The count of accepted masking defaults in one normalized repository path.
- **Natural key**: The normalized repository path, such as `src/example.py`.
- **Value**: A positive integer count.
- **Rules**: The count may fall. It may rise only through a reviewed change to the baseline file. The guard never raises a count on its own (contract `ratchet-baseline.md`).
- **States**:
  - `recorded` to `lowered`: a repair removes an occurrence. The count falls.
  - `recorded` to `removed`: the count reaches zero. The path leaves the file.

## Batch

- **Meaning**: One reviewable change set in the staged plan (D-1, D-8).
- **Natural key**: The batch identifier: `B1`, `B2`, `B3`, `B4`, or `B5`.
- **States**:
  - `planned` to `red`: the failing tests exist and fail on main.
  - `red` to `green`: the tests pass after the change.
  - `green` to `gated`: each local gate passes.
  - `gated` to `published`: the pull request exists after the parent grant.
  - `published` to `merged`: the squash merge lands on `main`.
  - Any state to `blocked`: a structural or review hold stops the batch (D-14, D-11).

Caution: batch B4 and batch B5 stay in `gated` until a human removes `needs-human-review` from the issue.
