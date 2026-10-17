# Data Model: MistDSW Preparation

## Store Input

Fields: site name, source IPv4 base, normalized `/22`, row number, four optional VLAN gateways, optional management gateway, and optional WAN gateway.
Site names must be nonblank, unique within a run, and at most 128 characters.
Reject control characters and spreadsheet formula prefixes after leading whitespace.
Accept IPv4 only. Normalize a host address into its `/22` and require acknowledgment.
Each VLAN gateway must be a usable address in its calculated `/24`.
Management uses `/27`; WAN uses `/29`.
Their supplied gateways must be usable addresses in those networks.
Reject overlapping store supernets in a batch.

## Addressing Profile

Fields: schema version, profile key, revision, approval reference, four variable network definitions, six static network definitions, service definitions, DNS servers, and policy mapping.
An approved profile has exactly ten unique network names and four services.
VLANs are unique integers from 1 through 4094.
The profile must resolve the three B2 conflicts explicitly.
Subnets, gateways, DHCP ranges, and template definitions must agree.
The operator supplies the profile. No customer profile is committed or embedded.
Only approved, nonsecret profile content can appear in a run record.
Approval evidence identifies the network owner and the exact revision.

## Preparation Run

Fields: run UUID, owner session key digest, workflow, profile key and revision, input digest, idempotency token, state, creation time, expiration time, findings, and artifact manifest.
All timestamps use UTC ISO 8601.
The UUID is the natural identity of the submitted run, not an auto-increment export row.
ArangoDB `_key` uses that identity within `mistdsw_preparation_runs`.
Use the existing configured ArangoDB database.
Do not retain raw exports, credentials, store addresses, or full payloads in run metadata.
Persist counts, digests, safe error codes, and artifact locations relative to the managed data root.
Reject the run if the shared database is unavailable.

States:

1. `received`: Ownership and input-size checks succeeded.
2. `invalid`: Input validation failed. No ready artifacts exist.
3. `review`: Validation succeeded. Required acknowledgments remain.
4. `ready`: Review and all verified artifact writes succeeded.
5. `failed`: Generation, verification, or persistence failed. Downloads remain disabled.

Expired records retain their safe audit metadata but cannot serve files.
Store expiration as a timestamp, not a sixth transient run state.
Physical private files expire after 24 hours.
Interrupted writes cannot transition to `ready`.
Reuse an idempotency token only for the same owner, workflow, profile revision, and input digest.
A conflicting reuse returns an explicit conflict.

## Artifact

Fields: run identity, artifact kind, relative path, media type, byte count, SHA-256 digest, schema version, and verified status.
Private artifacts reside under `data/mistdsw/<run_id>/`.
Never accept an output path from a browser.
CLI destinations must remain under the configured data root.
Artifact names are application-controlled.
Ready downloads require ownership, unexpired run state, and matching content verification.
Existing destinations are rejected by default.
An explicit replacement requires a verified backup and atomic replacement.

## Validation Finding

Fields: safe error code, field or row location, severity, correction text, and acknowledgment requirement.
Messages do not include raw credentials or template bodies.
Warnings include address normalization and intentional template differences.
Errors include unknown placeholders, invalid profiles, unsafe secrets, and ambiguous LAN selection.
Record total examined rows and total findings.
An unreadable input produces a failure, not a zero-count success.
