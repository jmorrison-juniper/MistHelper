# Security Checklist: WAN Performance portal integration

**Purpose**: Check the security and secret rules for the feature
**Created**: 2026-11-26
**Feature**: `spec.md`, `design/contracts/storage-and-cache.md`

- [x] SEC001 Portal access uses the existing `SecurityMiddleware` allowlist (FR-013, `web_portal/services/config.py` line 159, R75).
- [x] SEC002 POST routes use the existing CSRF protection (FR-013, `web_portal/app.py` lines 236-245, R71).
- [x] SEC003 Identifiers are validated before any call (FR-007, `identity.py` line 7, R63). Path components are rejected.
- [x] SEC004 The Redis password is read from configuration only (FR-014, `request_admission.py` line 64, R59).
- [x] SEC005 No token store is added. The Mist API session comes from the existing portal session (FR-013).
- [x] SEC006 Logs and pages never show a secret. The test plan checks each error page for a secret pattern (T022).
- [x] SEC007 Tests use mocked Mist responses and no production credential (issue 4200 test plan, quickstart step 5).
- [x] SEC008 The source license blocks copies. The feature uses an independent implementation (D-1, R131, R132).
- [x] SEC009 Each Redis key uses the `misthelper:wan:v1:` or `misthelper:api:v1:` namespace (contracts/storage-and-cache.md).
- [x] SEC010 No new port is published. The compose diff adds no port (SC-008, R81).
