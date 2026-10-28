# Zone Summary Boundary Review

## Decision

Require a dictionary when a nonempty zone analysis reaches `_display_zone_section`.
Preserve an explicitly empty dictionary and the empty-analysis return.

## Rationale

The historical assessment identifies the default at line 251 as a candidate.
The current `_build_zone_analysis_result` always provides `zone_count_stats`.
Its absence therefore indicates an incomplete analysis, not a measured zero.

The current display converts that absence to `{}`.
The header then prints zero sites, and later sections claim no missing zones or deviations.
A direct local reproduction confirms this false report.

## Alternatives Considered

- Changing every candidate would exceed the requested single repair and alter intentional defaults.
- Validating optional configuration fields would change their documented absence behavior.
- Requiring every statistics member would expand this boundary beyond the reviewed missing dictionary.
- Repairing exported identifiers would enter the separately owned resource-identifier scope.

## Ownership

The source has no open pull request overlap.
The prior test owner released the scoped addition.
Their existing commit remains preserved on its branch.
