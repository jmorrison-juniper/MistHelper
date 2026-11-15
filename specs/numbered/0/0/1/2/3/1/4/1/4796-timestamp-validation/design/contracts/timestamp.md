# Timestamp route contract

`Resolve-SpecFeaturePath` accepts valid UTC timestamp labels and returns the existing managed route.
The resolver rejects invalid labels without creating a destination.
The parser must not accept a date or time that differs from the original label after parsing.
