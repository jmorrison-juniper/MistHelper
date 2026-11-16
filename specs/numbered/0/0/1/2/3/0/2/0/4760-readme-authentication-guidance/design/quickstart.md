# Quickstart: README Authentication Guidance

## Prerequisites

- Use the issue 4760 worktree.
- Keep all unrelated README text unchanged.
- Do not use production credentials or contact Mist Cloud.

## Validation

1. Review the `Who`, `Where`, and Step 2 credential setup in `README.md`. Confirm both authentication methods, the conditional verification-code prompt, and HTTPS token transmission.
2. Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py`.
3. Run `ste-linter --config .ste-linter.toml --min-score 80 README.md`.

The targeted tests must pass. The README must meet the configured STE score.
