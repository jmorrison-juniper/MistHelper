### Block container builds from stale checkouts

- **Fixed**: The compose helper stops a build from a checkout behind `main`. The `--allow-stale` flag uses the local-only `misthelper:local` tag. Issue #4164.
