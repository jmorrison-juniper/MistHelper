# Evidence Quality Checklist: Converter Parity Evidence Gate

**Purpose**: Check the quality of the remote evidence in `design/research.md` before the register refresh.
**Created**: 2026-11-26
**Feature**: [research.md](../research.md)

## Evidence Quality

- [x] CHK001 Each remote check cites a path, a ref, a blob SHA or a stated marker, a result, and a line.
- [x] CHK002 Each code or document claim in `spec.md`, `plan.md`, and `analysis.md` has a remote check ID from R01 to R77.
- [x] CHK003 Each Mist API claim cites the OpenAPI file, and each SDK claim cites the installed mistapi file.
- [x] CHK004 The OpenAPI blob size and the operation lines match the local file.
- [x] CHK005 Absent paths are recorded as absent. The parity path drift appears as finding F-02.
- [x] CHK006 Upstream claims cite the observed commit `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c`, not the default branch.
- [x] CHK007 The local worktree is never cited as presence on main. Decision D-4 states the rule.
- [x] CHK008 Each unverified claim appears in the Unverified list with a reason.
- [ ] CHK009 Issue and pull request states carry a read timestamp.
  - Not met: the GitHub State table records states without a read timestamp. Add the timestamp at the parity T004 refresh.
- [x] CHK010 The record states that no test, linter, or build ran.
