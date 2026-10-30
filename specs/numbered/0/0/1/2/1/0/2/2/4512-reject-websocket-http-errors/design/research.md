# Research

**Decision**: Validate HTTP 200 before either device response payload is read.

**Rationale**: The SDK retains parsed error data on `APIResponse.data`.
Both discovery readers currently accept that data without checking status.
Existing device command handling also expects HTTP 200.

**Alternatives considered**: A shared fetcher changes injection and error handling beyond this defect.
Returning an empty dictionary would disguise failure as successful empty discovery.
Use explicit exceptions and existing nonfatal handlers instead.

No unresolved technology choice remains.
