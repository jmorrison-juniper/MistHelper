CI Container Triage — Tasks

Ordered tasks (investigate → remediate → verify)

1) Gather failing run logs
   - Action: Open the failing workflow run in GitHub Actions and capture full logs for the following steps:
     - "Log in to Container Registry"
     - "Build and push container image"
     - Any step reporting Docker/buildx/qemu errors
   - Goal: Identify whether the failure is auth (401/403), network timeout, buildx error, or pip/apt failure
   - Commands: Use GitHub UI; `gh` CLI: `gh run view --repo jmorrison-juniper/MistHelper <run-id> --log` (optional)

2) Validate repository & org permissions
   - Action: Check repo Settings → Actions → General → Workflow permissions to confirm GITHUB_TOKEN has package write. Check organization policy for package publishing.
   - Goal: Confirm whether GITHUB_TOKEN can push to ghcr.io
   - Deliverable: Note whether packages: write is allowed

3) Validate secrets used by workflow
   - Action: In repo Settings → Secrets, check for GHCR_TOKEN or other registry tokens. Confirm presence/absence and intended use.
   - Goal: Determine whether workflow should use a PAT (GHCR_TOKEN) instead of GITHUB_TOKEN
   - Note: Do NOT rotate or change secrets here; only document status

4) Reproduce build locally
   - Action: Try building locally with buildx to isolate network vs auth issues
   - Commands:
     - docker buildx create --use --name localbuilder || true
     - docker buildx inspect --bootstrap
     - docker buildx build --platform linux/amd64,linux/arm64 -f Containerfile --tag local/misthelper:debug --load .
     - If pushing to GHCR for test, create a local PAT and test: echo ${PAT} | docker login ghcr.io -u <username> --password-stdin
   - Goal: Reproduce failure and collect stdout/stderr

5) Add workflow diagnostic + auth fallback (minimal patch)
   - Action: Modify .github/workflows/container-build.yml to add a step that chooses the token source and validates login. If secrets.GHCR_TOKEN is present, use it; otherwise use GITHUB_TOKEN. Add a small script step to attempt `docker login` and fail with a helpful message.
   - Goal: Provide clearer failures and allow maintainers to choose PAT when necessary
   - Patch: specs/ci-container-triage/patch.diff (draft)

6) Add retry for build-push
   - Action: Wrap build-push-action with a retry for transient failures (3 retries, backoff). If the action doesn't support retries directly, add a shell loop to re-run the action or use job-level retry strategies with `timeout-minutes` and step retry where available.
   - Goal: Reduce flakes from transient network/QEMU failures

7) Test workflow changes in a feature branch
   - Action: Create a short-lived branch and push workflow changes; trigger workflow via workflow_dispatch and monitor logs
   - Goal: Confirm improved diagnostics and successful build/push when valid credentials are provided

8) If build still fails, instrument Containerfile
   - Action: Add temporary verbose flags to pip/apt steps, break long RUN chains, and add caching hints. Re-run local builds & CI.
   - Goal: Isolate failing layer and remediate (pin package versions, add --no-cache-dir, adjust SSL trusts)

9) Create PR with minimal change and clear description
   - Action: Open a PR with the patch that adds auth selection/diagnostics and retry logic. Include instructions for maintainers to add GHCR_TOKEN if GITHUB_TOKEN is disallowed by org policy.
   - Goal: Get review and merge

10) Operator verification and rollback plan
   - Action: After merge, run workflow on main, monitor, and if failure detected roll back by reverting the workflow change
   - Goal: Reduce downtime and enable quick rollback

Notes
- Keep changes minimal: prefer adding diagnostic steps and fallback to PAT over changing how images are pushed.
- Do not rotate or change any secrets as part of triage.
