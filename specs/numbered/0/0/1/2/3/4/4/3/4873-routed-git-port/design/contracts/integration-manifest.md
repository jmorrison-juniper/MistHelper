# Contract: Integration manifests and local rules

**Scope**: `.specify/integrations/copilot.manifest.json`, `.specify/integrations/speckit.manifest.json`, and `.github/copilot-instructions.md`.

## Manifest Schema

- `integration` is a string. Values are `copilot` and `speckit`.
- `version` is a string. The value is `1.4.3` in both files.
- `installed_at` is an ISO 8601 UTC timestamp.
- `files` is an object. Each key is a repository-relative path with forward slashes. Each value is a lowercase hexadecimal SHA-256 of the file bytes.
- The copilot manifest lists nine skill files. The speckit manifest lists thirteen files.

## Hash Rule

- The hash covers the bytes as committed. The check does not normalize line endings.
- Eight of twenty-two hashes match the committed bytes today (rows R-041 to R-062 in `research.md`).
- The three routed templates match neither the repository bytes nor the upstream bytes (rows R-056, R-058, R-060, R-063 to R-065). The cause is unverified (U-2).

## Local Rule List

- Location: `.github/copilot-instructions.md`, a section named "Managed Spec Kit files with a local rule". T013 adds the section.
- Columns: `Managed file`, `Relation to upstream`, `Local rule`, and `Guard`.
- Each managed file whose committed hash differs from the manifest has one row.
- Each row names the guard test that enforces the rule.

## Guard Behavior

File: `tests/guardrails/test_integration_local_rules.py`.

- `test_managed_hashes_match_or_have_a_local_rule` passes when each manifest hash equals the committed bytes, or when the path has a row in the local rule list. A failure names each file and prints the count of examined and failed files.
- `test_local_rule_list_names_only_managed_files` passes when each row names a manifest entry. A failure names the unknown path.
- `test_routed_templates_keep_local_rule` passes when the three routed templates each have a row.
- A guard that cannot read a manifest or the rule section fails with the path. The guard never skips silently.

Failure example:

```text
managed file .specify/templates/plan-template.md: hash differs and has no local rule (examined 22 files, 1 failed)
```
