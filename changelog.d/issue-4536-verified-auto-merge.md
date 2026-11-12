### Verify the auto-merge result

- **Fixed**: The shared merge workflow verifies the pull request state after a merge request fails. It accepts a confirmed merge or an active auto-merge request. An unverified result still fails. Issues #4536 and #4556.
