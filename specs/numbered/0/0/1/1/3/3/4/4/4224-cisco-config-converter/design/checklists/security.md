# Security and Privacy Checklist: Integrate Mist Cisco Config Converter

**Purpose**: Check the security and privacy design before any converter code change merges
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

Each item is checked, or it names the reason that it is open.

## Input Handling

- [x] Accepts six text suffixes and rejects every other suffix (FR-002, R-99).
- [x] Rejects path-like names, drive paths, and null characters before parsing (FR-002, R-38, R-99).
- [x] Decodes strict UTF-8 and rejects invalid bytes (R-38, line 76).
- [x] Limits each upload to 16 MiB and each multipart body to 16 KiB more (R-25, R-26).
- [x] Processes uploads in memory and stores no uploaded file (D-8).

## Credentials and Secrets

- [x] Keeps credentials out of browser storage, uploads, generated files, logs, and fixtures (FR-028, D-4).
- [x] Reads cloud credentials from existing settings on the server only (R-55, D-4).
- [ ] Requires a configured `PORTAL_SECRET_KEY` in production. Open: D-16 is a human decision. The current fallback is a random UUID (R-46).
- [ ] Requires a verified operator identity before each write. Open: D-16 is a human decision. `web_portal/app.py` defines no login route (A-12).
- [x] Redacts unsupported values that can carry a credential. Unsupported items keep line numbers and command categories only (R-98, child 4640 D-8).

## Cloud Writes

- [x] Uses mistapi methods only and no direct HTTP to Mist (plan constitution check, R-80).
- [x] Requires the typed word APPLY before an apply run (FR-016, D-5).
- [x] Refuses an apply when the write family is disabled (D-3, D-15).
- [x] Refuses an approval older than 15 minutes (FR-016, data model).
- [x] Makes no application retry for a write (D-6, R-79).
- [x] Marks an ambiguous write as indeterminate and stops the run (FR-019).
- [ ] Excludes service-policy deletion until the owner approves the scope. Open: D-15 is a human decision (A-22).

## Privacy and Storage

- [x] Stores converter state as private files under `data/`. It uses no new database (D-7, FR-033).
- [ ] Keeps private converter files out of the shared data browser. Open: the exclusion change is pending. The browser excludes only the firmware backup name (R-47, A-13, task T024).
- [x] Keeps browser evidence under `test-artifacts/` and out of the repository (child 4648 D-11).

## Logging

- [x] Logs in ASCII only (constitution Principle V, R-59).
- [x] Logs each action before and after it runs (constitution Principle VII, R-61).
- [x] Logs no request body and no configuration value (R-58, D-12).

## Tests

- [x] Uses synthetic data and simulated SDK responses only (FR-032).
- [x] Uses no live Mist credential in tests (FR-032, D-4).
- [x] Proves zero SDK write calls after each refused approval (SC-003, task T021).
