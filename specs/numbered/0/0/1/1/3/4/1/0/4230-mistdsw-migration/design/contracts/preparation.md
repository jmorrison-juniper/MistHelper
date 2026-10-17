# Preparation Interface Contract

## CLI

Proposed interface: `MistHelper.py --prepare-mistdsw <workflow>`.
Workflows are `variables`, `switch`, `gateway`, and `networks`.
This is a planned interface, not an available command.
All workflows require an explicit approved profile.
Variables accept `--site` with `--base`, or `--input` for TSV.
Optional `--netmgmt` and `--wan1` values apply to single-store input.
Template workflows require `--input` JSON.
All workflows require `--output` within the configured data root.
Exit 0 means that all artifacts are verified and their manifest is ready.
Invalid input exits 2. Storage or generation failure exits 1.
Never print raw CSV values, template bodies, secrets, or embedded organization identifiers.
Print examined counts, safe findings, and the manifest location.
If interactive review is required, use `InputUtils.safe_input`.
EOF and interruption leave the run unavailable for download.
Unattended use requires explicit acknowledgment options for normalization and reviewed template changes.

## TSV Input

Accept comments beginning with `#` and blank lines.
Accept these row shapes only:

| Shape | Fields | Site naming |
| --- | --- | --- |
| Base only | One IPv4 base | `Store_` plus base with underscores. |
| Base with VLAN gateways | Base and exactly four gateways | Same generated name. |
| Named store | Site and base | Supplied name. |
| Named store with optional gateways | Site, base, management, WAN | Supplied name. Three fields permit management only. |

Preserve an empty management column when WAN is supplied alone.
Reject malformed, missing, extra, or partial gateway fields with line numbers.
Reject the entire batch if any row fails.
The parser reads at most 5 MiB and 500 stores.
Use UTF-8. Preserve input site order.

## Portal

Add one preparation page under `/mistdsw` in the existing port-8055 portal.
Use the current layout, theme, and navigation.
Do not claim that a source UI exists.

| Proposed route | Result |
| --- | --- |
| `GET /mistdsw` | Workflow form and preparation-only warning. |
| `POST /mistdsw/runs` | CSRF-protected validation and owned run creation. |
| `GET /mistdsw/runs/<run_id>` | Owned preview, findings, and reviewed difference summary. |
| `POST /mistdsw/runs/<run_id>/review` | CSRF-protected acknowledgments and artifact generation. |
| `GET /mistdsw/runs/<run_id>/artifacts/<kind>` | Owned, verified private download. |

Return 400 for malformed requests, 413 for size limits, and 422 for field validation errors.
Return 409 for review or idempotency conflicts.
Return 404 for missing or unowned runs without revealing ownership.
Return 410 for an owned expired artifact.
Return 503 for unavailable shared storage.
A failed request must not expose a download link.

Use existing CSRF and session middleware.
B3 requires authorization evidence before private uploads are enabled.
Generate a cryptographically random session owner key within the existing signed session.
The browser must not select or replace its stored ownership digest.
An expired or lost session cannot recover another session's artifacts.
Do not add a feature login service.
If the existing session boundary cannot meet B3, require a separate approved portal-identity change.

Interactive controls need stable `data-testid` values, labels, keyboard access, and visible validation messages.
Planned selectors include `mistdsw-workflow`, `mistdsw-input`, `mistdsw-profile`, `mistdsw-preview`, and `mistdsw-download`.
Record failed browser flows as traces or screenshots under the existing CI artifact policy.

## Private Artifacts and Failure

Apply restrictive account-level permissions. Never make files writable or readable by all accounts.
Use managed temporary files, verify content, then replace atomically.
A failure removes only feature-owned temporary files and leaves an explicit failed run.
Log info before transformations, file operations, and persistence.
Log debug after success with counts and status.
Log contextual errors after failure without input bodies.
Prevent path traversal, symlinks outside the managed root, and cacheable public downloads.
Use private no-store responses and attachment filenames controlled by the application.

Warning: manual deployment changes the Mist organization and can disrupt production networks.
The page provides preparation only. It has no apply, POST-to-Mist, or device-command control.
