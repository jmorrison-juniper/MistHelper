# Implementation Plan: Organization Security Posture Checklist

**Branch**: `feat/3557-org-security-posture` | **Date**: 2026-09-29 | **Spec**: `specs/3557-org-security-posture/spec.md`

**Input**: Feature specification from `specs/3557-org-security-posture/spec.md`

## Summary

Menu 276 will produce one organization security posture checklist for a Mist organization. The implementation will read organization settings and related organization security resources, evaluate one small check class per setting, write `data/OrgSecurityPosture.csv`, and print pass, fail, and review counts.

The implementation plan defines the check model, the check registry, the runner, and the output contract. Menu wiring and primary key strategy changes are deferred to `specs/3557-org-security-posture/wiring.md`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, existing MistHelper export utilities, and the Python standard library.

**Storage**: CSV output through the existing export path. No new durable operational store is required.

**Testing**: `pytest`, `python -m py_compile`, `python -m ruff check`, and `python -m black --check` for touched implementation files.

**Target Platform**: Windows development, Linux container runtime, and SSH session execution.

**Project Type**: Command-line menu operation in the existing MistHelper application.

**Performance Goals**: Complete a normal organization checklist run in one operator action. Avoid repeated calls for the same organization resource.

**Constraints**: `--test` must not prompt, must not require network access, and must still write the required CSV structure. Missing or ambiguous source data must produce `review`, not `pass`.

**Scale/Scope**: One organization-level checklist. The first release covers at least sixteen checks across password policy, session policy, API policy, remote shell, packet capture, and stale configuration cleanup.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan response |
|-----------|--------|---------------|
| Five-Item Rule | PASS | Use one nested package with no more than five direct modules at each level. Group check classes by area. |
| Class-Based Architecture | PASS | Each setting check is a small class. The registry and runner are classes. No wrapper function is planned. |
| Safety-First | PASS | The operation is read-only. Normal mode fails safely when organization context is missing. |
| Full Deployment Pipeline | REVIEW | This step creates planning artifacts only. Implementation must run local gates and the full pull request pipeline. |
| Observability and Logging | PASS | Implementation must log before and after API reads, evaluation, export, and summary output. |
| Inline Comments | PASS | Implementation must add inline comments to each generated executable line. |
| Action Logging | PASS | Implementation must add `info` before each action and `debug` after each action. |
| Technology and Compatibility | PASS | Use `mistapi` methods after verification. Use `pathlib.Path` or `os.path.join` for paths. |
| Output Backends | PASS | The checklist uses the existing export path and writes the required CSV evidence file. |

## Project Structure

### Documentation (this feature)

```text
specs/3557-org-security-posture/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- wiring.md
+-- contracts/
    +-- checklist-output.md
    +-- mist-api-sources.md
```

### Source Code (repository root)

```text
src/
+-- reports/
    +-- org_security_posture/
    +-- checks/
    |   +-- api.py
    |   +-- base.py
    |   +-- password.py
    |   +-- registry.py
    |   +-- access.py
    +-- io/
    |   +-- exporter.py
    |   +-- formatting.py
    |   +-- sources.py
    +-- models.py
    +-- runner.py

tests/
+-- unit/
    +-- reports/
        +-- org_security_posture/
            +-- test_org_security_posture_checks.py
```

**Structure Decision**: Put new implementation code in `src/reports/org_security_posture/`. This keeps the feature with other reports and preserves the fleet ownership boundary.

## Design Overview

### Check class rule

Each security setting has one small check class. Each class owns one stable `check_id`, one `area`, one `setting_path`, one `recommended_value`, one source page, and one evaluation rule.

Each class returns a `SecurityPostureCheckResult` with these fields:

- `check_id`
- `area`
- `setting_path`
- `current_value`
- `recommended_value`
- `verdict`
- `reason`

The `source_page` value stays check metadata. The CSV does not export it.

The only allowed verdict values are `pass`, `fail`, and `review`.

### Registry

`OrgSecurityPostureCheckRegistry` returns the check classes in a stable order. The registry order is the CSV order. Tests must fail if duplicate check IDs exist.

### Runner

`OrgSecurityPostureRunner` gets source data, asks the registry for checks, evaluates all checks, writes `OrgSecurityPosture.csv`, and prints a summary with pass, fail, and review counts.

`--test` mode uses fixture data and the same runner path. It does not prompt and does not call the Mist API.

### Mist API sources

Implementation must use these OpenAPI operation IDs as the source list:

- `getOrgSettings`
- `listOrgSsos`
- `listOrgAdmins`
- `listOrgApiTokens`
- `listOrgWebhooks`

Before client code is written, implementation must verify these operation IDs and their response shapes in `documentation/mist-api-openapi3json.json` and in `mistapi`.

## Planned Checks

