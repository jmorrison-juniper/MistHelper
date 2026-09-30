# Data Model: Spectrum RF Diagnostics

## Entity: RfDiagnosticRun

One operator attempt to run spectrum analysis or RF diagnostic recording.

**Fields**:

- `run_id`: Local identifier for one attempt. Use a timestamp-based value.
- `mode`: `spectrum` or `recording`.
- `site_id`: Mist site identifier used for API calls.
- `site_name`: Operator-facing site name when known.
- `target_type`: `ap` for spectrum or `client_mac` for recording.
- `target_value`: AP device identifier or client MAC.
- `started_at`: Run start time in ISO 8601 format.
- `finished_at`: Run finish time in ISO 8601 format.
- `status`: `success`, `cancelled`, or `failed`.
- `result_reference`: Session id, downloaded path, or empty value.
- `message`: Clear ASCII outcome message.

**Validation rules**:

- `mode` must be one of the allowed values.
- `status` must be one of the allowed values.
- `site_id`, `target_type`, and `started_at` are required.
- `result_reference` is required for a successful recording download.
- Messages must not include secrets, tokens, or raw credentials.

**Relationships**:

- A run can have one `SpectrumAnalysisSession` when `mode` is `spectrum`.
- A run can have one `RfDiagnosticRecording` when `mode` is `recording`.
- A successful recording run has one `RfDiagnosticFile`.

## Entity: SpectrumAnalysisSession

One AP spectrum scan at one site.

**Fields**:

- `site_id`: Mist site identifier.
- `device_id`: AP device identifier.
- `band`: Spectrum band used for the request.
- `duration`: Optional requested duration.
- `format`: Optional requested format.
- `session`: Session value from the start response.
- `started_time`: Running-state start time from Mist, when returned.
- `poll_count`: Number of running-state checks.
- `final_state`: `completed`, `running_timeout`, or `failed`.
- `failure_reason`: Failure text when one exists.

**Validation rules**:

- `site_id`, `device_id`, and `band` are required before start.
- Start request body includes `band` and may include `device_id`, `duration`, and `format`.
- Running-state request has no body.
- Polling must stop at the configured poll limit.

**State transitions**:

1. `prepared`
2. `confirmed`
3. `started`
4. `polling`
5. `completed` or `failed`

## Entity: RfDiagnosticRecording

One client RF diagnostic recording at one site.

**Fields**:

- `site_id`: Mist site identifier.
- `client_mac`: Normalized client MAC used for the API request.
- `name`: Recording name sent to Mist.
- `type`: Recording type sent to Mist.
- `duration`: Optional duration in seconds.
- `sdkclient_id`: Optional SDK client identifier.
- `rfdiag_id`: Recording identifier returned by Mist.
- `start_response`: Sanitized start response summary.
- `stop_response`: Sanitized stop response summary.
- `download_path`: Local path when download succeeds.
- `final_state`: `downloaded`, `stopped_no_download`, `stop_failed`, or `failed`.

**Validation rules**:

- `site_id`, `client_mac`, `name`, and `type` are required before start.
- Start request body includes `name` and `type`. It may include `duration`, `mac`, and `sdkclient_id`.
- Stop runs after start when the wait ends or Ctrl+C interrupts the wait.
- Download runs only after a stop attempt succeeds.

**State transitions**:

1. `prepared`
2. `confirmed`
3. `started`
4. `waiting`
5. `stopping`
6. `downloading`
7. `downloaded` or `failed`

## Entity: RfDiagnosticFile

One downloaded RF diagnostic recording file.

**Fields**:

- `directory`: Always `data/rfdiags/`.
- `file_name`: Safe name with site, client MAC, and run time.
- `path`: Full local path.
- `site_token`: File-system safe site token.
- `client_mac_token`: File-system safe MAC token.
- `run_time_token`: File-system safe timestamp token.
- `byte_count`: Number of bytes written.

**Validation rules**:

- The directory must be under `data/rfdiags/`.
- The file name must not contain path separators or traversal segments.
- Empty download bytes are a failure.
- The operation reports success only after bytes are written.

## Entity: WiringManifest

The deferred integration manifest at `specs/3570-spectrum-rfdiag/wiring.md`.

**Fields**:

- `menu_item`: Menu 290 entry.
- `registry_entry`: Operation registry entry.
- `endpoint_catalog_items`: Spectrum and RF diagnostic endpoint catalog updates.
- `changelog_fragment`: Release-note fragment to create during implementation.

**Validation rules**:

- The manifest must list menu, registry, endpoint catalog, and changelog work.
- The manifest must keep integration out of the planning-only step.
