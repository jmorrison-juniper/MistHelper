# Implementation Plan: MistDSW Migration

**Branch**: `jmorrison-juniper-spec-mistdsw-migration`
**Date**: 2026-10-15
**Spec**: [Specification](spec.md)

**Input**: `specs/numbered/0/0/1/1/3/4/1/0/4230-mistdsw-migration/spec.md`

## Summary

Preserve four offline preparation workflows within MistHelper.
Add one preparation page and one unattended preparation command that share domain behavior.
Use the existing ArangoDB logical database and Compose group.
Do not introduce a database, service, API write, menu number, or dependency.
This PR delivers planning documents only.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Existing Flask, Flask-WTF, python-arango, structlog, and Python standard library.
**Storage**: Existing configured ArangoDB logical database for run records. Private files under `data/mistdsw/`.
**Testing**: Existing pytest, Flask client, Playwright, hypothesis, and shared development gates.
**Target Platform**: Windows 11, macOS, Linux, and the existing Podman application image.
**Project Type**: Existing CLI and Flask application, without a separate frontend process.
**Performance Goals**: 500 stores within five seconds on the reference host defined in SC-003.
**Constraints**: Zero cloud requests, 5 MiB upload limit, 500 stores, and 24-hour artifact retention.
**Scale/Scope**: Four workflows, ten networks, four services, two template transforms, and one feature-specific collection.

## Constitution Check

| Principle | Before research | After design |
| --- | --- | --- |
| Managed specification roots | Use fixed eight-level base-5 route for 4230. | Route verified as `0/0/1/1/3/4/1/0`. |
| Five-child structure | Do not add flat source modules. | Feature root has five children. Design subtree has five children. |
| Class-based behavior | Future code requires subject-based classes. | Domain, storage, and presentation own separate behavior. No CLI wrapper scripts. |
| Safety | Preparation only. | No cloud write or production command. |
| Observability | Boundary logging and redaction required. | Tests cover before-action info, after-action debug, and contextual errors. |
| Transport | No external transport needed. | Zero Mist calls. Future deployment needs a separate specification. |
| Outputs | Use managed product and evidence paths. | Private files stay under `data/`. Test evidence stays under `test-artifacts/`. |
| Deployment | No code change or release fragment here. | No build, deploy, merge, or automatic implementation in this PR. |
| Source rights | No license was established. | B1 blocks reuse until permission covers the material. |

Pre-design and post-design gates pass for a documentation-only change.
Implementation authorization remains blocked by B1-B4.
The user explicitly stops this workflow before implementation.
Do not invoke `speckit-implement`, merge this PR automatically, or change a running container.

Existing process-folder debt includes 792 grandfathered direct children under `specs/`.
The baseline stays unchanged.
Incremental remediation action: route each future feature through managed roots and migrate one separately owned legacy record when assigned.
The existing source and portal trees also exceed some five-child limits.
Future implementation must place code in nested compliant packages and avoid increasing a noncompliant parent's direct-child count.
T002 must confirm the exact package location before any code edit.

## Project Structure

### Documentation (this feature)

```text
4230-mistdsw-migration/
  spec.md
  plan.md
  tasks.md
  research.md
  design/
    data-model.md
    quickstart.md
    analysis.md
    contracts/
      preparation.md
      payloads.md
    checklists/
      requirements.md
      migration.md
```

### Source Code (repository root)

Future paths are proposals, not delivered files:

```text
src/operations/execution/configuration/mistdsw/
  domain/       # Inputs, profiles, and generation.
  storage/      # Shared database access and private artifacts.
  presentation/ # CLI, blueprint, and feature templates.
tests/unit/mistdsw/
tests/contract/mistdsw/
tests/integration/mistdsw/
tests/e2e/web_portal/mistdsw/
```

**Structure Decision**: Use a nested feature package within an existing compliant parent.
T002 must verify parent capacity and adjust the proposed root without introducing a compatibility shim.
Use named classes for store variables, switch transformation, gateway transformation, and bundle preparation.
Keep each function within 25 lines and cyclomatic complexity 10.
Use at most five immediate children per new package.
The nested `design/` directory keeps process documents within the same rule.

## Architecture and Integration

