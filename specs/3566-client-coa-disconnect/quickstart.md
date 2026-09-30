# Quickstart: Client CoA Disconnect

This guide validates the plan without sending destructive Mist requests.
Implementation must add the commands when code exists.

## Prerequisites

1. Bootstrap the worktree virtual environment.
2. Activate `.venv`.
3. Confirm that `mistapi` reports version `Version: 0.64.0`.
4. Do not run a live destructive request during automated tests.

## Validate SDK support

Run this check in the feature worktree:

```powershell
.\.venv\Scripts\python.exe -m pip show mistapi
```

Expected result:

```text
Version: 0.64.0
```

The implementation test setup must import these functions:

- `mistapi.api.v1.sites.clients.reauthSiteDot1xWirelessClient`
- `mistapi.api.v1.sites.wired_clients.reauthSiteDot1xWiredClient`
- `mistapi.api.v1.sites.clients.disconnectSiteWirelessClient`
- `mistapi.api.v1.sites.clients.unauthorizeSiteWirelessClient`
- `mistapi.api.v1.sites.rogues.deauthSiteWirelessClientsConnectedToARogue`

## Unit validation scenarios

Run the unit package after implementation:

```powershell
python -m pytest tests\unit\device\client_session_control
```

Expected results:

1. Colon separated input normalizes to lowercase colon-free form.
2. Hyphen separated input normalizes to lowercase colon-free form.
3. Dotted input normalizes to lowercase colon-free form.
4. Invalid input stops before confirmation.
5. Confirmation mismatch sends no Mist request.
6. `--dry-run` sends no Mist request.
7. Each attempt writes one CSV log row.
8. The destructive menu category stays excluded from automated safe tests.

## Dry run operator validation

Use this flow after menu 286 is wired:

```powershell
python MistHelper.py --menu 286 --dry-run
```

Expected result:

- The operation asks for a site.
- The operation asks for one action.
- The operation asks for a client MAC or rogue BSSID.
- The operation shows the normalized target.
- The operation asks for exact confirmation.
- The operation prints the Mist request that it would send.
- The operation sends no Mist request.
- The operation writes one `dry_run` row to `data/ClientSessionControlLog.csv`.

## Live validation guard

Run a live request only with an approved test site and approved test client.
Stop if the site, action, or target is not approved.

Expected result for a confirmed live request:

- The operation sends exactly one Mist request.
- The operation reports success or Mist failure.
- The operation writes exactly one CSV row.

## References

- Data model: `specs/3566-client-coa-disconnect/data-model.md`
- Contract: `specs/3566-client-coa-disconnect/contracts/client-session-control.md`
- Wiring manifest: `specs/3566-client-coa-disconnect/wiring.md`

