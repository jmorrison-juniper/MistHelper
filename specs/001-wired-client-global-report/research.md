# Research: Global Wired Client Search Report

## Decision 1: Operator-based filtering model with local authority

- **Decision**: Apply a shared operator catalog for MAC and manufacturer (`is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, `doesn't end with`, `is blank`, `is not blank`, `is null`, `is not null`), with local filtering as the final authority.
- **Rationale**: Mist-side query behavior is inconsistent for non-positional matching. A deterministic local evaluator guarantees operator semantics required by the spec.
- **Alternatives considered**:
  - Remote-only filtering: rejected due to non-positional mismatch behavior and inconsistent semantics.
  - Local-only retrieval without any remote prefilter attempt: rejected because selective prefiltering can reduce payload size in large orgs.

## Decision 2: Remote pre-filtering as optional optimization

- **Decision**: Use best-effort remote prefiltering only for the explicit positive subset (`is`, `contains`, `starts with`, `ends with`) when endpoint/query semantics align; always run full local operator evaluation on retrieved records.
- **Rationale**: Maintains correctness while still allowing performance improvements for large datasets when remote criteria are usable.
- **Alternatives considered**:
  - Strict mapping of every operator to remote query parameters: rejected because null/blank/negated and positional semantics cannot be uniformly guaranteed.

## Decision 3: Normalization rules

- **Decision**:
  - MAC: case-insensitive, delimiter-insensitive normalization for value-based operators.
  - Manufacturer: case-insensitive string normalization with positional semantics.
- **Rationale**: Aligns with user requirement for partial and positional matching parity while neutralizing format variance.
- **Alternatives considered**:
  - Exact raw-string comparison: rejected because punctuation/case differences create false negatives.

## Decision 4: Value-required vs null/blank operator validation

- **Decision**: Require non-empty normalized values for value-based operators; permit null/blank operators without values.
- **Rationale**: Prevents ambiguous execution and enforces predictable behavior.
- **Alternatives considered**:
  - Auto-convert empty input to wildcard behavior: rejected due to implicit behavior risks and operator ambiguity.

## Decision 5: Output consistency contract

- **Decision**: Local report artifact and standard export output must represent identical matched datasets and summary counts for the same run.
- **Rationale**: Downstream users consume both artifacts; count mismatch would break trust and auditability.
- **Alternatives considered**:
  - Allow independent rendering pipelines with minor count drift: rejected as unacceptable for operations reporting.

## Decision 6: Integration pattern

- **Decision**: Implement as a new read-only menu operation using existing MistHelper patterns (`ConfigUtils`, API retrieval utilities, `DataExporter.write_with_format_selection`).
- **Rationale**: Reduces risk and keeps behavior consistent with existing org-wide export operations.
- **Alternatives considered**:
  - Standalone script path under `scripts/`: rejected because requirement is explicit menu integration.

## Result

All technical-context uncertainties are resolved without remaining `NEEDS CLARIFICATION` placeholders. The feature is ready for task generation.
