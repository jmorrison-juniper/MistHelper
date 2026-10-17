# Data Model: Generated Operations control labels

## Existing Parameter

The parameter keeps its name, label, type, required flag, default, options, and dependency metadata.
No parameter field or server contract changes.

## Label and Control

The label's `for` attribute equals the control's existing `id`.
The label and control remain siblings in the existing parameter group.
Required markers and form classes remain unchanged.

## Replacement

An endpoint change removes the old dynamic groups and creates new groups through the same builder.
Each replacement label references its replacement control.
