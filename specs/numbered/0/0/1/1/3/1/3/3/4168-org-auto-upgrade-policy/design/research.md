# Research: Organization Firmware Standards

## Settings endpoint and supported fields

**Decision**: Use `updateOrgSettings` at `PUT /api/v1/orgs/{org_id}/setting`.

**Rationale**: The repository OpenAPI schema defines `auto_upgrade`, `switch.auto_upgrade`, `ssr.auto_upgrade`, and `juniper_srx.auto_upgrade`.
Each policy accepts a model-to-version map named `custom_versions`.
Only AP policies define `day_of_week` and `time_of_day`.
SSR and SRX policies apply when a device is first onboarded.

**Alternatives considered**: Upgrade endpoints start device changes and do not satisfy this feature.

## Site override removal

**Decision**: Remove the AP field with the Mist unset marker `{"-auto_upgrade": ""}`.
For switch, SSR, and SRX, replace the complete parent object after removing its `auto_upgrade` member.
Retain every sibling member, including unshown sensitive values, in memory and private verified backups only.
Read settings again and refuse success if a local override remains.

**Rationale**: The Juniper Terraform provider sends `unset["-auto_upgrade"] = ""` when the local AP policy is absent.
Its nested SSR conversion omits `auto_upgrade` while retaining the parent object.
This agrees with Mist object replacement behavior.

**Sources**:

- [AP unset prior art](https://github.com/Juniper/terraform-provider-mist/blob/640257310b9b7dfedcd7f79c9403283407b9d1ce/internal/resource_site_setting/terraform_to_sdk.go)
- [Nested SSR settings prior art](https://github.com/Juniper/terraform-provider-mist/blob/640257310b9b7dfedcd7f79c9403283407b9d1ce/internal/resource_site_setting/terraform_to_sdk_ssr.go)
- Repository schema: `documentation/mist-api-openapi31json.json`, `site_setting` and related components.

**Alternatives considered**: Setting `enabled` to false creates a local disabled policy rather than inheritance.
Setting an empty map or sending `null` does not establish removal semantics.
Omitting a top-level field from a partial update leaves it unchanged.

## Update sequence and safety

**Decision**: Read every selected organization's settings and sites before confirmation.
Write and verify its organization policy before clearing each site's overrides.
Do not submit automatic rollback or retry writes after an ambiguous failure.

**Rationale**: Clearing sites first can expose them to the old organization policy.
An explicit report identifies completed work and remaining sites after any partial failure.
Enabled policy changes can cause later cloud-managed upgrades. The preview must state this.

**Alternatives considered**: Clearing first follows the literal job order but is unsafe.
An upgrade request or scheduled upgrade job violates the user constraint.

## Existing selection flow

**Decision**: Reuse menu 168's injected MSP and organization selectors and AP model-version presentation when suitable.
Prompt for explicit enabled state and require `CONFIGURE` rather than menu 168's yes/no confirmation.

**Rationale**: The user requested familiar flow without borrowing firmware execution.
Use per-model selection for all supported hardware types.
Read SSR versions from its dedicated SDK endpoint and obtain actual models from inventory when versions lack a model field.

**Alternatives considered**: Calling menu 168's complete workflow changes local policies and cannot set the organization policy.

## Tooling

**Decision**: Keep the app-managed branch and existing core template.

**Rationale**: The branch hook refused its shell script. PowerShell is absent.
No project template overrides or presets exist. The resolved core template is already available.
The worktree bootstrap installed the pinned runtime and development requirements.

## Full backup and portal requirements

**Decision**: Save complete organization and site settings, then verify every backup before sending any settings write.
Use a private ignored folder under `data/`, exclusive creation, UTC metadata, content checksums, and parsed read-back equality.
Block that folder in portal file browsing and output discovery.

**Rationale**: The user added mandatory complete backups during implementation.
Policy-only snapshots no longer meet the requirement.
Full settings can contain credentials, so the backup cannot be a downloadable portal output.

**Decision**: Add a dedicated workflow to the existing numbered-menu portal on port 8055.
Keep generic safe-operation execution unchanged.

**Rationale**: This is the only existing portal that runs numbered menus.
The user was unavailable for the portal clarification, so this documented assumption keeps the work moving.
The graphical workflow uses server-side validated preview state and the same backup gate as the CLI.