| Check ID | Area | Setting Path | Recommended Value | Verdict rule |
|----------|------|--------------|-------------------|--------------|
| `ORGSEC-PASSWORD-001` | Password policy | `organization settings > password policy > enabled` | Enabled | Pass when enabled. Fail when disabled. Review when absent. |
| `ORGSEC-PASSWORD-002` | Password policy | `organization settings > password policy > minimum length` | At least 12 characters | Pass when value is at least 12. Fail when lower. Review when absent or unclear. |
| `ORGSEC-PASSWORD-003` | Password policy | `organization settings > password policy > uppercase required` | Required | Pass when required. Fail when not required. Review when absent. |
| `ORGSEC-PASSWORD-004` | Password policy | `organization settings > password policy > lowercase required` | Required | Pass when required. Fail when not required. Review when absent. |
| `ORGSEC-PASSWORD-005` | Password policy | `organization settings > password policy > number required` | Required | Pass when required. Fail when not required. Review when absent. |
| `ORGSEC-PASSWORD-006` | Password policy | `organization settings > password policy > special character required` | Required | Pass when required. Fail when not required. Review when absent. |
| `ORGSEC-PASSWORD-007` | Password policy | `organization settings > password policy > password reuse history` | Reuse blocked for at least the last 5 passwords | Pass when history is at least 5. Fail when lower. Review when absent or unclear. |
| `ORGSEC-PASSWORD-008` | Password policy | `organization settings > password policy > maximum password age` | 90 days or less, or review with federated identity evidence | Pass when age is 90 days or less. Review when SSO evidence must decide. Fail when age is higher with no SSO evidence. |
| `ORGSEC-PASSWORD-009` | Password policy | `organization settings > password policy > two-factor required` | Required | Pass when required. Fail when not required. Review when absent. |
| `ORGSEC-SESSION-001` | Session policy | `organization settings > session policy > idle timeout` | 30 minutes or less | Pass when timeout is 30 minutes or less. Fail when higher. Review when absent. |
| `ORGSEC-SESSION-002` | Session policy | `organization settings > session policy > maximum session lifetime` | 12 hours or less | Pass when lifetime is 12 hours or less. Fail when higher. Review when absent. |
| `ORGSEC-API-001` | API policy | `organization settings > API policy > API access` | Restricted to authorized administrators, or disabled when not required | Pass when restricted or disabled. Fail when broad access is allowed. Review when absent. |
| `ORGSEC-API-002` | API policy | `organization settings > API policy > token expiration` | API tokens expire within 365 days or less | Pass when all visible tokens expire within 365 days. Fail when any token exceeds 365 days. Review when expiration is absent. |
| `ORGSEC-API-003` | API policy | `organization settings > API policy > webhook URLs` | Every configured webhook URL uses `https://` | Pass when every URL starts with `https://`. Fail when any URL is non-HTTPS. Review when no URL exists. |
| `ORGSEC-REMOTE-001` | Remote shell | `organization settings > remote shell` | Disabled unless there is a documented break-glass exception | Pass when disabled. Fail when enabled. Review when absent or exception evidence is required. |
| `ORGSEC-REMOTE-002` | Remote shell | `organization settings > Junos shell role access` | Every role is set to none | Pass when every visible role is `none`. Fail when any role allows access. Review when absent. |
| `ORGSEC-CAPTURE-001` | Packet capture | `organization settings > packet capture` | Disabled unless there is an active troubleshooting exception | Pass when disabled. Fail when enabled. Review when absent or exception evidence is required. |
| `ORGSEC-CAPTURE-002` | Packet capture | `organization settings > packet capture bucket verified` | Verified | Pass when verified. Fail when unverified. Review when absent. |
| `ORGSEC-CLEANUP-001` | Stale configuration cleanup | `organization settings > stale configuration cleanup` | Enabled | Pass when enabled. Fail when disabled. Review when absent. |

## Phase 0 Research Output

Research decisions are recorded in `specs/3557-org-security-posture/research.md`.

## Phase 1 Design Output

Design artifacts are recorded in:

- `specs/3557-org-security-posture/data-model.md`
- `specs/3557-org-security-posture/contracts/checklist-output.md`
- `specs/3557-org-security-posture/contracts/mist-api-sources.md`
- `specs/3557-org-security-posture/quickstart.md`
- `specs/3557-org-security-posture/wiring.md`

## Post-Design Constitution Check

| Principle | Status | Result |
|-----------|--------|--------|
| Five-Item Rule | PASS | The proposed package keeps direct child counts within the rule. |
| Class-Based Architecture | PASS | The design uses check classes, a registry class, and a runner class. |
| Safety-First | PASS | The design is read-only and treats absent data as review. |
| Full Deployment Pipeline | REVIEW | Implementation and pull request steps remain outside this planning step. |
| Observability and Logging | PASS | The runner must log all data reads, evaluations, exports, and summary output. |
| Output Backends | PASS | The CSV contract uses the existing export path and required file name. |

## Complexity Tracking

No constitution violation is planned.
