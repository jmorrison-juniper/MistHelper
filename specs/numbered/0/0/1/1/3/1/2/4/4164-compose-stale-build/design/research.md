# Research: Prevent Unsafe Stale Builds

## Decision 1: Compare the checkout with a freshly fetched main branch

**Decision**: Fetch `origin/main` with an explicit refspec before a local image build. Count commits in `HEAD..origin/main`.

**Rationale**: The current helper does not compare the checkout with the remote branch. The explicit refspec updates the exact remote-tracking reference used for the count.

**Alternatives considered**:

- Read the existing `origin/main` reference without fetching. This can report an old count.
- Compare the running container revision. That reports the image revision, not whether the build source is stale.

## Decision 2: Keep stale images separate from the published image

**Decision**: Pass the selected image name through a temporary environment variable to the build overlay. Use `misthelper:local` only when an operator permits a stale build.

**Rationale**: The deployment guide already uses `misthelper:local` for local images. A scoped environment value avoids a second Compose file and does not change the published name for current builds.

**Alternatives considered**:

- Always use the local image name. This changes the existing current-checkout build behavior.
- Add a second stale-build overlay. This adds a file and another compose-file ordering rule.

## Decision 3: Keep validation independent of a live container runtime

**Decision**: Extend the existing contract tests and use a temporary Git repository to prove the behind-count direction. Do not start a container or publish an image.

**Rationale**: The contract tests already validate the compose helper without a container. This change only needs Git revision evidence and source contracts.

**Alternatives considered**:

- Build a real image in local tests. This adds network, container, and image-tag side effects that the contract does not require.
- Add PowerShell as a CI dependency. The existing workflow runs on Ubuntu and does not install PowerShell. The test module can guard the script contract without changing workflow infrastructure.

## Environment limitation

The local worktree has no `pwsh` executable. The repository setup-plan script cannot run on this host. The feature directory and plan use the selected managed route and the checked-in plan template.
