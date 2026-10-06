### Portal accent button fill in the hover state and in the disabled state

- **Fixed**: `.btn-accent` now sets `--bs-btn-bg`, `--bs-btn-hover-bg`,
  `--bs-btn-active-bg`, `--bs-btn-disabled-bg`, and the matching border
  variables to the portal accent. Bootstrap 5.3.3 draws the hover state and the
  disabled state from those variables, so the button kept the accent fill in
  each state. Issue #3658.
- **Removed**: The scoped copy `.ws-page .btn-accent` in the WebSocket
  stylesheet. The shared rule now holds every accent state. Issue #3658.
