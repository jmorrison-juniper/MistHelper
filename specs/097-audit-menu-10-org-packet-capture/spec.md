# Org Packet Capture: Specification

## Summary

Org Packet Capture: an org-scoped workflow to start, track, and store packet captures across sites using PacketCaptureManager.start_org_packet_capture. Produces PCAP artifacts (binary) and minimal indexed metadata for search, audit, and downstream analysis.

## Purpose

Allow NOC engineers to trigger organization-level packet captures, persist capture artifacts in durable object storage, and index lightweight metadata in the MistHelper outputs for discovery and auditing.

## Stakeholders

- NOC Engineers (primary users)
- Platform/Infra (object storage + retention)
- Security/Compliance (audit trail)
- Developer(s) maintaining MistHelper

## Acceptance Criteria

Pass conditions:
- Calling PacketCaptureManager.start_org_packet_capture triggers capture at target sites and returns capture identifiers and status.
- Capture PCAPs are stored in a durable object store (S3/Podman volume/Share) with predictable pathing.
- Minimal metadata for every capture is recorded in MistHelper outputs (CSV/SQLite) with fields: capture_id, org_id, site_id (nullable), start_time, end_time (when available), filename/URI, size_bytes, filter, status.
- Permission checks and basic rate-limiting are enforced.

Fail conditions:
- Failed capture requests are not surfaced with reason and identifier.
- PCAP files are stored only transiently and not discoverable via metadata.

## API function(s) used

- PacketCaptureManager.start_org_packet_capture (primary)
- Optional: lower-level site capture APIs if needed by manager

## SQL export relevance & recommendation

sql_export_relevant: false — large binary PCAPs should NOT be exported into SQL. Recommendation: record only minimal metadata rows in SQLite/CSV for discovery and audit (capture_id UUID, org_id, site_id, start_time, end_time, filename_or_uri, size_bytes, filter, status). Store full PCAPs in object storage and reference them by URI in the DB.

## Primary key strategy suggestion

- Entity: org_packet_capture
- PK type: natural_pk
- Primary key: [capture_id] (UUID provided by manager)
- Indexes: org_id, site_id, start_time

## Risks & Assumptions

- Assumes PacketCaptureManager returns/accepts stable capture_id UUIDs.
- Assumes availability of object store or accessible filesystem for large files and retention policy.
- Risk: large capture volumes could exhaust storage or bandwidth — require retention and size limits.
- Assumes proper permissions to start org-scoped captures. If not, capture calls will fail with auth errors.
- Assumes capture filtering syntax stability across devices/sites.