# Plan: missing row controls

## Root cause

`web_portal/services/operation.py` did not declare controls for prompts that arrive through injected prompt helpers. The prompt audit cannot see these helper calls.

## Design

Add each site-only row to `site_only_menus`. Move menu 78 to the site-plus-device list so the portal answers the site prompt before the device prompt.

## Risks

- Menu 197 can ask later prompts after the site selection, but issue #3184 only blocks at the missing site control.
- The registry is a shared hot file, so the branch must rebase before push.
