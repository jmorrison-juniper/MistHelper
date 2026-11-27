# Checklist: Routing

**Purpose**: Check the route, the numbering, and the pointer rules.
**Created**: 2026-11-26
**Feature**: `spec.md` in this folder

- [x] RTE001 The route has eight digits and equals the base-5 digits of 4873. Evidence: `design/research.md` D-14 and R-022.
- [x] RTE002 The route leaf holds the records of one issue. Evidence: each issue number maps to one route, so the leaf is unique to the issue.
- [x] RTE003 The git scripts and the core script use the same scan scope. Evidence: D-7, FR-008, FR-009, and R-009.
- [x] RTE004 Timestamp names do not raise the sequential number. Evidence: the exclusion `^\d{8}-\d{6}-` in the 1.0.0 script (R-083) carries into the 1.0.8 scripts.
- [x] RTE005 The git script creates no record. Evidence: D-8 and `contracts/git-create-feature-cli.md`.
- [x] RTE006 The pointer does not change in this change. Evidence: FR-020, D-17, and R-036.
- [x] RTE007 The PowerShell and bash scripts share one numbering rule. Evidence: FR-008, FR-009, and `contracts/git-create-feature-cli.md`.
- [x] RTE008 A path with spaces works in the bash loop. Evidence: T008 acceptance requires a line-by-line loop over `find` output.
- [ ] RTE009 The bash behavior runs on macOS or Linux. Explained: this record cannot run bash on Windows (U-5). The implementer runs the quickstart on a POSIX host.
