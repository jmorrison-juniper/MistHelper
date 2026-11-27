# Data Model: Ship the preserved admission scope work

The change adds no database table, no schema, and no product output file. It changes the in-process state and the Redis keys that the shared admission ledger writes. This model names each state, its natural key, and its transitions.

## Entities

### Organization scope

- **Natural key**: The organization identifier, a non-empty string.
- **Storage**: A context variable named `misthelper_scoped_organization`. The branch defines it at `src/interfaces/wan_performance/collection/request_admission.py:22-25`. The ship design moves it into `OrganizationScope` as a class attribute.
- **Lifetime**: One block. The block saves the previous value as a token. The `finally` clause resets the variable from that token.
- **Rule**: Only the site request path reads this value (`request_admission.py:139` on the branch).

State transitions:

| From | Event | To | Rule |
|------|-------|----|------|
| unset | Block enters with a non-empty identifier | active with that identifier | FR-004 |
| unset | Block enters with an empty identifier | unset | `ValueError` is raised before the value changes (FR-008) |
| active (outer) | Nested block enters | active (inner) | The inner identifier is active. |
| active (inner) | Nested block exits | active (outer) | The token restores the outer value (FR-007). |
| active (any) | Block exits normally or by exception | the previous value | The `finally` clause resets the variable (FR-006). |

### Shared admission key

- **Natural keys**: The credential fingerprint for the key `misthelper:api:v1:requests:{fingerprint}`. The organization identifier for the key `misthelper:api:v1:org:{org_id}`.
- **Storage**: Redis sorted sets. The Lua script `RequestLedger.SCRIPT` writes them (`request_admission.py:25-35` on main).
- **Members and scores**: Each member is a random token. Each score is the request time in seconds.
- **Window**: The script removes members that are older than 3600 seconds. The key expires after 3601 seconds (`request_admission.py:28-33` on main).
- **Limit**: The script refuses a request when a key holds the class attribute `LIMIT`, which is 5000 members.
- **Failure rule**: When Redis raises a `RedisError`, the ledger sets `available` to false and admits later requests without a reservation (`request_admission.py:91-97` on main).

### Credential fingerprint

- **Natural key**: The fingerprint string.
- **Derivation**: The SHA-256 hex digest of the value of the `Authorization` header, or of the `Cookie` header when no `Authorization` header exists (`request_admission.py:78-81` on main).
- **Storage**: Only in the shared admission key. The fingerprint never appears in a log line, in a rendered traceback, or in the record.
- **Failure rule**: A request with neither header is refused with the message "Shared API admission requires configured authentication." (`request_admission.py:78-80` on main).

### SDK error line filter

- **Natural key**: The filter instance. One instance exists for each MSP call.
- **Attachment point**: The logger object returned by `logging.getLogger("mistapi")` (`.venv\Lib\site-packages\mistapi\__logger.py:218`).
- **Transitions**: Detached, then attached when `SdkErrorLineMute.muted()` enters, then detached when the block exits. The detach runs in a `finally` clause (FR-017).
- **Effect**: The filter drops each record at level ERROR or higher that the logger object emits during the block. Records from other loggers pass unchanged.

### MSP organization list outcome

- **Natural key**: The MSP identifier `msp_id`.
- **Source**: The response of `listMspOrgs` (`.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py:17`).

| Status | Outcome | Warning line | Failure row |
|--------|---------|--------------|-------------|
| 200 | Organization rows, with continuation pages | None | None |
| 0 (transport sentinel) | Failure row | None. The client logs its own error line in `_request_with_retry`. | Error text `HTTP 0` (observation O-6) |
| 403 | Failure row | One warning that names HTTP 403 (FR-015) | Error text `HTTP 403` |
| Any other status | Failure row | One warning that names the status (FR-015) | Error text with the status |

### Ledger availability

- **Natural key**: The ledger instance, which lives for the process.
- **Transitions**: Available, then unavailable after the first `RedisError`. The unavailable state stays for the rest of the process (`request_admission.py:91-92` on main).

## Observation

- **O-6**: For a transport failure, the failure row reads `HTTP 0`. The expression that builds the error text (`client.py`, `_discover_msp`) returns that text for every status that is not None, and the transport sentinel is 0. The change does not alter that expression. Record for the owner as UR-7 in `analysis.md`.
