# Dependency Pin Checklist: mando and radon

**Purpose**: Check the dependency decision, the lock state, and the update policy for the mando pin.
**Created**: 2026-11-26
**Feature**: `design/research.md` (D-1, D-2) and `design/contracts/dependabot-pip-ignore.md`

## Upgrade Path

- [x] CHK201 The record checks whether radon offers a release that accepts mando 0.8 (research.md, D-1 Option B).
- [x] CHK202 The record names the newest radon release and its requirement (research.md, R-64 and R-65).
- [x] CHK203 The record checks the installed radon metadata in the local environment (research.md, R-66).
- [x] CHK204 The record rejects the option to replace radon, with the reason (research.md, D-1 Option C).

## Lock State

- [x] CHK205 The record names the lock and export files that stay unchanged (spec.md, FR-003).
- [x] CHK206 The record shows that the pull request changes only the generated export (research.md, E-5).
- [x] CHK207 The record names the lock check and the export guard in the dependency lock job (research.md, E-6).

## Update Policy

- [x] CHK208 The record names the ignore entry, its range, and its comment rule (contracts/dependabot-pip-ignore.md).
- [x] CHK209 The record checks the ignore syntax in the GitHub docs and in dependabot-core (research.md, R-67 to R-70).
- [ ] CHK210 The range form works in the Dependabot service. Explained: U-1 remains open until the first pip update run after the merge.
- [x] CHK211 The record keeps every other update stream unchanged (spec.md, FR-005).

## Security Scope

- [x] CHK212 The record states that mando is absent from `requirements.txt` (research.md, R-06).
- [ ] CHK213 The record reviews the mando 0.8.2 release notes and advisories. Explained: U-5 remains open. The package is dev-only, so the gate does not block the decision.
