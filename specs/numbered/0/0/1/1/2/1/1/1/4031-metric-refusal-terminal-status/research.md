# Research: Metric Refusal Terminal Status

## Question 1: Which existing marker changes the portal terminal status?

**Decision**: Emit one `ERROR` log line containing the existing `Failed to`
marker when a metric operation records one or more refusals.

**Rationale**: `web_portal/services/operation.py` scans captured operation
messages for `HANDLED_ERROR_MARKERS`. The tuple contains `failed to`. The
portal therefore needs no change and receives the smallest compatible signal.
The refusal report remains separate and keeps the metric name, HTTP status, and
reason for the operator.

**Alternatives considered**:

- Reuse the refusal report only. Rejected because its wording does not match
  the portal handled-error marker tuple.
- Add a new portal marker. Rejected because the issue forbids a portal change.
- Raise an exception after the batch. Rejected because the batch must preserve
  successful rows and must continue after each refused response.

## Question 2: Where should the marker be emitted?

**Decision**: Emit the marker in each operation's existing `_run_export`
completion path, after `_finalize()` and the existing refusal report.

**Rationale**: `_finalize()` writes successful rows or the existing empty
export. The marker after that write preserves partial output and also covers a
batch that contains only refused responses. The existing
`MetricRefusalLog.report()` remains the source of refusal details.

**Alternatives considered**:

- Emit the marker from `_fetch_one_metric()`. Rejected because it would create
  one terminal error signal per refusal and would mix per-metric handling with
  batch completion.
- Emit the marker from `MetricRefusalLog`. Rejected because the shared helper
  is explicitly out of scope and does not know the operation's output scope.
- Change `web_portal/services/operation.py`. Rejected by FR-014.

## Question 3: How should successful rows and counts behave?

**Decision**: Keep `_fetch_one_metric()` returning `None` for a refusal, keep
  `_collect_metrics()` appending only non-`None` rows, and use the existing
  refusal list only as a post-batch status condition.

**Rationale**: The current design already excludes refusal bodies, continues
  the loop, counts only valid non-empty rows, and reports each refusal. The
  smallest safe repair adds only the terminal marker condition.

**Alternatives considered**:

- Return a new result object from the collector. Rejected because it expands
  the implementation surface and can change successful behavior.
- Add a refusal row to the export. Rejected by FR-003.
- Count refusals as retrieved metrics. Rejected by FR-005 and FR-006.

## Question 4: Is an external interface contract artifact required?

**Decision**: Do not create `contracts/`.

**Rationale**: This plan changes no public endpoint, command schema, response
  shape, or new integration. It consumes the existing portal handled-error
  contract through an existing log marker. The contract is documented in this
  plan and in the validation guide.

## Question 5: Which validation commands apply?

**Decision**: Run the two focused pytest modules, compile validation, Ruff,
  Black checks for the changed Python files, and a diff-scope check.

**Rationale**: The focused modules are the explicit test scope. Compile,
  formatting, and lint checks cover the two implementation files and two test
  files. The diff-scope check proves that the implementation manifest remains
  limited to the two operations, two focused tests, and one changelog
  fragment. Full deployment gates remain implementation-phase work.

**Alternatives considered**:

- Run the complete repository quality pipeline during planning. Rejected
  because this phase creates design artifacts only and does not change product
  code.
- Add a contract test file. Rejected because the existing portal contract is
  read-only context for this feature and the user forbids unrelated test files.
