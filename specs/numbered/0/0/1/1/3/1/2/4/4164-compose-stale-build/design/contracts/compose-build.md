# Compose Build Command Contract

## Commands

| Command | Required behavior |
|---|---|
| `.\scripts\compose.ps1 build` | Fetch `origin/main`. Stop if the fetch fails. Stop before the provider when the checkout is behind. Use the published image name when the checkout is not behind. |
| `.\scripts\compose.ps1 build --allow-stale` | Fetch `origin/main`. Permit a stale checkout only for this build. Use `misthelper:local` when the checkout is behind. |

## Safety requirements

- The helper reports the number of missing commits before it stops.
- A failed fetch or revision count prevents the provider call.
- The override does not reach the compose provider.
- The helper restores the prior `MISTHELPER_BUILD_IMAGE` environment value.
- Other compose commands keep their existing argument behavior.

## Validation

The contract tests verify the revision-count direction in a temporary Git repository. They also check that the failure decision precedes the provider call and that documentation uses the guarded helper.
