# Analysis: Menu 1 Compliance Refactor Closeout

## 2026-09-14 closeout

The issue matched the existing spec directory `specs/003-menu1-compliance-refactor`.
This directory currently holds `tasks.md` only. It does not hold `spec.md` or `plan.md`.
The issue body and the task list therefore served as the closeout record.

I verified that `CHANGELOG.md` already records the extraction.
The entry is under `26.03.04.00.55` and says `Extract OrgAlarmEventExporter from OrgExportUtils (5-Item Rule compliance)`.
I did not edit `CHANGELOG.md`.
I checked T022 in `tasks.md` because it was a stale checkbox.

I completed the deployment ceremony for T023.
I pulled `ghcr.io/jmorrison-juniper/misthelper:latest`.
I restarted only `misthelper-app` in the compose group with `.\scripts\compose.ps1 up -d --no-deps misthelper`.
The first readiness check returned 503 because the old app container was unhealthy.
I removed only the application container by container ID.
I started `misthelper-app` again in the compose group.
`podman ps` reported `misthelper-app` healthy and running from the latest image.
The web readiness endpoint at `http://127.0.0.1:8055/ready` returned 200.

No code change was necessary.
No release note fragment was necessary because this pull request only closes stale spec tasks.
