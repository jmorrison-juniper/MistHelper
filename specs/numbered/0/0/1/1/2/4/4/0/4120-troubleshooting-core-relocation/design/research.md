# Relocation decisions

## Menu test support

**Decision**: Use `src/foundation/support/menu_testing/`.

**Rationale**: The runner manages test execution and unattended answers. Foundation support has two children.

**Alternatives considered**: Execution now has five children. A sixth child violates the package guard.

## Marvis troubleshooting

**Decision**: Use `src/mist/intelligence/marvis/troubleshooting/`.

**Rationale**: Both modules implement Marvis behavior. Marvis has two children.

## Catalog contract

**Decision**: Update the active hook catalog only.

**Rationale**: The #4117 contract freezes the inventory at `7c4e57f3db93afda4c93ef0aec1e73c35fb7774e`.

**Alternatives considered**: Regenerating historical evidence would break its revision contract.

## Ownership

Current open PR files do not intersect the required active path edits.
PR #4358 owns the test quality baseline and an older quickstart. This change does not edit either file.
