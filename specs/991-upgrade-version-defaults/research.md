# Research: Per-Type Upgrade Version Defaults

## Decision: Use returned model availability as the only target source

**Rationale:** `read_model_versions` already reads the version data that the
portal shows. The selector can use that typed map and never create a version.

**Alternatives considered:** A static release catalog could supply more names.
It cannot prove that every current device offers a target, so the plan rejects
it.

## Decision: Select from an intersection for each device type

**Rationale:** Every eligible device of a type must offer the selected version.
The selector will intersect normalized returned values before it ranks a
candidate.

**Alternatives considered:** A union permits a value that some devices cannot
install. Per-model selection does not meet the shared type default requirement.

## Decision: Validate against a second current read on save

**Rationale:** Inventory and offered versions can change after the page loads.
The existing `build_options_record` already reads inventory at the save
boundary. It will also read current availability before it builds targets.

**Alternatives considered:** Trusting the browser body permits tampering and
stale values. Validating only on the page read does not protect persistence.

## Decision: Keep the existing target body and confirmation boundary

**Rationale:** The current browser body holds individual `mac` and
`version_target` entries. Per-type controls can populate those existing rows.
The `save_options` route only saves a record, while the confirmation path owns
the upgrade start.

**Alternatives considered:** A new type-target API shape would require a wider
public interface change. Starting an upgrade during save violates the safety
requirement.

## Decision: Use type-specific environment variables

**Rationale:** The approved names isolate operational choices by device type:
`CAPTURE_DEFAULT_AP_VERSION`, `CAPTURE_DEFAULT_SWITCH_VERSION`, and
`CAPTURE_DEFAULT_GATEWAY_VERSION`.

**Alternatives considered:** One global setting cannot represent independent
type compatibility. Per-device or per-model settings exceed the feature scope.
