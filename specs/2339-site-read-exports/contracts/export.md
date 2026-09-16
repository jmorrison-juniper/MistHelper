## contracts/export.md

### C01: Menu and selection

1. Add one entry with description `Export a selected site dataset (20 read-only operations)`.
2. Use the next free numeric menu key after inspecting current `menu_actions`. The audited remote maximum is 243. Therefore 244 is provisional, not reserved.
3. Offer the twenty operationIds in manifest order. Do not dynamically enumerate every SDK method.
4. Use `InputUtils.safe_input` with `default_value=""` and an explicit context string.
5. Blank input, `q`, `0`, EOF, and Ctrl+C return a cancelled outcome. Require ASCII decimal digits for numbered choices. Invalid text and out-of-range integers return a clear message without a selected-endpoint request.
6. Resolve the organization before selecting the site. Read the cached organization again after selection and require it to match the request context.
7. Do not use the site name in the output path. It is untrusted display text.

### C02: SDK resolution and initial request

Import only `EndpointSpec.module_path` from the explicit catalog. Resolve `EndpointSpec.operation_id` from that module. Require a callable. Validate its signature against the supplied positional and keyword arguments in a contract test.

For a paginated entry, pass the runtime page limit and `page=1`. For a resolve-enabled entry, pass `resolve=True`. Do not add `limit`, `page`, `resolve`, `type`, or other options to a function that does not accept them.

Use the injected session. Pace each initial or continuation request. Reuse the configured session retry behavior. If it ultimately returns a failed response, do not retry independently.

### C03: Response and continuation

Require `status_code == 200` and a list of dictionaries for every accepted page. A 200 empty list is a valid empty dataset. A dictionary error body, `None`, string, or mixed scalar list is an error, even with status 200.

After a page passes validation, inspect `response.next`. A false or empty continuation ends the fetch. A nonempty continuation must be a relative URL with no authority, credentials, or fragment. Its parsed path must equal the selected endpoint path after site substitution. Do not construct a cursor or print its query string.

Track previously seen continuations. Reject repetition before the next network call. Use `mistapi.get_next` with the same session. If a declared continuation returns `None`, report an error. Stop at 1,000 pages or 1,000,000 total rows. A bound breach discards the pending export.

No writer may run until the entire fetch passes. Do not use `mistapi.get_all`, because its current implementation does not enforce this contract. Do not copy `APIDataFetcher` partial-save recovery.

### C04: Record validation and scope

Reject rows with missing, null, blank, boolean, container-valued, or redacted business-key components. Require every field listed in the endpoint's existing `primary_key` strategy. Never substitute an index, a random UUID, a body hash, or `name` for a missing key.

Copy records before enrichment. Set `org_id` and `site_id` from the selected request. Reject a nonempty conflicting `org_id`. For an inherited record with a different original `site_id`, preserve that value as `source_site_id` before setting the selected site. Reject a collision with an already different `source_site_id`. This distinction keeps the source entity and the selected export scope visible.

For a nonderived endpoint, a nonempty conflicting `site_id` is an error. Do not silently relabel another site's data.

Preserve upstream `id`, `mac`, `map_id`, nested values, and list order. Do not manufacture a timestamp for snapshot statistics. Reject every duplicate business-key tuple within one complete fetch, including identical duplicate rows. Report the duplicate count and write nothing. This fixed policy prevents silent collapse and pagination overlap.

### C05: Credential boundary

Use `CredentialRedactor.redact_records` before flattening or writing. Add explicit coverage for nested `secret`, `password`, `psk`, `token`, `private_key`, `ssh_keys`, `keywrap_kek`, `keywrap_mack`, and `magic`. Extend the canonical redactor's exact-key set for the last three names. Do not create a second weaker redactor.

Use only the redacted raw copy as `ExportBackendOptions(raw_data=...)`. The CSV/SQLite argument is a flattened form of that same copy. Do not pass the original response list to any writer or log.

Never log raw exceptions from the SDK. Log the operation, stage, exception class, and full traceback frame locations without source lines or local values. Log HTTP status separately when present. This retains diagnostic context without echoing credentials from exception text.

### C06: Primary output and mirrors

Generate a bare filename: `SiteRead_` + operationId + `_` + canonical site UUID with hyphens removed + `.csv`. The catalog operationId and canonical UUID are the only variable parts.

Call `DataProcessingUtils.flatten_nested_fields` on safe raw records. Call the canonical writer with the flattened rows, basename, exact operationId, and `ExportBackendOptions(raw_data=safe_raw_rows)`.

`DataExporter` already escapes multiline values and places bare CSV names under `data/`. Do not hand it an absolute path or a caller-supplied directory. SQLite derives a per-site table from the same basename.

If the writer returns false, return an error and do not log export success. If it returns true, report primary output saved. Preserve database-drop warnings. Cross-backend writes are not a distributed transaction.

### C07: Scoped storage keys

Add `storage_key_fields` to each selected strategy. Its value is `["site_id", *primary_key]`, without duplicate fields. Keep the existing `type`, `primary_key`, indexes, and routing unchanged.

Add `src/db/storage_keys.py:StorageKeyEncoder`. It owns the deterministic encoding of the ordered business-key values. Use compact UTF-8 JSON of the value list, URL-safe Base64 without padding, and the prefix `v1_`. Reject missing components and an encoded Arango key over 254 characters. Do not truncate. This is an encoding of natural business identity, not a new API identifier.

In `ArangoDBWriter._prepare_document`, use the encoder only when `storage_key_fields` exists. Otherwise preserve the current `_compute_key` path unchanged. Do not globally repair every old composite strategy in this feature.

In `RedisJSONWriter.write`, select the opt-in fields and carry the scoped-key flag through its batch helpers. For opted-in records, append the encoded key after the operationId namespace. For all other records, preserve the existing key exactly. Keep helper parameter counts at five or fewer.

SQLite remains on its native keys inside a per-site table. The endpoint document collection is the authoritative site-specific record in ArangoDB. Existing graph vertices still identify shared entities. Do not change global graph vertex IDs or promise that a shared graph vertex stores every site's effective configuration.

### C08: Existing data and rollback

Before enabling the new key mode on a deployment with existing endpoint collections, inspect counts through an authorized read-only process. These endpoints lack application integration, but an operator might have imported records manually.

If matching collections already contain records, stop for a separate reviewed migration plan. Do not delete, rewrite, clear, or silently duplicate those records. Tests use new temporary stores only. A code rollback must never delete data.

### C09: Import and compatibility boundary

The new package has no API calls, file writes, environment loading, global router construction, or `MistHelper` imports at import time. Resolve SDK modules only when executing or explicitly checking the catalog.

The menu composition point may import the new classes with private names. Do not add them to the existing `MistHelper.__all__` contract. The existing `menu_actions` API remains the integration point.
