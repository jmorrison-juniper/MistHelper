# Cleanup-order research

## Decision

Publish terminal results after the existing cleanup attempt.

## Rationale

Current main is `9991d30a187e5d215462eefac60a09a57e5f99e5`.
The unchanged execution source blob is `1211c1f0576641b09510e136b8e27648870fc38d`.

The deterministic proof holds `mist_delete` before the fake session records DELETE.
The worker signals barrier entry before the test reads the sink.
The test releases and joins the worker even when its assertion fails.
All four cases failed with `Terminal state preceded matching DELETE cleanup.`
The cases cover site and organization captures, with normal monitoring and an execution exception.
The run reported `4 failed in 0.26s`.

The initial draft used an unsupported organization utility key.
That draft had two setup failures and two ordering failures.
The corrected proof uses `mxedge.orgRemotePcap` and has four ordering failures.

## Alternatives considered

- Repeated passing runs cannot prove ordering.
- A longer timeout does not establish cleanup completion.
- Changing the existing assertion would hide the defect.
- Moving cleanup into `_execute()` would leave execution exceptions outside the completion boundary.
- Existing error classification treats a stop flag as stopped. It cannot classify cleanup failure safely.

## Scope limits

No changes to capture duration, stream monitoring limits, trigger membership, or capture identity checks.
No production request runs.
The issue artifact list endpoint returned HTTP 404.
The issue and its comments contain no image references.
