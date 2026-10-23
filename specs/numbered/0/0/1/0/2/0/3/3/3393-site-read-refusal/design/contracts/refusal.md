# Contract: Site read refusal

The affected endpoints are:

- `POST /api/org-upgrades/options`
- `GET /upgrade/org/options`
- `GET /upgrade/org/confirm`

When the selected-site read raises `RequestException`, each endpoint returns status 503 and this JSON envelope:

```json
{"error":{"code":"org_upgrade_site_read_failed","message":"The Mist cloud site read failed. Try again."}}
```

The response contains no transport exception text or submitted option value.
The save creates no plan, nonce, or saved options.
An earlier plan and its saved options remain unchanged.
The browser stays on the options form, restores its controls, and retains its entered values.
Missing-site and invalid-option responses remain unchanged.
