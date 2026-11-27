# Security Requirements Quality Checklist: Site Request Admission by Organization

**Purpose**: Check that the security and data-handling requirements of issue #4921 are complete and testable.
**Created**: 2026-11-26
**Feature**: `spec.md` and `plan.md` for issue #4921

## Credential and Secret Handling

- [x] CHK001 The site organization map stores no credential. It stores only site identifiers and organization identifiers. (`data-model.md` Site Organization Map)
- [x] CHK002 The existing credential fingerprint stays in place. The change does not alter the credential handling of `admit`. (`request_admission.py` lines 78 to 81 on `main`)
- [x] CHK003 The session organization read never prompts and never exposes a credential. (`research.md` R31)
- [x] CHK004 No test uses a production credential. The tests use the fake Redis client and invented identifiers. (`plan.md` Test Strategy)

## Consent and Command Safety

- [x] CHK005 The change keeps the batch confirmation of menu 309 unchanged. The change touches only the admission attribution. (`spec.md` Non-Goals)
- [x] CHK006 The shell trigger request keeps its path and body. The change adds no command. (`research.md` R46 and R47)
- [x] CHK007 The live check stops at the preview. It never types the confirmation phrase. (`quickstart.md` Optional Live Read-Only Check)
- [x] CHK008 A wrong attribution changes the quota count only. It grants no access and it runs no command. (`spec.md` Edge Cases)

## Data Exposure and Limits

- [x] CHK009 The learning step logs counts only. It never writes a site identifier or an organization identifier at info level. (`contracts/site-organization-resolution.md` Learning Rules)
- [x] CHK010 The map is bounded at 50,000 entries. Memory use stays bounded for a long process. (`research.md` D-3)
- [x] CHK011 The map is in memory only. It writes no file and no database row. (`data-model.md` Lifetime)
- [x] CHK012 A failed learning step never raises. A Mist read never fails because of the learning step. (`contracts/site-organization-resolution.md` Learning Rules)
- [x] CHK013 The logs use ASCII only. The new messages use the message template and the values, and they hold no secret. (`plan.md` Constitution Check, rule V)

## Notes

- CHK008 accepts a recoverable risk. A wrong fallback changes a counter only. The risk does not affect a credential or a command.
- CHK009 keeps identifiers out of the info log. A debug record may hold a count only.
