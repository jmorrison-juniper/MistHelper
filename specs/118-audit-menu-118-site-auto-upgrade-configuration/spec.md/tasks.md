File: specs\\118-audit-menu-118-site-auto-upgrade-configuration\\tasks.md

Task breakdown and checklist for menu 118: Site Auto-Upgrade Configuration

Legend: Owner: (TBD), Est: hours, Priority: P0/P1/P2

Phase A: Design & API (P0)
1. API schema & OpenAPI stubs
   - Owner: Product/Backend
   - Est: 8h
   - Tasks: write request/response, example payloads, error codes. Acceptance: OpenAPI passes lint and review.

2. DB schema & migrations
   - Owner: Backend
   - Est: 12h
   - Tasks: create migrations for site_auto_upgrade_plans, site_auto_upgrade_waves, site_auto_upgrade_targets, site_auto_upgrade_events. Add indexes on plan_id, site_id, device_id, event_ts.
   - Acceptance: Migrations run locally and in CI, unit tests for models.

3. Input validation & dry-run resolver
   - Owner: Backend
   - Est: 12h
   - Tasks: implement validation logic, timezone checks, maintenance_window validation, target resolution for dry-run using device inventory mock.
   - Acceptance: Unit tests cover failure and success cases.

Phase B: Scheduler & Execution Engine (P0)
4. Scheduler integration
   - Owner: Backend/Platform
   - Est: 16h
   - Tasks: schedule job creation at plan creation (scheduled_start), respect maintenance windows, implement immediate execute endpoint.
   - Acceptance: Plans scheduled actually enqueue jobs at correct UTC times in test environment.

5. Wave runner & device job submission
   - Owner: Backend/Orchestration
   - Est: 40h
   - Tasks: implement algorithm to map devices to waves (deterministic), enforce concurrency caps, create device-level job objects/messages.
   - Acceptance: Simulated devices show correct order and concurrency; per-wave success/failure computation matches spec.

6. Event ingestion & status update
   - Owner: Backend
   - Est: 24h
   - Tasks: implement event API or queue consumer to accept device success/failure, update target and plan statuses, create audit events.
   - Acceptance: Events recorded in events table and plan transitions logged.

Phase C: Policies, Rollback & Notifications (P1)
7. Retry and rollback workflow
   - Owner: Backend
   - Est: 24h
   - Tasks: implement retry policy, backoff, and rollback initiation logic when thresholds exceeded.
   - Acceptance: Tests for retry metrics and rollback initiation on simulated failures.

8. Notifications (email/webhook/Slack)
   - Owner: Backend/Platform
   - Est: 8h
   - Tasks: hook notification_policy to notification service; test triggers on events.
   - Acceptance: Notifications are emitted on configured events in staging.

Phase D: Exporter & Audit (P1)
9. SQL/CSV exporter
   - Owner: Backend/Compliance
   - Est: 16h
   - Tasks: implement export endpoint to stream CSV or SQL INSERTs for plan + events + targets with anonymization option.
   - Acceptance: Exported SQL imports cleanly into Postgres and CSV column counts match.

Phase E: Testing & QA (P0)
10. Unit tests
    - Owner: QA/Backend
    - Est: 24h
    - Tasks: create unit tests for validation, wave mapping, edge cases.
    - Acceptance: Coverage target met for new modules (e.g., >80%).

11. Integration & E2E tests
    - Owner: QA
    - Est: 40h
    - Tasks: simulate device fleet, run plans with success/failure scenarios, run rollback tests, and verify metrics and notifications.
    - Acceptance: E2E tests pass reliably in CI; smoke tests for feature flag enabled.

12. Load & Performance tests
    - Owner: SRE/QA
    - Est: 24h
    - Tasks: drive N=10k simulated device targets and measure queue/backlog, concurrency enforcement.
    - Acceptance: System behaves within acceptable latency and no critical resource saturation.

Phase F: Documentation & Rollout (P2)
13. User docs & UI text
    - Owner: Product/Docs
    - Est: 8h
    - Tasks: write UI descriptions, help text, example policies.
    - Acceptance: Docs published in repo and linked from UI.

14. Runbook & monitoring docs
    - Owner: SRE
    - Est: 8h
    - Tasks: write runbook for failed plans, rollback steps, how to halt feature flag.
    - Acceptance: Runbook reviewed and stored in runbooks repo.

Acceptance & QA criteria for each task
- Unit and integration tests must exist for new logic.
- End-to-end flow must demonstrate correct plan lifecycle transitions for at least three scenarios: success path, partial failure with retry, and failure with rollback.
- SQL export must produce valid SQL importable into Postgres.

Notes on prioritization
- Implement core scheduling and safe dry-run first to prevent accidental mass upgrades.
- Stage risky features (auto_rollback) after initial dogfood period.

End of tasks.md

