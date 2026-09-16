## data-model.md

The names below are proposed new symbols. They do not exist yet. Existing symbols have their verified source paths in `plan.md`.

### EndpointSpec

Create a frozen, slotted dataclass in `src/export/site_read/models.py` with exactly five fields:

1. `operation_id: str`. Use the exact packet operationId.
2. `module_path: str`. Use the verified dotted SDK module.
3. `api_path: str`. Use the packet path template containing `{site_id}`.
4. `paginated: bool`. This controls whether the initial call receives `limit` and `page`. It does not permit ignoring a returned continuation.
5. `default_kwargs: tuple[tuple[str, str | int | bool], ...]`. Use `(("resolve", True),)` for the six resolve-enabled entries. Use an empty tuple otherwise.

The catalog holds twenty immutable entries. The primary-key strategy remains the single source for business-key fields. Do not duplicate that configuration in the dataclass.

### SiteReadRuntime

Create a frozen, slotted dataclass with five dependencies:

1. `session`. The already configured `mistapi.APISession`.
2. `select_site`. The existing zero-argument callable that returns a site identifier or an empty result.
3. `resolve_org`. The existing zero-argument organization resolver.
4. `pace`. A zero-argument callable from `AdaptivePacer(...).pace`.
5. `page_limit: int`. The existing configured API page limit, validated as a nonboolean integer from 1 through 1,000.

Use typed `Callable` declarations. A test injects fakes. A new exporter must not locate these dependencies by importing `MistHelper`.

### SiteReadRequest

Use three fields: `endpoint: EndpointSpec`, `org_id: str`, and `site_id: str`. Canonicalize selected UUIDs with `uuid.UUID` before constructing a request. Keep API entity identifiers unchanged.

### SiteReadOutcome

Use four fields: `status`, `operation_id`, `record_count`, and `output_name`.

`status` is one of `cancelled`, `empty`, `saved`, or `error`. A saved outcome means that the configured primary writer returned true. It does not certify every database mirror. Empty, cancelled, and error outcomes have zero saved records.

### SiteReadError

Use a feature-owned exception with a safe error code and operation context. Do not put raw payloads, exception messages, or continuation URLs into its user-facing text.
