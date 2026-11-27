# Contract: Durable Manifest and Finalization Marker

This contract covers the files that one run folder holds. The run folder sits under `data/websocket-streams/<run_id>/`. The keys of `manifest.json` do not change. The marker file is new.

## manifest.json

The file holds one JSON object with these keys.

| Key | Type | Value |
|-----|------|-------|
| `status` | text | `writing`, `ready`, or `failed` |
| `partial` | boolean | True when a target or a write failed. The value is True while `status` is `writing`. |
| `sequence` | integer | The count of saved results |
| `owner_pid` | integer | The process identifier of the owner |
| `files` | list of text | The saved relative paths, in sorted order |
| `targets` | list of objects | One outcome for each target |
| `expires_at` | text or null | Null for the hardware preset |
| `durable` | boolean | True for the hardware preset |
| `run_id` | text | 32 lowercase hexadecimal characters |

Example with no saved file:

```json
{"status":"writing","partial":true,"sequence":0,"owner_pid":1234,"files":[],"targets":[],"expires_at":null,"durable":true,"run_id":"0123456789abcdef0123456789abcdef"}
```

Rules:

- The replace is atomic. A reader never sees partial content (FR-014).
- A refused replace leaves the file unchanged.
- After finalization returns, one of these conditions holds. The `status` is `ready` or `failed`. Or the file `finalization-failed.json` exists in the same folder.
- The file never holds a local path, a token, or a device secret. The existing redaction applies.

## finalization-failed.json

The marker exists only after a refused final replace. The marker uses the same atomic replace and the same encoding as `manifest.json`.

| Key | Type | Value |
|-----|------|-------|
| `status` | text | Always `failed` |
| `partial` | boolean | Always true |
| `durable` | boolean | Always true |
| `run_id` | text | Equal to the run folder name |
| `reason_code` | text | Always `manifest_not_final` |

Example:

```json
{"status":"failed","partial":true,"durable":true,"run_id":"0123456789abcdef0123456789abcdef","reason_code":"manifest_not_final"}
```

Rules:

- The archive does not include the marker. The archive reads only the saved files and `manifest.json` (`artifacts.py:677`).
- The orphan scan reads only `manifest.json`. A run folder with `durable` set to true stays in place (`artifacts.py:595`).
- The marker holds no path and no target identity.
