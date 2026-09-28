# Implementation Plan: Repair Work In Progress portal rows

## Root Cause
`CATEGORY_RANGES` classified menu numbers 63 through 65 as `Work In Progress`. The three handlers now implement real site exports. Menu 63 calls `PromptUtils.select_site()` and then `PromptUtils.select_device_id_from_inventory(site_id, device_type="switch")`, but the registry declared only the site answer.

## Design
- Add category overrides for menus 63, 64, and 65 to `Site Data Exports`.
- Move menu 63 from the site-only registry list to an explicit site plus switch entry.
- Extend the existing prompt-order guard for menu 63.
- Add a category guard that the shipped menu has no `Work In Progress` rows.

## Risks
Menu 63 can still have no switch for a selected site. The existing dependent device selector shows the server reason and keeps Run disabled until a valid switch exists.
