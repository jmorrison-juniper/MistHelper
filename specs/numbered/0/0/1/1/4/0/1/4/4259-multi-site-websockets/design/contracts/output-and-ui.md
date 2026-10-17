# Output and UI Contract: Multi-site WebSocket batches

**Issue**: #4259

## 1. Saved Output

The operator selects `combined`, `grouped`, or `both` before batch admission.
For grouped output, select `site`, `device_type`, `device`, or `client`.
Reject unknown modes and unsupported groupings.
A site-only operation cannot use device or client grouping.
A device-only operation cannot use client grouping.
An organization-only operation supports combined output or site grouping through an explicit organization bucket.

Use the existing approved output boundary under `data/`.
The proposed relative session root is `data/websocket-streams/{session_id}/`.
The server creates each path component.
Do not accept a label, filename, directory, or archive path from the request.

### Layouts

Each session has `manifest.json`.
The following paths are relative to the session root.

| Selection | Relative data path |
| - | - |
| Combined | `combined.jsonl` |
| Group by site | `sites/{site_key}/results.jsonl` |
| Group by device type | `device-types/{family}/results.jsonl` |
| Group by device | `devices/{site_key}/{device_key}.jsonl` |
| Group by client | `clients/{site_key}/{parent_key}/{client_key}.jsonl` |

The device-type file retains each record's site and device identity.
Client parent keys identify the verified switch or map.
Use `organization-{org_id}` for a null-site organization target.
Never assign an organization target to an arbitrary site.

### Name Safety

Use canonical lowercase UUIDs and normalized MACs when available.
For composite resource keys, use a fixed-length digest of the full natural-key tuple.
Use only approved lowercase family names.
Keep original names as redacted display labels inside the manifest.
Reject reserved names, empty components, absolute paths, separators, and dot components.
Use `pathlib.Path` for all host path operations.

Verify resolved containment beneath the session root before each write or download.
Reject symlink components and symlink archive entries.
Do not follow a symlink during cleanup.
Use exclusive session-directory creation and private file permissions.
Never overwrite another session's files.
Check archive entry names separately from host paths.

The five-item source structure rule does not cap runtime result file counts.
Runtime output still has the target and disk limits in the plan.

## 2. Record and Write Rules

Every line is one UTF-8 JSON object followed by a newline.
Use the result envelope from [data-model.md](../data-model.md).
Keep parent sequence and target identity in every file.
Preserve complete JSON lines when output stops.
Do not deduplicate equal payload text.
Grouped copies retain the same `(session_id, seq)` identity as combined records.

Write a terminal outcome for each target, including empty, failed, and cancelled targets.
Write output before the live buffer can evict it.
Use one bounded writer queue for the parent.
Apply backpressure instead of accepting unbounded pending writes.
Count combined and grouped copies against the same 64 MiB batch disk limit.
Reserve 1 MiB of that limit for manifest and terminal outcome metadata.

Redact before output enters the public buffer or artifact writer.
Apply the existing secret-redaction boundary to messages and exceptions.
Retain redactor state across split chunks for one target.
Test tokens split across frames.
Do not log or export WebSocket URLs, API tokens, passwords, or shell secrets.
Do not save raw command text in the manifest.
If safe redaction cannot be proved, omit the affected payload and report the omission.

Write manifests through a temporary file and atomic replacement.
Before rewriting an existing manifest, preserve a private backup.
Validate the new manifest before replacement.
Count temporary files and backups within the disk limit.
Remove obsolete temporary files and backups through session cleanup.
Verify each required flush and final file before reporting `ready`.

If a write fails, preserve previously saved files.
Stop queued work and request active target termination.
Report `output_failed` and `artifact_status: failed`.
Do not label the batch complete when required writes fail.
If the disk cannot hold final metadata, expose the failure through the parent response.

## 3. Retention and Downloads

The batch uses the current session retention policy.
Keep no more than five ended sessions.
Expire an ended session after 600 seconds.
The first applicable count or age rule removes its artifact tree.
Keep the current idle, lifetime, and stuck-stop rules.

Explicit deletion removes an ended session's files and index entries.
Expiry and deletion close artifact handles before removal.
A bounded download pin delays removal until the response ends or its deadline expires.
Report cleanup failure and retry it through the reaper.
Never delete outside the verified session root.

