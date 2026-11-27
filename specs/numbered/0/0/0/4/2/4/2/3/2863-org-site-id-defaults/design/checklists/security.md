# Security Requirements Quality Checklist: Organization and site identifier defaults

**Purpose**: Check that the security and redaction requirements are complete and testable.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Secret and Input Handling

- [x] Each refusal message names the field and omits the input value (FR-005). Test: `test_refusal_names_field_without_value`.
- [x] Each refusal log record names the field and omits the input value (FR-006). Test: `test_refusal_logs_field_only`.
- [x] A private value with sensitive text does not reach the message or the log record (User Story 1, scenario 4).
- [x] This change reads, prints, and stores no token or password. It adds no new environment variable read. The one existing organization environment read is at `wsgi.py:55` (research RC-77).

## Logging and Output

- [x] Log text and messages use ASCII only (`.specify/memory/constitution.md:182-203`, Principle V).
- [x] Log lines use `%s` formatting, not f-strings (`AGENTS.md:104-116`).
- [x] Each refusal writes one error record. The record carries no timestamp, because the logging library adds one.

## Destructive and State-Changing Paths

- [x] Batches 4 and 5 touch destructive menus (`src/foundation/support/utils/operation_registry.py:183-185` and `:636`). Human review stays required (D-11).
- [x] A refusal occurs before each write or restart call (FR-016).
- [x] A refusal never returns an empty result for a state-changing call (`design/contracts/tenant-identifier-refusal.md`).
- [x] No `auto-merge` label goes on a pull request that changes a destructive operation (`AGENTS.md:230-231`).

## Testing Safety

- [x] Tests use mocked SDK responses. No test calls the live Mist cloud (`AGENTS.md`, Tests section, and `.github/copilot-instructions.md:50-76`).
- [x] Tests create no production credential.
- [x] Tests write to `tmp_path` or to memory only. They create no product output under `data/`.

## Findings and Suppressions

- [x] No security finding is suppressed. Bandit runs on the changed folder (T-LOCAL-GATES step 9).
- [x] The baseline guard never raises a count on its own (`design/contracts/ratchet-baseline.md`).
- [x] Credential and environment defaults belong to issue #2861. They are out of scope for this record, and the scope section says so.

## Notes

- The residual risk of a malformed but non-blank identifier reaching the cloud is recorded in `plan.md`. The existing HTTP contract returns an empty result for that case (FR-009).
- The change adds no network path and no file path. The security review of this record found no new trust boundary.