Browser or CLI input enters one validation boundary.
Validated inputs enter the same deterministic domain classes.
A preparation run records its profile revision, findings, and verified artifact manifest.
ArangoDB stores the run in the existing configured database.
The file layer writes private artifacts under `data/mistdsw/<run_id>/`.
The current Flask application serves authorized downloads.

The feature uses collection `mistdsw_preparation_runs`, not a new database.
The natural run key is an application-issued UUID. Store identity is the submitted site name within the run.
Retries use an idempotency token and do not create duplicate records.
CSV remains an interchange artifact, not the run store.
Existing SQLite export behavior remains available to other operations.
Do not mirror these runs into SQLite or Redis.
Do not remove the existing Redis service, because other MistHelper features use it.

`compose.yml` remains the only Compose group.
The application uses its current image, `data` mount, ArangoDB connection, and port 8055.
No second app, pod, port, volume, worker container, database, or Redis dependency is required.
An in-process cleanup step enforces expiration.
Downloads check expiration before file access even when physical cleanup is delayed.

Use the existing ArangoDB backup procedure for operational run records.
Verify backup readability and record counts before any destructive database maintenance.
After recovery, verify each artifact manifest, digest, ownership, and original expiration.
Missing or damaged files make the run failed, not ready.
The operator must submit inputs again if a private artifact cannot be recovered.
Do not extend retention during recovery or preserve private exports in indefinite backup files.
T003 covers recovery with synthetic data. This feature adds no database restore endpoint.

The preparation page uses the current base layout and theme.
It provides workflow selection, input fields or upload, validation findings, a reviewed difference summary, and downloads.
CLI preparation accepts an explicit workflow, input, approved profile, and output destination.
No default demo run, implicit home-directory import, or silent overwrite is permitted.
The proposed CLI flag is `--prepare-mistdsw`; no menu number is reserved in this plan.

## Compatibility and Output Rules

Preserve input modes and supported variable names.
Keep JSON types and wrappers as defined in [payload contracts](design/contracts/payloads.md).
Compare independently written fixtures, not copied source tests or exports.
Show normalization and metadata changes before export.
Intentional differences include strict row validation, explicit LAN selection, reviewed tenant mapping, and no source organization default.
Guest and Realo settings require a profile approval rather than a hidden precedence rule.
No existing MistHelper menu, primary-key strategy, or export behavior changes.

## Validation Strategy

Use unit tests for addressing, profile validation, DHCP boundaries, and deterministic output.
Use contract tests for transposed CSV, JSON types, metadata, references, and exact output counts.
Use integration tests for CLI behavior, atomic files, shared storage, retries, and failure transitions.
Use Flask and browser tests for preview, correction, keyboard navigation, ownership, expiration, and downloads.
Use secret canaries to prove that each output boundary removes credentials.
Mock cloud clients and fail the test if any request occurs.
Test a database outage without a ready-file fallback.
Measure 500 stores on the documented reference host before release.

The nine source scenarios are calculation, normalization, gateway rejection, TSV preservation, CSV CLI output, partial gateway rejection, switch transformation, gateway transformation, and network generation.
Tasks T005-T018 cover these scenarios with independently written synthetic data.
The quickstart separates current planning validation from future product tests.

## Blockers and Release Conditions

| ID | Condition | Owner and proof | Effect |
| --- | --- | --- | --- |
| B1 | Source license or reuse permission is absent. | Repository owner supplies written rights and notice rules, or approves independent implementation. | Blocks source reuse and implementation authorization. |
| B2 | Guest VLAN, Guest subnet, and Realo subnet conflict. | Network owner approves a versioned profile with matching networks, gateways, and DHCP. | Blocks output acceptance and production release. |
| B3 | Portal ownership and secret removal need contract proof. | Portal owner approves identity integration and negative tests. | Blocks private upload and download release. |
| B4 | Generated examples are not proof of current Mist schema acceptance. | Network owner approves synthetic schema evidence against the local Mist specification. | Blocks the claim that generated bundles are deployable. |

Planning may finish with these explicit release conditions.
No condition grants permission to bypass another condition.
Automatic deployment stays outside scope even if all four conditions pass.

## Complexity Tracking

No new executable complexity exists in this PR.
No constitution exception is requested.
The documentation layout changes the template's suggested artifact locations to preserve the five-child limit.
All artifact links and task references use the selected layout.
