# Local build revision decisions

## Build metadata

**Decision**: Use compose build labels with a helper-scoped environment value.
**Rationale**: Both supported image builders accept compose build labels, and the existing overlay is already build-only.
**Alternative**: A container recipe argument would require changes to both recipe variants and CI metadata precedence.

## Dirty detection

**Decision**: Read `git status --porcelain --untracked-files=normal`.
**Rationale**: This includes staged, unstaged, and untracked changes, while ignored runtime files remain outside the decision.
**Alternative**: `git diff HEAD` would omit untracked build inputs.

## Dirty freshness

**Decision**: Fail with an explicit uncommitted-content explanation.
**Rationale**: A base commit cannot establish the content of a dirty image.
**Alternative**: Removing `-dirty` and reporting current would make an unsupported freshness claim.

## Verification

**Decision**: Execute the actual PowerShell helper with native command substitutes.
**Rationale**: This proves argument flow, environment restoration, and failure decisions without changing shared containers.
**Alternative**: Text contracts alone cannot prove command execution.
