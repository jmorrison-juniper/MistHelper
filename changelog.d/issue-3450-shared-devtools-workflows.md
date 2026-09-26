### Shared devtools workflows

- **Changed**: The Copilot, linked-issue, container build, and release image
  workflows call the shared reusable workflows in `misthelper-devtools` at
  release v0.3.0. `requirements-dev.txt` pins the same release. Issue #3450.
- **Fixed**: A release publishes the container image for `linux/amd64` and
  `linux/arm64`, so the `latest` tag keeps an arm64 image. The scheduled
  linked-issue sweep keeps an issue open when a person reopened it after the
  merge. A failed Copilot assignment writes one comment with the cause and adds
  no `in-progress` label. Issue #3450.