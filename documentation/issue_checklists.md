# Issue Checklists and Acceptance Criteria

This document contains detailed checklists for each of the issues created from the TODO/WIP scan, and acceptance criteria to mark the work done.

---

## Issue #4  Investigate re-adopt switch failure on non-VC (Menu #143)
- [ ] Reproduce failure and capture full API request/response (headers, body, status, raw response).
- [ ] Inspect mistapi.readoptSiteOctermDevice docstring and official API docs.
- [ ] Implement `is_device_vc_capable(site_id, device_id)` helper.
- [ ] Add preflight check in `DeviceUtilityCommands.readopt_device` to skip non-VC devices with a clear message.
- [ ] Add unit tests (mocked API): VC vs non-VC flows.
- [ ] Add integration test against lab device (if available).
- [ ] Update menu help text and changelog.

Acceptance criteria:
- Non-VC devices do not call readopt API and produce a clear message.
- VC-capable devices invoke the existing API call unchanged.

---

## Issue #5  Fix clear_session API body/prompt (Menu #149)
- [ ] Reproduce the 400 error and record API expectations from cloud doc.
- [ ] Update UI prompts to allow either `service_name` or multiple `session_ids` (comma-separated).
- [ ] Map inputs into API body: `body['service_name'] = ...` or `body['session_ids'] = [...]`.
- [ ] Preserve optional `node` parameter if provided.
- [ ] Add unit tests for both input forms and 400->user-friendly error handling.
- [ ] Add integration test in lab to validate behavior.

Acceptance criteria:
- API call is made with `session_ids` (list) or `service_name` per API contract.
- 400 responses produce actionable guidance rather than opaque errors.

---

## Issue #6  Investigate clear_bpdu_error 400 on EX4100 (Menu #151)
- [ ] Reproduce with EX4100 and capture failing request/response.
- [ ] Confirm required body keys (port identifier format) via mistapi docstring.
- [ ] Implement port normalization helper mapping human interface names (e.g., ge-0/0/0) to API-expected identifier.
- [ ] Add fallback attempts (alternate key names) when 400 is returned.
- [ ] Add unit tests covering normalization and fallback logic.

Acceptance criteria:
- BPDU clear succeeds when the port exists and is specified correctly.
- When unsupported, emit clear guidance explaining requirements.

---

## Issue #7  Investigate clear_learned_macs 400 on EX4100 (Menu #152)
- [ ] Reproduce and record API expectation for `clearAllLearnedMacsFromPortOnSwitch` body.
- [ ] Use same port normalization helper as Issue #6.
- [ ] Add graceful error-handling and retries with normalized inputs.
- [ ] Unit tests for Junos-style interface names and edge cases.

Acceptance criteria:
- Learned MACs clearing works for Junos-style port names or provides a helpful message.

---

## Issue #8  Investigate clear_policy_hit_count 400 on SSR120 (Menu #153)
- [ ] Reproduce on SSR120; try calling with and without `node` param.
- [ ] Check mistapi docs to confirm support for SSR120; add capability detection via `getSiteDevice`.
- [ ] If unsupported by model, skip with a clear message.
- [ ] If required, ensure the `node` param is included in the body.
- [ ] Add unit tests for supported/unsupported models and node handling.

Acceptance criteria:
- SSR120 model either succeeds when `node` provided or is skipped with an explanation.

---

## Issue #9  Stabilize WIP export features (Menus 63-65)
- [ ] Identify all APIs used (searchOrgDeviceEvents, listOrgAuditLogs, gateway device configs) and confirm pagination semantics.
- [ ] Implement chunked streaming writes to CSV/SQLite using `mistapi.get_all` or manual pagination.
- [ ] Add checkpointing (resume token or last-timestamp) to safely restart long exports.
- [ ] Add exponential backoff for 429/5xx and configurable chunk size.
- [ ] Add CLI flags: `--chunk-size`, `--resume`, `--dry-run`, `--duration`.
- [ ] Add integration/stress test scaffolding for long-running exports (mocked API to simulate many pages).

Acceptance criteria:
- Exports for large durations complete without OOM and can resume after interruption.

---

## Issue #10  Stabilize Virtual Chassis conversion (Option 92 - WIP)
- [ ] Review API doc for convertSiteVirtualChassisToVirtualMac and preconditions.
- [ ] Add preflight checks: model compatibility, VC membership, device health, and backups availability.
- [ ] Add mandatory multi-step confirmations and a `--dry-run` mode.
- [ ] Add audit logging and post-op verification steps.
- [ ] Create rollback guidance in documentation.
- [ ] Add thorough unit and integration tests (mocked API and lab playbook).

Acceptance criteria:
- Conversion only proceeds when preflight checks pass and explicit consent provided; dry-run simulates steps without changes.

---

# Notes
- Each checklist maps to a corresponding GitHub issue and the test scaffolding under `tests/`.
- Unit tests are intentionally scaffolds and may be marked xfail until code changes are implemented.
