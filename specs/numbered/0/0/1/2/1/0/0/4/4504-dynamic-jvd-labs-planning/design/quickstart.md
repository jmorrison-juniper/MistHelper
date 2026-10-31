# Quickstart: GUI Journeys and Test Hooks

This is a design for acceptance tests. Nothing here runs today. Port 8055 is the existing portal.
Each hook is a stable `data-testid`. Each failed browser flow keeps a screenshot or trace under `test-artifacts/`.

| Journey | Steps | `data-testid` values |
| - | - | - |
| Catalog and preview (US1) | Open Labs, select template, edit parameters, preview | `labs-tab`, `labs-catalog-row`, `labs-parameter-form`, `labs-preview-submit`, `labs-preview-topology`, `labs-plan-digest`, `labs-field-error` |
| Import and compose (US2) | Import file, read rejection, compose blocks, preview | `labs-import-file`, `labs-import-submit`, `labs-import-error`, `labs-block-picker`, `labs-block-unavailable` |
| Qualify and approve (US3) | Qualify, read gates, type approval word | `labs-qualify-submit`, `labs-capability-gate`, `labs-approval-word`, `labs-approval-submit`, `labs-approval-invalid` |
| Deploy and monitor (US4) | Start job, watch progress, refresh page, read monitoring | `labs-deploy-submit`, `labs-job-progress`, `labs-job-state`, `labs-monitor-inventory`, `labs-monitor-freshness`, `labs-recovery-required` |
| Test and impair (US5) | Propose test or impairment, approve, restore | `labs-impair-profile`, `labs-impair-submit`, `labs-restore-submit`, `labs-evidence-list` |
| Cleanup (US6) | Propose cleanup, approve, read outcome | `labs-cleanup-submit`, `labs-cleanup-outcome`, `labs-cleanup-skipped` |

Stable artifacts: screenshot per journey step, Playwright trace for each failure, and sanitized job evidence.
Live acceptance uses the same hooks but needs separate approval (T104).
