### Native compose provider for new worktrees

- **Fixed**: The bootstrap installs `podman-compose==1.6.0` for `scripts/compose.ps1` in each new worktree.
  The existing missing-provider error remains unchanged. Issue #3398.
