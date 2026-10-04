# Implementation Plan: SSR registration commands

**Branch**: `feat/3568-ssr-registration-commands`  
**Spec**: `specs/3568-ssr-registration-commands/spec.md`  
**Issue**: #3568

## Summary

Add menu 288 as a deferred wiring entry for an operation class named `SsrRegistrationCommands`. The operation reads the organization SSR registration commands, prints them to the console, and asks before it writes `data/SsrRegistrationCommands.txt`.

## Technical Context

- Language: Python 3.13.
- Mist API operation: `getOrg128TRegistrationCommands`.
- SDK status: The installed `mistapi` package has no helper for this operation, so the client will use `apisession.mist_get`.
- Package: `src/mist/resources/gateway/ssr_registration/`.
- Tests: `tests/unit/gateway/ssr_registration/`.
- Output file: `data/SsrRegistrationCommands.txt`.

## Design

Create a small package with three modules.

1. `client.py` reads `/api/v1/orgs/{org_id}/128routers/register_cmd` and returns the Mist response.
2. `model.py` normalizes the response shape and formats the printable command text.
3. `operation.py` resolves the active organization, prints the command text, prompts for the guarded write, and handles non-2xx responses.

## Safety Rules

- Print the command text to the console because the menu exists for the operator to read it.
- Never log the command text or the registration code.
- Log only the destination file path after a write.
- Exit cleanly on non-2xx responses.

## Deferred Wiring

The integration pull request must update `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, generated menu documentation, and any top-level operation count. This feature branch records the exact changes in `specs/3568-ssr-registration-commands/wiring.md` only.

## Validation

Run the contract gates against the new package and tests before each implementation commit. Run `vulture` and `interrogate` before the final commit.
