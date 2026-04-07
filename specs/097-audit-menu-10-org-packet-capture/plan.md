# High-level approach

1. Discovery: inspect PacketCaptureManager.start_org_packet_capture signature, inputs, outputs, and error modes.
2. Data model: design minimal metadata model for SQL indexing (capture_id, org_id, site_id, start_time, end_time, filename_or_uri, size_bytes, filter, status).
3. Storage plan: define object-store path template (e.g., org/{org_id}/captures/{capture_id}.pcap) and retention policy.
4. Integration: plan call flow — trigger capture, poll/subscribe for completion, persist metadata, store file URI.
5. Controls: add rate limiting, size caps, permission checks, and logging.

Stop before IMPLEMENT: this plan produces design and tasks only; do not modify code or run deployments.

# Deliverables

- This specification (spec_md) and implementation plan
- Metadata schema (DDL / JSON schema) and indexing recommendations
- Storage path and retention policy document
- Task breakdown for implementation, tests, and docs
- Verification checklist (manual + automated tests to add)

# Milestones

1. M1 — API & signature discovery, produce metadata schema (1–2 days)
2. M2 — Storage & retention design + index strategy (1 day)
3. M3 — Tests plan and CI hooks (1 day)
4. M4 — Implementation sprint (not included here) — follow the tasks list

# People / Roles

- Single engineer (owner): responsible for design, tests, and coordinating infra for object storage.
- Optional reviewers: Security/Compliance, Platform.

# Verification plan

Manual checks:
- Trigger a capture via manager in a dev/org sandbox; verify capture_id returned and progress status.
- Confirm PCAP file landing in object store path and accessibility.
- Verify metadata row appears in SQLite/CSV with correct fields and URI reference.

Automated tests to add (later):
- Unit: simulate PacketCaptureManager responses (success/fail) and assert metadata extraction.
- Integration: mock object storage and ensure file URI persistence and size recorded.
- Regression: permission and rate-limit behavior.

Note: STOP before implementation — create artifacts and task list for the next (implementation) phase.