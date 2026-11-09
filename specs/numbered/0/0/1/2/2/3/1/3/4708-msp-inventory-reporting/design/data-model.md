# Data Model

Existing organization results retain `safe_org`, `model_rows`, `version_rows`, and `ver_per_model`.
The repair changes no exported fields.

The batch coverage calculation uses the input count and the collected-result count.
The excluded count is their difference.
A console label identifies complete or partial coverage.
The label is not an export row, field, or filename component.
