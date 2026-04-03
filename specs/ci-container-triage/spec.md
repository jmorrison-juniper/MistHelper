Feature: CI container build triage

Problem statement

The GitHub Actions workflow "Build and Push Container" (/.github/workflows/container-build.yml) is failing on the main branch. The workflow is responsible for building the project Containerfile and publishing images to the GitHub Container Registry (ghcr.io). Failures observed in the workflow (issue #22) report errors during the "Log in to Container Registry" and/or "Build and push container image" steps.

Why this matters

- Container images are required to publish releases and for CI/CD distribution (developer testing, containers for running the app).
- Build failures block automated publishing and make releases manual and error-prone.

Repository evidence

Key workflow excerpts (container-build.yml):
- Registry and image name: env.REGISTRY = ghcr.io, IMAGE_NAME = ${github.repository}
- Login step uses: docker/login-action@v3 with username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }}
- build-push uses docker/build-push-action@v5 with file: ./Containerfile and pushes for platforms linux/amd64,linux/arm64
- Job permissions set: contents: read, packages: write

Container build inputs:
- Containerfile (project root) contains apt-get installs, pip install with --trusted-host and corporate SSL bypass environment variables. The build performs network calls and large dependency installs which can fail on ephemeral runners.

Probable causes

1) Registry authentication/permissions
   - GITHUB_TOKEN may not have package write permission for ghcr.io depending on repository or org settings. Even with job-level packages: write, organization policy can restrict package publishing with GITHUB_TOKEN.
   - docker/login-action may fail silently if the token is invalid or rate-limited.

2) Missing or misconfigured secrets
   - The workflow relies on secrets.GITHUB_TOKEN; some repositories prefer using a Personal Access Token (PAT) stored in secrets like GHCR_TOKEN for registry login. If a PAT was expected but missing, login will fail.

3) Runner environment / network timeouts
   - The Containerfile runs apt-get and pip installs that reach out to external networks. Corporate network, intermittent DNS, or runner transient failures can cause timeouts that look like build failures.

4) Buildx / QEMU multi-arch setup failures
   - The workflow uses setup-qemu and setup-buildx; if those steps misconfigure or the runner cannot set up binfmt/qemu, buildx may fail pushing multi-arch images.

5) Containerfile issues
   - Long-running RUN steps or commands that require root but switch users may cause failures.
   - Environment variables disabling SSL verification might be needed during build but could cause pip failures if not set at build time.

6) Docker metadata and tags formatting
   - docker/metadata-action outputs may produce tag strings that are incompatible with build-push inputs if malformed.

Recommended immediate fixes (minimal & testable)

1) Add an explicit registry-auth validation step before trying to login/push and prefer an explicit PAT if present. Example logic:
   - If secrets.GHCR_TOKEN exists, use it for docker/login-action (username: "${{ github.actor }}", password: ${{ secrets.GHCR_TOKEN }})
   - Else fall back to GITHUB_TOKEN but fail early with clear guidance if login fails

2) Improve the workflow to surface helpful errors and avoid silent failures:
   - Add a diagnostic step that prints which token source will be used (do not print token values)
   - Add retry wrapper around docker/build-push-action for transient network failures

3) Make build more robust on runners:
   - Break long RUN chains in Containerfile into smaller steps to improve caching and speed
   - Pin apt-get and pip operations where possible and reduce network calls
   - Add `--progress=plain` and increased verbosity to build step when diagnosing

4) Permissions check guidance:
   - Document and verify that repository/org allows GITHUB_TOKEN to write packages to GHCR. If not allowed, add documentation to use a PAT in secrets and update workflow to use it.

5) Local repro instructions (for maintainers):
   - Reproduce build locally using buildx: docker buildx create --use && docker buildx build --platform linux/amd64,linux/arm64 -f Containerfile --tag test/misthelper:local --load .
   - Validate registry login locally: echo ${PAT} | docker login ghcr.io -u <username> --password-stdin

Assumptions

- We have access to view the workflow file and Containerfile, but not the runner logs for the failing run in this triage. The issue description indicates failures in the login/build steps.
- We will not rotate or change any secrets; only document validation and restoration steps.

User scenarios & testing (acceptance)

- Maintainer can run the modified workflow or manual commands and see an explicit diagnostic if registry auth is missing or insufficient.
- With a valid PAT in secrets (GHCR_TOKEN), the workflow should authenticate and publish images.
- Local build reproduces the failure (or passes) and the diagnostics help identify network vs auth failures.

Functional requirements (testable)

1) Workflow must fail with a clear, actionable error if registry authentication is invalid or missing. (Test: run with no GHCR_TOKEN and with limited GITHUB_TOKEN permissions -> expect clear error)
2) Workflow must attempt to use secrets.GHCR_TOKEN when present. (Test: create secret GHCR_TOKEN and verify the login step uses it)
3) Build step should be resilient to transient network failures (simple retry). (Test: simulate transient failure and confirm a retry occurs)
4) Local reproduction instructions must allow maintainer to build and test without workflow execution. (Test: run provided docker buildx commands locally)

Success criteria

- CI job completes the Build and Push Container job on main when provided valid registry credentials (GITHUB_TOKEN or GHCR_TOKEN) and healthy runner/network.
- Diagnostic messages allow a maintainer to distinguish auth vs network vs Containerfile issues within one run.

Deliverables

- This spec and an ordered tasks list (specs/ci-container-triage/tasks.md)
- An operator verification checklist (specs/ci-container-triage/checklists/requirements.md)
- A minimal patch suggestion (specs/ci-container-triage/patch.diff) that adds registry credential selection and pre-checks to the workflow

Next: implement the minimal workflow patch that checks for GHCR_TOKEN and adds a clear diagnostic + retry wrapper around the build-push step.

Status: SUCCESS (spec ready for planning)
