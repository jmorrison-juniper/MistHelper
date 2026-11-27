# Deployment Checklist: Upgrade Portal Session Recovery

**Purpose**: Check the deployment and operations readiness of the change.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Configuration

- [x] CHK-D01 Each new variable appears in `compose.yml` and in `deploy/.env.example` (FR-020, tasks T008).
- [x] CHK-D02 A container start without the encryption key raises `SettingsError` (FR-019, TP-16).
- [x] CHK-D03 The capture command keeps `--workers 1` and no `--max-requests` option (FR-018, TP-24, RC-10).
- [x] CHK-D04 No requirement or lock file changes. The change adds no package (RC-14).
- [x] CHK-D05 The change adds no new container, port, or volume (plan.md, Dependencies).

## Rollout

- [x] CHK-D06 The rollback steps name the revert, the redeploy, the prefix-only key removal, and the variable removal (plan.md, Rollback Steps).
- [x] CHK-D07 The rollback steps forbid `FLUSHDB`, `FLUSHALL`, and volume removal, with the reason (plan.md, Rollback Steps).
- [ ] CHK-D08 The compose default Redis password change. Explained: this change waits for the approval of decision D-2 and for the operator action in open item OI-10.
- [ ] CHK-D09 The one-time sign-in notice for operators. Explained: the operations owner announces the notice before deployment (D-19, OI-9). The guide text is in task T016.
- [ ] CHK-D10 The deployment window. Explained: deploy when no upgrade run is active (D-19). The operations owner selects the window.
