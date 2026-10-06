# Implementation Plan: Specs Intake Routing

## Technical approach

1. Add the PowerShell route helper.
2. Make `create-new-feature.ps1` use the helper.
3. Add the readable legacy baseline and migration-aware guard.
4. Add Python tests for the route and guard failure paths.
5. Update the constitution and MistHelper instructions.
6. Store this numeric feature at
   `specs/numbered/0/0/1/1/0/0/0/0/3750-spec-intake-routing/`.
7. Keep timestamp features under `specs/live/`.

## Data and safety

The baseline lists the current direct `specs/` entries except `skills`.
The guard allows the managed roots `numbered`, `live`, `skills`, and `indexes`.
The phase records use the numeric route for feature 3750.

## Validation

Run the scoped guard tests, the changelog guidance guard, the Markdown link
guard, Ruff, Black, mypy, the STE linter, and the symbol check.
