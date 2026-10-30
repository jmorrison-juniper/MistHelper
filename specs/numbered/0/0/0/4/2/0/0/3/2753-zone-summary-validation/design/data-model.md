# Zone Summary Input

## Zone Analysis

An empty analysis means no zone section is available.
The display returns without printing that section.

A nonempty analysis requires the `zone_count_stats` dictionary.
Other analysis fields retain their existing optional behavior.

## Statistics

The normal builder supplies site counts, mean, median, range, and standard deviation.
This repair checks the dictionary boundary only.
It preserves the established treatment of individual statistics members.

## Failure

Missing, null, and non-dictionary statistics produce `ValueError`.
The error log and exception name `zone_count_stats` and `_display_zone_section`.
Neither includes the rejected value.
The display emits no zone summary before this decision.
