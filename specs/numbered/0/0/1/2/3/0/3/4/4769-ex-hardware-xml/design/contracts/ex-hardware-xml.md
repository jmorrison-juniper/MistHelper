# EX Hardware XML Portal Contract

**Feature**: [spec.md](../../spec.md)

## Preview Request

Use the authenticated Operations portal WebSockets batch preview route. A preset request has this shape:

```json
{
  "preset": "ex-hardware-xml",
  "format": "both",
  "scope_revision": 0
}
```

`format` is optional and defaults to `xml`. Valid values are `xml`, `json`, and `both`. The server rejects unknown fields, unsupported formats, disabled shell access, incomplete discovery, and requests that exceed existing target limits.

The browser does not submit a command, organization ID, site ID, or device ID. The server resolves every site and each eligible EX target from the configured organization. It binds the fixed command and output format to the preview snapshot.

## Preview Response

Return the preset, format, and ordered server-owned `fixed_commands` array.
Include the online target count, offline and unknown exclusion counts, expiry, and exact confirmation phrase.
Native output and terminal transcripts remain private.

## Start Request

Use the existing batch admission route with the opaque preview ID and the existing validated concurrency and confirmation fields. Do not send a command or change the output format at start. The format is fixed in the preview.

## Progress and Results

Use existing summary and target routes. Report one target outcome and separate requested-format outcomes.
Skipped targets have no shell dispatch. Partially failed targets retain successful format files.
The summary exposes `run_id` for durable filesystem access.

## Artifact Routes

Use the existing manifest and ZIP download routes. The ZIP contains the selected `.xml` and/or `.json` files and the existing safe manifest. The manifest does not contain raw terminal output, command echoes, credentials, or secret values.

Hardware files remain in `data/websocket-streams/<run_id>/hardware` after session expiry and restart.
The durable manifest remains beside that directory. Portal download routes still require a retained session.

## Security and Failure Contract

- Preserve existing portal authentication, authorization, CSRF, shell enablement, preview ownership, single-use, capacity, timeout, cancellation, and artifact retention checks.
- Enforce `preset`, format enum, EX-only targets, and the fixed command on the server.
- Keep each successful result under the existing per-record and total run quotas. BOTH mode counts both files.
- Return safe 4xx responses for invalid or out-of-scope requests. Keep Mist 4xx and 5xx setup failures as per-target failure outcomes after an admitted run.
- Do not write a success file for incomplete, malformed, oversized, timed-out, or secret-bearing output.
- Do not report production-device or live-output results in automated test results.
