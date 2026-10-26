# Bootstrap pip security research

## Decision

Require `pip>=26.2.2` in each existing requirement installation.

## Evidence

At `a558faf44`, the original bootstrap installed pip 26.0.1.
The installed-environment audit reported eight rows with four distinct identifiers.
Issue #4360 records a clean audit after a local upgrade to pip 26.2.2.
The current requirements audit separately aborts in temporary-environment `ensurepip`.

## Rationale

An explicit minimum repairs old environments and permits newer supported releases.
The existing transaction preserves installer selection, package sources, transport limits, and failure handling.

## Alternatives Considered

- `upgrade_deps=True`: Reject because environment creation bypasses the existing source policy and cannot repair an existing environment.
- A separate upgrade subprocess: Reject because the existing transaction can enforce the minimum.
- Unbounded `--upgrade`: Reject because it can change unrelated product dependency resolution.
- A product dependency pin: Reject because pip belongs to development setup, not the product requirements.
