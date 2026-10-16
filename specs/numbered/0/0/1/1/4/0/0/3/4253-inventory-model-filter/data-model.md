# Data model

Inventory rows contain a nonblank `model` and `type`.
Recognized policy hardware types are `ap`, `switch`, and `gateway`.
Gateway inventory matches only the existing SSR or SRX catalog group.
Compare case-insensitive model names, but return the exact supported catalog spelling.
Duplicate inventory rows produce one display choice.

The display catalog retains the existing nested device-type, model, and version structure.
An empty inventory produces empty model maps, never a full supported catalog.
Inventory rows with invalid model or type values fail the display request.

The explicit boolean `show_all` bypasses inventory filtering, not compatibility checks.
Changing this boolean invalidates graphical selections and prepared readiness.
