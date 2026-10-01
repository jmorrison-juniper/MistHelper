# Contract: Cradlepoint status export

## Operation

Menu `245` calls `testOrgCradlepointConnection` once for the selected organization.
The endpoint remains `GET /api/v1/orgs/{org_id}/setting/cradlepoint/setup`.
No regional host, token, prompt, or request argument changes.

## Refusal

Before any body processing, validate the native `status_code`.
For a valid non-success status, raise a failure with this bounded content:

```text
testOrgCradlepointConnection failed: HTTP <status> (checked 1 response).
```

For an absent or unusable status, use this named failure:

```text
testOrgCradlepointConnection failed: transport status is unavailable (checked 1 response).
```

The existing menu boundary includes that failure in its error and operator notice.
The boundary constructs no row and invokes no persistence or writer callback.
It emits neither `! No Cradlepoint connection status found` nor a successful export notice.

## Success

An integer HTTP status from `200` through `299` permits existing body handling.
Valid HTTP `200` integration status rows and empty-body behavior remain unchanged.
An integration `error` value does not determine HTTP success.

## Diagnostic privacy

New product diagnostics must contain no response body, header values, cookies,
tokens, URL credentials, or configuration credentials.
SDK diagnostics remain outside this bounded product change.
