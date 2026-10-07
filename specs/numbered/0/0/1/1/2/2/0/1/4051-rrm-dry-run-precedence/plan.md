# Implementation Plan: RRM Dry-Run Precedence

## Scope

Implement one fail-closed resolver for menu 291. Keep the existing durable
before capture and exact typed confirmation.

## Design

1. Change the operation and registered handler to use `bool | None`.
2. Add mutually exclusive `--dry-run` and `--live-run` CLI modes.
3. Resolve explicit argument, explicit CLI mode, environment, and absence in
   that order.
4. Treat the environment as a one-way dry-run control.
5. Make the fallback `.env` loader preserve process environment values.
6. Add an AST guard for the single protected environment read.

## Verification

Run the focused resolver, operation, registered-path, and guard tests. Then run
the repository lint, format, type, security, complexity, symbol, generation,
and test-quality gates required by the repository.

## Safety

Warning: a live menu 291 request can change the radio plan for a site. Human
review is mandatory. Do not enable auto-merge.
