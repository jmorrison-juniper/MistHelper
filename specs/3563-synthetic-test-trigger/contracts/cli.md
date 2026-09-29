# CLI Contract: Synthetic Test Trigger

## Menu

- Menu number: `283`.
- Category: `interactive`.
- Handler: `SyntheticTestTrigger.run`.
- Integration file changes: deferred to `wiring.md`.

## Prompts

1. Site selection uses `PromptUtils.select_site_with_logging`.
2. Scope prompt accepts `1` for site, `2` for device, and `3` for RADIUS from one switch.
3. Device selection uses `PromptUtils.select_device_id_from_inventory`.
4. Test parameter prompts depend on the selected scope.
5. Confirmation accepts `y` only. Any other value cancels the trigger.

## Output

The operation writes `SyntheticTestTrigger.csv` through the shared export path. The file contains the request summary and the result. It never contains the RADIUS password.

## Timeout

The poll stops after `SYNTHETIC_TEST_TIMEOUT_SECONDS`. The default is `120` seconds.
