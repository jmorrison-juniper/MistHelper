# Research: Missing Zone Map Validation

## Decision

Require `sites_missing_common_zones` to be a dictionary before the display helper prints the section.

## Rationale

The producer builds this field from the missing-site analysis and always includes it. A default empty dictionary hides an incomplete result and creates a false reassurance.

## Alternatives Considered

- Keep the empty default. Rejected because missing data then looks complete.
- Broaden the existing issue scan. Rejected because its current scope is comparator device IDs and this slice has a direct behavioral test.
- Change exports or other summary fields. Rejected because they do not affect this display claim.

## Unknowns

None. The producer contract and display behavior are present in the current source.
