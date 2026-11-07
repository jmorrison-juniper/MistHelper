# Metadata Lookup Contract

`OrgConfigMigrationManager._get_org_name()` returns a string.
It calls `mistapi.api.v1.orgs.orgs.getOrg` once with the stored session and organization identifier.
It checks status before it accesses response data.

Successful, valid metadata returns the exact name.
Unsuccessful or invalid results return `Unknown`.
Refusal warnings identify the organization and HTTP status.
Missing or invalid statuses use the fixed text `unavailable`.
Request failures identify the exception type, without exception text or traceback.

Manager logs must not contain response bodies, returned names, headers, or exception messages.
The Mist API SDK can print refused response data through its direct console when SDK debug output is enabled.
This contract does not disable that process-wide SDK output.
The typed import confirmation and all configuration writes remain outside this repair.
