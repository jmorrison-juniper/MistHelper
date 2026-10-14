# Implementation Plan: Organization Auto-Upgrade Policy

**Branch**: `jmorrison-juniper-org-auto-upgrade-settings` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: [Feature specification](spec.md). Issue #4217.

## Summary

Add destructive menu 305 to set organization firmware standards and remove all supported site overrides.
Reuse the existing MSP selectors and AP version display logic where their contracts are suitable.
Require `CONFIGURE` after a complete preview. Perform only SDK settings writes, followed by read-back verification.
Save the organization policy before clearing overrides, so no site inherits a policy that failed to save.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: mistapi 0.64.x and existing CLI input helpers.

**Storage**: Complete JSON settings backups in a private ignored subdirectory under `data/`.

**Testing**: pytest unit, contract, integration, menu guard, and Playwright browser tests with mocked SDK responses.

**Target Platform**: Windows, macOS, Linux, and the existing Podman image.

**Project Type**: CLI menu operation and a Flask operations-portal workflow.

**Performance Goals**: Sequential, bounded requests. Read each organization's full site list before any write.

**Constraints**: No upgrade, reboot, restore, clear-pending-version, or device-push call. No real Mist mutation during development.

**Scale/Scope**: Selected organizations, all their sites, and AP, switch, SSR, and SRX policy types.

## Constitution Check

- Use SDK REST methods only. No owned HTTP or WebSocket transport.
- Use typed confirmation and a destructive registry category with a `DESTRUCTIVE` skip reason.
- Validate settings, UUIDs, model names, available versions, enabled flags, and AP schedule.
- Keep dry run read-only. Stop after the first failed update in an organization and report partial completion.
- Preserve sibling settings when replacing a nested settings object.
- Log action names, identifiers, status codes, and counts. Never log settings bodies that can contain credentials.
- Add a new package as the fifth child of `src/operations/execution/`.
- Do not add a child to the existing over-limit firmware package.
- Save and verify every selected organization and site backup before the first settings write.
- Deny backup paths in the generic portal data browser and output scanner.
- Provide menu 305 through a dedicated protected portal workflow. Keep the generic safe-operation gate unchanged.
- Keep the specification root at five children: spec, plan, tasks, checklist folder, and design folder.
- Existing process-folder debt remains unchanged. Incremental remediation remains issue #3824, outside this feature.
- Update only owned menu references and one issue-specific release fragment.
- Use a Conventional Commit and a templated pull request with `Closes #4217`.
- No product output is needed. Store temporary evidence in the session artifact folder or ignored `test-artifacts/`.

## Project Structure

### Documentation (this feature)

```text
4168-org-auto-upgrade-policy/
  spec.md
  plan.md
  tasks.md
  checklists/requirements.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/settings.md
```

### Source Code (repository root)

```text
src/operations/execution/firmware_policy/
tests/unit/firmware_policy/
tests/contract/firmware_policy/
tests/integration/firmware_policy/
tests/e2e/web_portal/test_firmware_policy.py
web_portal/routes/firmware_policy/__init__.py
web_portal/routes/firmware_policy/templates/firmware_policy.html
web_portal/static/js/firmware-policy.js
MistHelper.py
src/foundation/support/utils/operation_registry.py
documentation/org-auto-upgrade-policy.md
changelog.d/issue-4217-org-auto-upgrade-settings.md
```

**Structure Decision**: Use a separate bounded package for settings-only behavior. Do not call an upgrade workflow.
Existing menu 168 remains available and retains its behavior.
Reuse its selection helpers, not its apply or confirmation code.
Use five modules: `sdk.py`, `changes.py`, `backup.py`, `workflow.py`, and `cli.py`.
The portal and CLI share the same backup and verified-write workflow.
The new blueprint owns its template, so the existing five-template folder gains no child.

## Complexity Tracking

The existing entry point and firmware package exceed the structural limits.
Make only the menu registration and required import changes in the entry point.
The new package must not increase existing nested-package excess.
No compatibility shim or new quality exclusion is permitted.
