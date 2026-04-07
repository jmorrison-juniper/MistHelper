File: specs\\118-audit-menu-118-site-auto-upgrade-configuration\\plan.md

Implementation Plan: Site Auto-Upgrade Configuration (menu 118)

Summary
- Deliver feature in 3 major milestones: Design & API + DB schema, Core Execution Engine & Scheduler Integration, Staged Rollouts + Exports + Tests.
- Estimated total effort: 4-6 sprints depending on team size (approx 6-10 dev-weeks).

Milestone 1: Design, API + Storage (1 sprint)
- Deliverables:
  - Finalize JSON API contract for create/get/list/execute/cancel/export.
  - DB schema (migrations) for site_auto_upgrade_plans, site_auto_upgrade_waves, site_auto_upgrade_targets, site_auto_upgrade_events.
  - Input validation library & dry-run resolver for target_selector.
- Tasks:
  - Define and freeze request/response schemas (OpenAPI snippets).
  - Implement DB migrations and models/ORM mappings.
  - Unit tests for validation and dry-run.
- Dependencies: authentication, device inventory service (for target resolution).

Milestone 2: Execution Engine & Scheduler Integration (1-2 sprints)
- Deliverables:
  - Scheduler hooks: schedule job to start plan at scheduled_start respecting maintenance window.
  - Wave runner: converts wave into set of device upgrade jobs, respects concurrency & retry rules.
  - Event ingestion endpoint to capture device success/failure and update events and plan status.
- Tasks:
  - Integrate with existing orchestration queue (or add new queue/topic).
  - Implement concurrency enforcement; implement queueing/fair-share when multiple plans compete.
  - Implement retry/backoff and device job backchannel handling.
- Dependencies: orchestration/scheduler, device job executor API, notification service.

Milestone 3: Staged Policies, Rollback, Exports, Monitoring & Tests (1-2 sprints)
- Deliverables:
  - Implement staged (wave) logic with percentage->target mapping deterministic algorithm.
  - Implement rollback workflows and rollback job tracking.
  - Exporter: SQL/CSV exporter for plan + events + targets with anonymization support.
  - Monitoring/metrics: plan counts, active plans, failures, average wave length; dashboards and alerts for failures.
  - Comprehensive integration, e2e and load tests.
- Tasks:
  - Implement wave mapping, min_success check, wave transition logic.
  - Implement event audit logging and notification triggers.
  - Add endpoint GET /export.

Rollout Plan
- Start behind feature flag.
- Internal dogfood on non-production data with synthetic devices.
- Gradual enable for select customer accounts/sites.
- Monitor metrics closely for concurrency/backpressure problems.

Rollback Strategy for the Feature
- Feature flag switch off -> scheduler stops scheduling new plans; running plans continue but no new plans created.
- DB migration reversible if needed.

Monitoring & Alerting
- Metrics to capture:
  - Plans created / started / completed / failed rates
  - Devices upgraded per minute
  - Per-plan failure rate
  - Queue backlog for upgrade jobs
- Alerts:
  - Excessive plan failures (> X% in Y minutes), queue backlog > threshold.

Risks & Mitigations
- Risk: Concurrency limits insufficient -> cause network/device strain. Mitigation: conservative default limits, phased rollout.
- Risk: Wrong target_selector mapping causes mass upgrade. Mitigation: required dry-run and confirmation on large targets, safety caps.

Dependencies & Integration Points
- Authentication & RBAC
- Device inventory and device attributes service (to resolve selectors)
- Orchestration/scheduler and device job executor
- Notification service (email/Slack/webhooks)

Deliverable Sign-off Criteria
- All API endpoints implemented and passing contract tests.
- End-to-end tests demonstrating staged rollout working with simulated failures and rollback.
- SQL exporter produces accurate exports that import cleanly into a RDBMS cluster.

File paths
- Spec & plan location: specs\\118-audit-menu-118-site-auto-upgrade-configuration\\

End of plan.md

