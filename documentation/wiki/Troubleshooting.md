# Troubleshooting

## Quick Reference

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Empty CSV | Missing org_id / expired token | Verify `.env`, re-run |
| Slow runs / many 429s | Hitting rate limits | Space requests, enable `--fast`, avoid heavy options concurrently |
| SQLite table missing | First run not completed or permission issue | Re-run with `--output-format sqlite` and check write perms on `data/` |
| SSH runner fails | Missing `paramiko` or creds | Ensure `paramiko` installed; add SSH vars to `.env` |
| WIP export fails | Endpoint schema drift | Treat 63-65 as non-stable; review code before relying |
| SSH connection refused | Container not running | Check `podman ps`, restart container with SSH enabled |
| SSH wrong password | Using incorrect credentials | Default password is `misthelper123!` |
| SSH session won't start | ForceCommand or session issues | Check container logs, verify SSH server is running |
| SSH port conflict | Port 2200 already in use | Stop other services on port 2200 or modify container config |
| Multiple SSH sessions interfering | Session isolation problem | Each connection should get unique session ID -- check logs |
| `script.log` permission error | Data directory not writable | Run `chmod -R 777 data/` on host before starting container |

## Debug Mode

Run with detailed logging for troubleshooting:

```bash
python MistHelper.py -M 11 --debug
```

Debug mode enables detailed table data in logs and verbose API response logging.

## Log File

Check `data/script.log` for runtime logs. Search for the failing menu ID to find relevant error context.

## Support Flow

1. Run with `--debug` and reproduce the issue
2. Inspect `data/script.log` (search for failing menu ID)
3. Confirm token validity (menu 11 success?)
4. Try alternate output backend (`--output-format csv` vs `sqlite`)
5. Open issue with log excerpt (redact org/site/device IDs if required by policy)

See also: [SSH Remote Access Troubleshooting](SSH-Remote-Access#troubleshooting) for container-specific issues.
