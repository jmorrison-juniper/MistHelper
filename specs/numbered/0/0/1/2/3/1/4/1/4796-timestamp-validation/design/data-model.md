# Data model: Timestamp validation

A timestamp label contains a UTC date, a six-digit time, and a feature name.
The date must be 1970 or later and the time must be between `000000` and `235959`.
A valid label maps to its existing fixed-width base-5 route.
An invalid label has no destination.
