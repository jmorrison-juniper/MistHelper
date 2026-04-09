# Data Model: MistAPI SDK Compatibility Audit

This feature is an audit and compatibility-planning effort. It does not add new runtime storage, but it does use a small planning model to keep the findings organized.

## Entities

### ReleaseNoteEntry

Represents one MistAPI GitHub release entry.

| Field | Purpose |
|---|---|
| `tag_name` | Release tag, such as `v0.61.4` |
| `published_at` | Published date/time used to order releases |
| `summary` | Human-readable release summary |
| `change_type` | Breaking, feature, fix, or deprecation |
| `affected_areas` | SDK modules or endpoint families mentioned in the notes |

**Validation rules**:

- `tag_name` must be newer than `0.59` for this audit.
- `change_type` must be one of the documented categories.
- Each entry must be traceable to a release note source.

**Relationships**:

- One `ReleaseNoteEntry` can map to many `CompatibilityFinding` records.

### SDKCallSite

Represents one direct MistAPI usage inside `MistHelper.py`.

| Field | Purpose |
|---|---|
| `file_path` | Source file containing the call site |
| `symbol` | MistAPI function or method name |
| `current_call_signature` | Current arguments used by MistHelper.py |
| `workflow_name` | User-facing workflow that depends on the call |
| `category` | Stats, alarms, events, SLE, maps, WLAN, E911, or other |

**Validation rules**:

- `file_path` must resolve to `MistHelper.py` for this audit.
- `symbol` must be a direct `mistapi` call, not a helper abstraction.
- `current_call_signature` must reflect the actual source usage.

**Relationships**:

- Each `SDKCallSite` belongs to exactly one `CompatibilityFinding` once reviewed.
- One `SDKCallSite` can be covered by one or more `VerificationWorkflow` items.

### CompatibilityFinding

Represents the audit decision for a call site.

| Field | Purpose |
|---|---|
| `status` | `compatible`, `updated`, or `deferred` |
| `reason` | Why the call site received that status |
| `release_version` | Release that introduced the relevant behavior change |
| `action_required` | Any code or verification action needed |
| `evidence` | Link or note supporting the finding |

**Validation rules**:

- Every reviewed `SDKCallSite` must have exactly one status.
- Any call site affected by a breaking change must not remain in `compatible` status.
- A `deferred` status must include a reason and a follow-up note.

**State transitions**:

- `identified` -> `reviewed` -> `updated` or `deferred`
- `updated` -> `verified` after the representative workflow passes

### VerificationWorkflow

Represents a smoke-test or regression check used to prove compatibility.

| Field | Purpose |
|---|---|
| `workflow_name` | Name of the workflow under test |
| `coverage_area` | The group of call sites it exercises |
| `expected_result` | What must remain true after the update |
| `validation_method` | How the workflow is verified |
| `result` | Pass/fail outcome |

**Validation rules**:

- At least one verification workflow must cover every impacted call site.
- Verification must include the breaking insight-metric path and the unaffected stats/event paths.
- A passing result must be recorded before the audit can be considered complete.

## Relationships summary

- `ReleaseNoteEntry` drives the compatibility review.
- `SDKCallSite` is the unit of audit work.
- `CompatibilityFinding` records the audit decision for each call site.
- `VerificationWorkflow` confirms that the chosen decision holds in practice.

## Persistence note

No new runtime storage is introduced. These entities exist only to structure the audit documentation and any later implementation notes.
