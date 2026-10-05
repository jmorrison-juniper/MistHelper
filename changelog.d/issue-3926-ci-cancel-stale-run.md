### A new push stops the older quality gate run

- **Fixed**: A force-push to a pull request now stops the older Quality Gates
  run. Each job that ran after a failed gate used `always()`, and GitHub Actions
  does not cancel such a job. These jobs now use `!cancelled()`. Issue #3926.
