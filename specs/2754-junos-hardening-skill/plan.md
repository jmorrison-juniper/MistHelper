# Implementation Plan: Junos hardening skill

**Branch**: `docs/2754-junos-hardening-skill` | **Date**: 2026-09-16 | **Spec**: `specs/2754-junos-hardening-skill/spec.md`

**Input**: Feature specification from `specs/2754-junos-hardening-skill/spec.md`

## Summary

Add one source-grounded Junos hardening skill for the hardening decisions that
MistHelper exposes. The skill will cite repository rules first, cite Juniper
documentation for Junos command effects, and mark unavailable corpus details as
unverified.

## Technical Context

**Language/Version**: Markdown documentation only. The worktree virtual
environment uses Python 3.13 and `mistapi` 0.64.0 for validation.

**Primary Dependencies**: Existing repository documentation tools only.

**Storage**: Markdown files in `.github/skills/`, `specs/`, and `changelog.d/`.

**Testing**: Ruff, Black, diagram reference lint, citation check, pytest collect,
and the STE linter.

**Target Platform**: GitHub Copilot skill discovery in this repository.

**Project Type**: Documentation and agent skill package.

**Performance Goals**: Keep the skill directory at or below 400 KB.

**Constraints**: Do not edit `MistHelper.py`, OpenAPI files, or `documentation/api/`.
Do not copy the external Juniper corpus into the repository.

**Scale/Scope**: One skill entry point, four reference files, three SpecKit files,
and one release-note fragment.

## Constitution Check

- Five-Item Rule: This documentation package adds one skill directory with one
entry point and one `references` directory. The reference directory contains four
files.
- Safety: The skill reinforces secret handling, typed confirmation, and the ZTP
terminal gate.
- Quality gates: The local gates named in issue #2754 will run before commit.
- STE: Each new Markdown file will run through the STE linter.
- Git workflow: The branch starts from `origin/main` and targets `main` by pull
request.

## Project Structure

### Documentation for this feature

```text
specs/2754-junos-hardening-skill/
├── spec.md
├── plan.md
└── tasks.md
```

### Source files changed

```text
.github/skills/hardening-junos/
├── SKILL.md
└── references/
    ├── source-index.md
    ├── repository-decisions.md
    ├── junos-verified-rules.md
    └── validation-and-gaps.md

changelog.d/
└── issue-2754-junos-hardening-skill.md
```

**Structure Decision**: Use the same `SKILL.md` plus `references/` shape as the
merged Mist API and Python optimization skills.

## Complexity Tracking

No constitution violation exists. The feature is documentation-only and does not
change application code.
