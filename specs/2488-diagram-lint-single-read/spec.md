# Specification: Diagram reference lint performance

## Goal

Optimize the CI diagram reference lint path for issue #2488.

## Scope

The change applies to `scripts/lint_diagram_refs.py`.
The production command is `python scripts/lint_diagram_refs.py`.
The CI job is `Diagram reference lint`.

## Requirements

- Preserve the public command-line interface.
- Preserve the exit code for the representative repository tree.
- Preserve the full standard output and standard error for the production command.
- Preserve stale reference order and line numbers.
- Keep the implementation sequential.
- Retain the change only if measured performance clears the threshold.

## Non-goals

- Do not add concurrency.
- Do not change Mermaid parsing rules.
- Do not change the allowlist.
- Do not change CI workflow files.

## Acceptance criteria

- The end-to-end CPU median improves by at least 5 percent.
- The output capture matches the baseline exactly.
- The unit tests for `lint_diagram_refs.py` pass.
- The required local quality checks pass.
