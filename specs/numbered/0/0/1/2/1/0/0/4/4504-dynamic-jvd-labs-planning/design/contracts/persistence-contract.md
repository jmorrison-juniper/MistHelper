# Persistence Contract

Backend: the existing ArangoDB, through host-owned repositories. Redis is a cache only. No SQLite journal exists in the integrated build. The generic ingestion router is not used because it can degrade to CSV-only success.

| Collection (proposed) | Holds | Key |
| - | - | - |
| `labs_templates` | Imported templates | `template_id` + `version` |
| `labs_drafts` | Immutable draft snapshots | `draft_id` |
| `labs_approvals` | Approvals and revocations | `approval_id` |
| `labs_jobs` | Jobs and state transitions | `job_id` |
| `labs_runs` | Lab runs and ownership records | `run_id` |

Rules:

1. Write intent and the request key in one transaction before the first remote write.
2. Use verified unique indexes. Unique keys alone do not serialize overlapping address ranges, so admission needs an explicit lock or a guarded transaction (T023).
3. Receipts are immutable. A state change appends a record.
4. An unavailable backend returns an explicit error and never a partial success.
5. Exclude private records from generic data downloads.
6. Define backup, restore, retention, schema migration, and compatible rollback (T024). Do not import standalone framework records.
7. Live locks need POSIX unless decision D-03 approves a cross-platform lock.
