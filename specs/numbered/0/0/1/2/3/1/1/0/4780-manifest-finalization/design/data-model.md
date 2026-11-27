# Data Model: Hardware Manifest Finalization After a File Lock

Each entity lists its fields and constraints. A task cites a field as `Entity.field`. The run folder uses the artifact identifier as its natural key. The identifier is a 32-character lowercase hexadecimal string that the service generates for each run.

## BatchArtifactRecord

The in-memory state of one run folder. The class sits in `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 56-73).

| Field | Type | Constraint |
|-------|------|------------|
| `BatchArtifactRecord.artifact_id` | text | Required. A 32-character lowercase hexadecimal string. It names the run folder. |
| `BatchArtifactRecord.status` | enum | `writing`, `ready`, or `failed`. The default is `writing` (`artifacts.py:68`). |
| `BatchArtifactRecord.partial` | boolean | True when any target or any write failed. |
| `BatchArtifactRecord.complete` | boolean | True only after the final manifest replace succeeds. |
| `BatchArtifactRecord.manifest_stale` | boolean | New. True after a refused in-run manifest replace. False after a successful manifest write. |
| `BatchArtifactRecord.files` | set of text | Relative paths of the saved native files. Each path passes the checked path rule (`artifacts.py:301`). |
| `BatchArtifactRecord.outcomes` | list of mapping | One entry for each target. Each entry holds a redacted target identity and the target state. |
| `BatchArtifactRecord.sequence` | integer | Count of saved results. It never decreases. |

### State transitions

| From | Event | To | Requirement |
|------|-------|----|-------------|
| `writing` | Finalization replace succeeds | `ready`, and complete is set to True | FR-006 |
| `writing` | Finalization replace refused beyond the budget | `failed`, and partial is set to True. The marker is written. | FR-007, FR-008 |
| `writing` | Report publish fails during finalization | `failed` | FR-007 |
| `writing` | Quota or link refusal during the run | `failed` | FR-003 |
| `writing` | Refused in-run manifest replace | `writing`, and manifest_stale is set to True | FR-003 |
| `writing` with manifest_stale True | Later in-run manifest replace succeeds | `writing`, and manifest_stale is set to False | FR-004 |
| `ready` or `failed` | Any further write | Refused | FR-006 |

## DurableManifest

The file `manifest.json` in the run folder. The file keeps its existing keys. See `design/contracts/manifest-json.md`.

| Field | Type | Constraint |
|-------|------|------------|
| `DurableManifest.status` | enum | `writing` during the run. `ready` or `failed` after a successful final replace. |
| `DurableManifest.run_id` | text | Equal to `BatchArtifactRecord.artifact_id`. |
| `DurableManifest.durable` | boolean | True for the hardware preset. Orphan cleanup keeps any run folder with this flag (`artifacts.py:595`). |
| `DurableManifest.files` | list of text | Equal to the sorted `BatchArtifactRecord.files` at the last successful write. |

The manifest reflects the last successful replace. A later refused replace leaves the file unchanged (FR-014).

## FinalizationMarker

The file `finalization-failed.json` in the run folder. It exists only after a refused final manifest replace. See `design/contracts/manifest-json.md`.

| Field | Type | Constraint |
|-------|------|------------|
| `FinalizationMarker.status` | enum | Always `failed`. |
| `FinalizationMarker.partial` | boolean | Always True. |
| `FinalizationMarker.durable` | boolean | Always True. Orphan cleanup keeps the run folder. |
| `FinalizationMarker.run_id` | text | Equal to `BatchArtifactRecord.artifact_id`. |
| `FinalizationMarker.reason_code` | text | Always `manifest_not_final`. |

## NativeFile

One saved XML or JSON reply of one target.

| Field | Type | Constraint |
|-------|------|------------|
| `NativeFile.relative_path` | text | Must pass the checked path rule (`artifacts.py:301`). |
| `NativeFile.state` | rule | Written once. The publish stage refuses an existing destination (`artifacts.py:205`). |
| `NativeFile.preservation` | rule | No manifest failure, expiry, or cleanup path deletes the file (FR-010). |

## BatchRunResult (CLI)

The result of one organization run. The class sits in `src/operations/exporting/ex_hardware_inventory/run/batch.py` (lines 100-111).

| Field | Type | Constraint |
|-------|------|------------|
| `BatchRunResult.run_id` | text | Empty when no batch started. Otherwise the run folder name. |
| `BatchRunResult.cancelled` | boolean | True when the operator stopped the batch. |
| `BatchRunResult.results` | tuple of `TargetResult` | One result for each confirmed target. |
| `BatchRunResult.reason` | text | Empty when the batch ran. |
| `BatchRunResult.artifact_ready` | boolean | New. Default True. False when the artifact status of a started batch is not ready. |

## Natural Keys

- A run folder uses `artifact_id`.
- A target uses `target_key`, which the service derives from the target identity.
- A native file uses its relative path inside the run folder.
- The marker and the manifest use the fixed names `finalization-failed.json` and `manifest.json`.
