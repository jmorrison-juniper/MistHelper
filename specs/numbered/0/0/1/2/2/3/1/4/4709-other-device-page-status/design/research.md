# Pagination research

## Decision

Use the existing SDK `get_next` helper and inspect each returned `APIResponse` before collecting rows.
Retain a local all-or-nothing aggregate and the sanitized external-call fallback from #1794.

## Evidence

Installed mistapi 0.64.1 exposes `status_code`, `data`, and `next` on each `APIResponse`.
`get_next` delegates to the existing session `mist_get`.
`get_all` does not inspect status. It can discard error dictionaries or merge them into list results.

Shared `src/mist/access/api/api_fetch_utils.py`, `api_core_fetch_utils.py`, and `api_data_fetcher.py` call `get_all`.
They do not expose per-page status validation.
`src/operations/exporting/export/wifi_clients_exporter.py` uses a local `get_next` loop and validates statuses.
Its partial-result policy and domain-specific methods cannot serve this all-or-nothing event export unchanged.

`src/operations/exporting/export/http_response_status.py` logs the response URL and permits missing statuses.
It cannot meet this operation's strict completeness and private-response requirements without changing a shared contract.
`ResponseIntegrityChecker` detects some malformed bodies, but not a blank body.
Requiring a list or a list-valued `results` field rejects malformed pages without a new shared contract.

## Alternatives considered

- Check only the first response: rejected because a later page can fail.
- Validate after `get_all`: rejected because the aggregate has lost later-page statuses.
- Add a session adapter: rejected because it adds indirection and changes the SDK call boundary.
- Modify shared helpers: rejected because the reserved file set does not include them.

## Preservation

The session artifact folder holds `issue-1794-preserved.patch`, `issue-1794-preserved-exporter.py`,
`issue-1794-preserved-tests.py`, and `issue-1794-preserved-sha256.txt`.
The original commit remains an ancestor of this repair.
