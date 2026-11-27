# Security Checklist: Unattended token skip for menu 247

**Purpose**: Check token handling, credential policy, and log safety for this change.
**Created**: 2026-11-26
**Feature**: `spec.md`

- [x] The unattended run never answers the token prompt. The provider raises before any value exists (FR-001, RC-01 to RC-03).
- [x] The unattended run never calls `verifySelfEmail` for option 247 (FR-007, test T001).
- [x] The unattended run never writes the verification audit row for option 247 (FR-008, test T001).
- [x] No real or fabricated token value appears in any test. The stop uses an empty answer.
- [x] Each skip log line names the option, the context, and the skip reason only (FR-014).
- [x] Each skip log line uses ASCII characters (FR-014, test T001).
- [x] No secret or token value appears in STATUS, the summary, the research record, or any other draft file. Environment variable names appear by name only.
- [x] The change adds no dependency, so it adds no supply-chain input.
- [x] The change adds no path write. Telemetry keeps the existing `data/` path.
- [x] The interactive path keeps its cancel behavior for an empty token (FR-012, RC-14 and RC-28).
- [x] The input seam is restored after every operator-only skip (FR-009, RC-05).
- [x] The change leaves the EOF and interrupt handling of the input seam unchanged (RC-20 and RC-21).