On restart, remove abandoned session directories because process-local sessions cannot resume.
Use an exclusive process lock for startup cleanup.
Do not run a broad directory deletion without verified session ownership.
Do not replay saved shell commands.

A live combined download uses a fixed last-sequence snapshot.
A final archive contains the requested layout and manifest.
Partial batches remain downloadable until expiry.
Each download states whether collection is partial.
The manifest reports target counts, terminal outcomes, truncation, files, and expiry.

## 4. Tab Behavior

Use the existing template and JavaScript files.
Single Site is the initial tab.
Keep its current test IDs and behavior.
Do not reset or stop a session when the operator changes tabs.
Keep separate form state for each tab.
Share the public session capacity indicator.

Use accessible tab roles, keyboard navigation, and selected-state attributes.
Give each new interactive element a stable `data-testid`.

| Test ID | Purpose |
| - | - |
| `ws-single-site-tab` | Select the unchanged Single Site panel |
| `ws-multi-site-tab` | Select the Multi Site panel |
| `ws-batch-operation` | Select one catalog operation |
| `ws-batch-sites` | Select all eligible sites or a site subset |
| `ws-batch-targets` | Select supported resources with parent identity |
| `ws-batch-commands` | Enter a finite shell command list |
| `ws-batch-layout` | Select output mode and grouping |
| `ws-batch-preview` | Resolve and review the exact targets |
| `ws-batch-confirmation` | Enter the preview phrase for the exact batch |
| `ws-batch-start` | Start the confirmed preview |
| `ws-batch-progress` | Show aggregate counts and per-target states |
| `ws-batch-stop` | Stop queued and active work |
| `ws-batch-download` | Download saved results |

Derive Multi Site fields from catalog metadata.
Show site and target identity for each resource.
Exclude unsupported families with a plain reason.
Show empty, denied, incomplete, and unavailable discovery as distinct states.
Disable start until the preview and required confirmation are valid.
Invalidate the preview when operation, parameters, targets, or commands change.
Discard discovery responses whose selection revision is stale.

The review panel shows the exact operation, command list, and explicit target set.
It shows target count, concurrency, output layout, and storage limits.
Shell commands require explicit selected devices.
Do not offer an interactive Multi Site terminal or broadcast input.

## 5. Progress and Safety

Keep target progress visible after a target fails.
Display one outcome for every admitted target.
Label each output with its site, target type, and target identity.
Use a clear organization label when `site_id` is null.
Render output and labels as text, not executable HTML.

Retain the current capture and change locks.
Retain `PORTAL_WS_ENABLE_SHELL` for shells.
Do not hide the reason when an operation is locked.

Warning: Each shell command runs on every confirmed device and can change device state.

Require the preview phrase `RUN <target_count> TARGETS` and the stored confirmation snapshot for change and shell batches.
Keep the current Single Site device-name confirmation.
A changed command or target invalidates that confirmation.
The UI must not infer confirmation from a previous batch.
Keep raw commands and output out of browser diagnostic logs.
Capture the normalized device prompt before the first command.
After each command, require that same prompt and two seconds without output before collection continues.
Use a 30-second initial-output deadline and a 30-second deadline for each command.
Preserve partial output, mark the result unproven, and skip later commands when collection misses its deadline.

## 6. Acceptance Checks

- Verify unchanged Single Site repeatable selections at 1, 10, and 11 paths.
- Verify unchanged interactive shell input, resize, stop, and download.
- Verify keyboard tab navigation and independent form state.
- Verify multi-page discovery and stale-response rejection.
- Verify mixed success, failure, no-output, and cancellation outcomes.
- Verify no queued target starts after cancellation.
- Verify batch shells reject interactive terminal routes.
- Verify combined and grouped files preserve record identities.
- Verify traversal, unsafe labels, symlinks, and duplicate labels cannot escape the session root.
- Verify split-secret redaction in messages, files, errors, and logs.
- Verify disk failure, quota, expiry, deletion, and restart cleanup.

Use mocked SDK and transport fixtures for automated checks.
Use read-only commands only for separately approved live validation.
