# Data Model: Dynamic JVD Labs

All timestamps use UTC ISO 8601. Every record uses a natural key, not an artificial counter.

| Entity | Key | Main fields | Notes |
| - | - | - | - |
| Template | `template_id` + `version` | schema_version, catalog_version, source (`catalog` or `import`), content_digest | Immutable once saved. |
| Draft | `draft_id` | template key, parameters, plan_digest, owner_pseudonym, state | Immutable snapshot. Cancel adds a state record. |
| Plan | `plan_digest` | topology, resource_budget, provenance, engine_revision | Deterministic output. Grants no authority. |
| Approval | `approval_id` | action, plan_digest, target, backend_identity, engine_revision, lease, budget, owner_proof, expires_at | Browser-bound. Revocable. |
| Job | `job_id` | approval_id, operation, state, request_key, progress, evidence_refs | State set: `queued`, `running`, `succeeded`, `failed`, `recovery-required`, `cancelled`. |
| LabRun | `run_id` | plan_digest, resources, ownership_records, lease, last_evidence_at | Observed resources only. |
| Ownership record | `run_id` + `resource_id` | resource_type, created_by_job, verified_at | Cleanup needs a fresh check. |
| Evidence | `evidence_id` | job_id, kind, redacted_payload, collected_at | Never holds a token or bootstrap. |
| Capability | `capability_id` | state, reason, engine_revision | States: `available`, `unavailable`, `unverified`. |

## Invariants

- A Plan digest covers the full intent, so any change creates a new digest.
- An Approval is valid only for the exact digest, target, backend identity, engine revision, lease, and budget.
- A Job persists intent and `request_key` before the first remote write.
- An uncertain write sets `recovery-required` and never repeats automatically.
- Foreign private records return the same 404 as a missing record.
- Secrets never enter any record. Records hold references only.
