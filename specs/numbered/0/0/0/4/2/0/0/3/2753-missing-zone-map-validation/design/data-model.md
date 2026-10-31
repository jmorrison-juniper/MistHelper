# Data Model: Missing Zone Map Validation

## Zone Analysis

The analyzer result includes an explicit `sites_missing_common_zones` dictionary. Each key identifies a site. Each value contains the site name and the missing zone names.

## Validation Rules

- The display requires the field to exist and hold a dictionary.
- An empty dictionary means no site lacks a common zone.
- A nonempty dictionary retains its site entries and the existing display cap.
- A missing or non-dictionary value stops the display before it prints a count or a success statement.

## Relationships

The zone-pattern producer creates the zone analysis. The display helper reads the missing-zone dictionary from that result.
