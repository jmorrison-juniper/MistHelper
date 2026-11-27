# Security Requirements Quality Checklist: Windows Symlink Privilege in the Spec-Route Contract Guard

**Purpose**: Check that the fixture change keeps the guard secure and grants no new right

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Privilege and Host Changes

- [x] The change grants no symlink privilege. Decision D-3 and the Non-Goals section say so.
- [x] The change does not enable Developer Mode. Decision D-3 records the reason.
- [x] The rule in AGENTS.md line 159, which forbids widening permissions to repair a permission error, is applied in D-3.

## Guard Integrity

- [x] The production reparse-point checks stay unchanged. FR-006 covers this, and research rows RC-12 and RC-13 cite the lines.
- [x] No assertion of the symlink case is removed or weakened. FR-005 and FR-007 cover this.
- [x] A red proof removes the reparse-point check on the task branch. Task T008 and SC-004 cover it.
- [x] A skip prints its cause. FR-003 and AGENTS.md lines 142-143 cover this.

## Command Safety

- [x] The `mklink` command runs with a list of arguments. The fixture passes no shell string built from input.
- [x] The fixture builds all paths under `tmp_path`. No external input reaches the command.
- [x] The junction target stays inside `tmp_path`. The Warning in `spec.md` and the Limits section of the link contract cover this.

## Data Exposure

- [x] The log lines print link and target paths only. The contract `link-fallback.md` covers this.
- [x] The skip reason prints the `mklink` output. The output holds a path and a Windows message only. This path uses no credential.

## Notes

- Open items: U-1 (junction privilege) and U-2 (results on the affected host) remain open until task T-LOCAL-GATES and task T002 finish.
