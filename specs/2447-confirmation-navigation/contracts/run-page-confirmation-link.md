# Run-page confirmation-link contract

For `GET /runs/{run_id}`:

- If the run state is `awaiting_confirmation` and a pre-check identifier exists, render one visible link.
- The link MUST have `data-testid="upgrade-confirm-link"`.
- The link MUST target `/runs/{run_id}/confirm`.
- Otherwise, omit the link.
- Following the link MUST leave all confirmation safety checks to the existing confirmation route.
