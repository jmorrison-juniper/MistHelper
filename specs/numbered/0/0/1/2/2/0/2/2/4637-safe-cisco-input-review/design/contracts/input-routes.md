# Contract: Input Routes

This contract defines the routes of the isolated converter blueprint at `/cisco-config-converter`. The blueprint stays out of the shared portal. Task T007 implements the input rules, and task T009 implements the observation route.

## Common Rules

- Each POST route requires the CSRF token. The existing host check at `routes.py` lines 103 to 108 enforces it.
- Each response carries `Cache-Control: no-store`. The existing `no_store` hook at `routes.py` line 60 enforces it.
- Each error returns JSON with one `error` field. The field holds a safe message. The response never includes a path or a traceback.
- The request body limit is 16,777,216 bytes plus 16,384 bytes. Flask refuses a larger body with 413 before parsing.

## Routes

| Method | Path | Request | Success | Error statuses | Review effect |
| --- | --- | --- | --- | --- | --- |
| GET | `/cisco-config-converter/` | None | HTML page | None | None |
| GET | `/cisco-config-converter/inputs` | None | 200 with the catalog document | 409 when the private root is unsafe | None |
| POST | `/cisco-config-converter/preview` | Multipart: exactly one of `file` or `stored_id`, plus `name`, `type`, and optional `retain` set to `on` | 200 with the unchanged proposal | 400 for an invalid selection or a retain request while retention is disabled. 409 for a save collision or an unsafe root. | Clears the earlier review first. Publishes a new digest on success. |
| POST | `/cisco-config-converter/observations` | Multipart with the same selection fields and no `retain` field | 200 with the observation document | 400 for an invalid selection or any `retain` field | None |
| POST | `/cisco-config-converter/review` | JSON proposal | Unchanged | Unchanged | Approves the digest |
| POST | `/cisco-config-converter/export` | JSON proposal | Unchanged | Unchanged | Requires an approved digest |

## Selection Rules

These rules apply to `/preview` and `/observations`.

1. The request sends exactly one of `file` or `stored_id`.
2. A request with neither field returns 400 with the message `Select one configuration file.`
3. A request with both fields returns 400 with the message `Select one stored input or one file, not both.`
4. The `stored_id` value must match `^[0-9a-f]{32}$`. The server resolves the file. A client never sends a path.
5. An unknown or malformed `stored_id` returns 400 with the message `Select a stored input from the current list.`
6. A file upload follows the name, suffix, size, and encoding rules of `SourceConfiguration`.
7. The `name` and `type` fields keep their current rules.

## Preview Order

The preview runs these steps in order. The order keeps a failed save from producing an approvable review.

1. Remove `cisco_proposal` and `cisco_reviewed` from the session.
2. Build the source from the upload or from the stored input.
3. Convert the source with `IOSDnsConverter`.
4. When `retain` is `on`, save the source with `PrivateInputRetention.save`. A failed save returns 400 or 409 and publishes no digest.
5. Publish the proposal digest.
6. Return the proposal with the current shape.

## Catalog Response

```json
{"retention_enabled": false, "inputs": [{"id": "0123456789abcdef0123456789abcdef", "suffix": ".cfg", "bytes": 1024, "created_at": "2026-11-26T00:00:00+00:00"}]}
```

The response includes no path, no original name, and no file system detail. When the root does not exist, `inputs` is an empty list.

## Observation Response

The response follows `contracts/observation-families.md`. The route changes no session value. It writes no file.

## Logging

- The route logs one info line before each action and one debug line after it.
- The route never logs source text, file names from clients, or the content of a file.
