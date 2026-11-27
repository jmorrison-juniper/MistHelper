# Data Model: Mist Identity Object Sign-In

The change adds no table, file, or cache key. It adds one field to a registry entry. The records below describe the in-memory values and the session state that the change reads. Row numbers name the evidence rows in research.md.

## MistEndpoint (registry entry)

- **Natural key**: `entity_type`, the key of the registry dictionary (types.py row 4).
- **Fields**: `entity_type`, `api_module`, `read_method`, `write_method`, `id_params`, `list_method`, and the new field `object_response`. The field defaults to false (row 5).
- **Entry `self_identity`**: `api_module` is `self.self`, `list_method` is `getSelf`, and `object_response` is true (row 4).

## ApiResult (service result)

- **Natural key**: none. The value exists only in memory.
- **Fields**: `status_code` (an integer) and `data` (a dictionary or a list of dictionaries).
- **Rule**: `success` is true for each status from 200 to 299 (endpoints.py row 2 holds the result construction).

## Identity object (Mist response)

- **Source**: the response `Admin` of the operation `getSelf` (row 33). The response refers to the `admin` schema (row 34). The schema defines the `privileges` property (row 35).
- **Natural key**: none in this change. The change reads the object and writes nothing.
- **Shape rule**: one non-empty dictionary becomes one identity record. A list keeps its records. Any other body yields no record (decision D-3).

## Identity record (list row)

- **Source**: one identity object for an object endpoint (decision D-1).
- **Consumer**: `_fetch_self` reads the first row (auth.py row 9).
- **Natural key**: none. The record exists for one call.

## Privileges (returned value)

- **Source**: `validate_token` returns the privileges type (auth.py row 10).
- **Empty value**: `MistPrivileges()`. The middleware and the login route treat the empty value as a rejected token (rows 11 and 15).

## Active SDK token (SDK session state)

- **Attributes**: `_apitoken` (a list of token strings) and `_apitoken_index` (an integer). The SDK sets both in `set_api_token` (row 83).
- **Valid state**: the index lies inside the list. The active token is the entry at the index.
- **Invalid state**: the index is minus one, the index lies outside the list, or the attribute has another type. The active-token check fails closed in each invalid state (decision D-4).

## Supplied token (input value)

- **Source**: the string that the caller passes to `validate_token`.
- **Normalization**: the string splits on commas, and each part loses its surrounding spaces. Empty parts drop out. The same split rule appears in `set_api_token` (row 83).
- **Membership**: the active token must equal one normalized part.

## Session record (existing store)

- **Creation**: the login route stores the supplied token and the privileges payload (row 17).
- **Freshness**: the record holds the privileges for 300 seconds (row 13).
- **Refresh**: the middleware calls Mist again after the freshness window ends, and it stores the result (row 12).

### State transitions

1. **Created**: sign-in succeeds with non-empty privileges. The record holds the privileges and the time of verification.
2. **Fresh**: a request within 300 seconds reads the stored privileges. The middleware makes no Mist call.
3. **Stale**: a request after 300 seconds calls Mist again.
4. **Refreshed**: the stored privileges change to the result of the new call. An empty result also replaces them. The middleware then rejects the request with HTTP 401 (rows 11 and 12).
5. **Empty but fresh**: the record holds empty privileges for the rest of the window. This state is analysis finding A-03, which a follow-up issue owns.

### Sign-in transitions

1. A valid supplied token with a 2xx identity and an active token that matches yields privileges. The login route creates the session record.
2. A 2xx identity with a mismatched active token yields empty privileges. The login route returns HTTP 401 and creates no record.
3. A 4xx response yields empty privileges and HTTP 401.
4. A 5xx response or a transport fault raises the unavailable error and returns HTTP 503.
