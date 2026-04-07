# Task list (short IDs, dependencies)

- pc-001 — discover-api-signature
  - Description: Inspect PacketCaptureManager.start_org_packet_capture method, parameters, return schema, and error modes. Identify capture_id format and callback/polling mechanism.
  - Depends: none

- pc-002 — define-metadata-schema
  - Description: Produce a concise metadata schema (CSV/SQLite DDL and JSON schema) with fields: capture_id (PK UUID), org_id, site_id (nullable), start_time (ISO8601), end_time, filename_or_uri, size_bytes, filter, status, created_at
  - Depends: pc-001

- pc-003 — storage-retention-plan
  - Description: Document object-store path convention (org/{org_id}/captures/{capture_id}.pcap), retention policy, size limits, and access control requirements.
  - Depends: pc-002

- pc-004 — indexing-and-pk-strategy
  - Description: Update ENDPOINT_PRIMARY_KEY_STRATEGIES doc (proposal only) with natural_pk for org_packet_capture and recommended indexes (org_id, site_id, start_time).
  - Depends: pc-002

- pc-005 — error-and-retry-policy
  - Description: Define retry/backoff for transient failures, and transient vs permanent error classification for failed captures.
  - Depends: pc-001

- pc-006 — rate-limit-and-permissions-checks
  - Description: Define rate-limiting thresholds and permission checks to prevent accidental large-scale captures. Produce policy text for NOC.
  - Depends: pc-001, pc-003

- pc-007 — tests-plan-and-mocks
  - Description: Create unit & integration test plan and identify mocks needed (PacketCaptureManager, object store). List assertions and expected responses.
  - Depends: pc-002, pc-003

- pc-008 — docs-and-README-update
  - Description: Draft user-facing README / playbook snippet: how to request org captures, how to locate PCAPs, retention, and how to escalate failed captures.
  - Depends: pc-003

- pc-009 — verification-checklist
  - Description: Produce step-by-step manual verification checklist from the Verification plan for runbooks and QA.
  - Depends: pc-002, pc-003, pc-007

- pc-010 — implementation-pr-prepare
  - Description: Bundle artifacts, schema, tests descriptions, and tasks into a PR template ready for implementation work (coding tasks not to be executed yet).
  - Depends: pc-001, pc-002, pc-003, pc-007, pc-008

Each task should be converted into a GitHub issue with acceptance criteria, owner, estimate, and linked dependencies before implementation begins.