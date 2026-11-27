# Checklist: Manifests and local rules

**Purpose**: Check the managed-file state, the hash rule, and the local rules.
**Created**: 2026-11-26
**Feature**: `spec.md` in this folder

- [x] MAN001 Both manifests read version 1.4.3. Evidence: R-039 and R-040.
- [x] MAN002 Each managed path exists on `main`. Evidence: rows R-041 to R-062 each record a blob SHA.
- [x] MAN003 Each stale hash has a local rule or a regeneration task. Evidence: D-11, T012, and T013.
- [x] MAN004 The hash rule covers the committed bytes. Evidence: `contracts/integration-manifest.md` Hash Rule.
- [x] MAN005 The template mismatch has a recorded result and an unverified cause. Evidence: F-06, R-056, R-058, R-060, R-063 to R-065, and U-2.
- [x] MAN006 The ignore rule keeps the pointer tracked. Evidence: R-029 and R-026.
- [x] MAN007 The companion registry entries are unchanged. Evidence: R-081, R-082, and D-9.
- [ ] MAN008 The CLI status output is in the PR. Explained: this record did not run the CLI (U-1). T012 and SC-001 require the output.
