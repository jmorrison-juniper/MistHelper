# Quickstart: WebSockets tab in the Operations portal

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Run the tests

Run these commands in the worktree, with the virtual environment active.

```powershell
python -m pytest tests/unit/websocket_streams tests/contract/websocket_streams -q
python -m pytest tests/e2e/test_websockets_page.py -q
```

The unit tests and the contract tests open no Mist connection. The browser test starts the portal with a fake engine.

## Run the page on your own machine

1. Put the Mist token and the organization in `.env`, as for the other portal pages.
2. Start the portal on a test port in the range 9600 through 9699.

   ```powershell
   $env:PORT = "9651"
   python -m gunicorn --bind 127.0.0.1:9651 --worker-class gthread --threads 24 --workers 1 wsgi:app
   ```

3. Open `http://127.0.0.1:9651/websockets`.
4. Select a site, then select **Device statistics**, then select **Start**.
5. Read the messages in the session card. Select **Stop** when you are done.

## Check the locks

1. Open the page with no flag set. Each state-changing utility and each shell shows a lock and the flag name.
2. Set `PORTAL_WS_ENABLE_CHANGES=true` and start the portal again. The change utilities now ask for the typed device name.

Warning: A state-changing utility interrupts traffic on a live port or a live client. Set the flag only in a lab, or with a change window.

## Stop the portal

Press `Ctrl+C` in the Gunicorn window. The portal closes every Mist connection when it stops.
