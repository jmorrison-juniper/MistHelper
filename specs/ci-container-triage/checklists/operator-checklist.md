Operator Verification & Rollback Checklist — CI Container Build

Purpose: Steps for operators to verify CI fix and rollback if needed.

Verification steps

1) Pre-checks (before running workflow)
   - Confirm repository Settings -> Actions -> Workflow permissions: "Read and write permissions" or that packages: write is allowed.
   - Confirm whether GHCR_TOKEN secret exists and is up-to-date (do NOT rotate here).

2) Trigger build
   - Create a test branch with workflow patch (or use provided feature branch) and push
   - Trigger workflow via GitHub UI using workflow_dispatch

3) Monitor run
   - Watch the following steps closely:
     - "Checking registry credentials..." (diagnostic)
     - Docker login step output (should say which token source used)
     - Build attempts (shows attempt 1..N)
   - Capture logs for "docker buildx" output and login output

4) Validate published images
   - On success, confirm images were published to GHCR by checking packages in GitHub or via `crane ls ghcr.io/<owner>/<repo>` (or docker pull)
   - Confirm tags: generated version and latest

5) Post-checks
   - Merge patch to main if verified
   - Document changes in release notes or CI maintenance notes

Rollback procedure

1) Quick revert (recommended if merged recently)
   - Use GitHub to revert the merge commit that updated .github/workflows/container-build.yml
   - Alternatively, push a branch that restores the previous workflow file and open an emergency PR

2) If revert is not possible immediately
   - Disable the workflow file temporarily by renaming the workflow or adding `if: false` to job definitions (make sure to coordinate with team)
   - Communicate to stakeholders that automated container publishing is temporarily suspended and manual release steps are required

3) Post-rollback verification
   - Ensure that workflow runs no longer attempt publishes until fix is re-applied
   - Validate that other CI jobs are unaffected

Notes
- Do NOT rotate or replace secrets during triage. If secrets are invalid, document who (owner) must rotate them and provide steps to do so outside this triage.
- Keep operator communications clear: provide run IDs, timestamps, and diagnostic logs when requesting help from repository or org admins.
