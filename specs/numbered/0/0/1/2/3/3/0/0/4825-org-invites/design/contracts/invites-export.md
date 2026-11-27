# Contract: Organization Invites Export

## Scope

This contract covers `OrgExportUtils._invites` in `src/operations/exporting/export/org_export_utils.py`, lines 717 to 735 on GitHub main. The method is a static method. It takes no argument and returns `None`. The contract covers the supported path, the absent path, and the logging rules of the follow-up change.

## Lookup

The method reads one attribute, `listOrgInvites`, from `mistapi.api.v1.orgs.invites`. A missing attribute gives `None`. No other name is read.

## Supported path

Condition: the attribute is a callable.

The method calls the shared export with these arguments:

- `api_call` is the callable.
- `data_type` is `"invites"`.
- `sort_key` is `"email"`.

The shared export builds the file name `OrgInvites.csv` from `data_type`. It writes the file through its existing path.

## Absent path

Condition: the attribute is missing.

The method meets this contract:

- It writes exactly one ERROR record. The text starts with "Skipped the organization invites export." It names `listOrgInvites` and `OrgInvites.csv`.
- It writes no file.
- It raises no exception.
- It calls no Mist API endpoint.
- It does not call the shared export.

## Logging rules after the follow-up change

- Before the shared export call, the method writes one INFO record. The record names the organization invites export.
- After the call returns, the method writes one DEBUG record. The record reports that the call returned.
- Each record uses `%s` style values. A record holds no token, password, or invite content.
- All log text uses ASCII characters only.

## Outside the contract

- No substitute function. The method never reads another mistapi name.
- No raw HTTP request.
- No new output column. The columns of `OrgInvites.csv` come from the response rows of the supported function, and this contract does not change them.
