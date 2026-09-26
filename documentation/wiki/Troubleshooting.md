# Troubleshooting

## Quick Reference

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Empty CSV | Missing `org_id` or expired token | Verify `.env`, then run the operation again |
| Slow runs / many 429s | Hitting rate limits | Space requests, enable `--fast`, avoid heavy options concurrently |
| SQLite table missing | First run not completed or permission issue | Run again with `--output-format sqlite` and check write access on `data/` |
| SSH runner fails | Missing `paramiko` or credentials | Ensure `paramiko` is installed, and add SSH variables to `.env` |
| Endpoint explorer fails | Endpoint schema drift | Review the endpoint row in the menu API endpoint map |
| SSH connection refused | Container not running | Check `podman ps`, restart container with SSH enabled |
| SSH wrong password | Using incorrect credentials | Default password is `misthelper123!` |
| SSH session won't start | ForceCommand or session issues | Check container logs, verify SSH server is running |
| SSH port conflict | Port 2200 already in use | Stop other services on port 2200 or modify container config. A test container must never publish 2200. See [Container Setup](Container-Setup#test-and-debug-containers). |
| Multiple SSH sessions interfere | Session isolation problem | Each connection should get a unique session ID. Check the logs |
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

1. Run with `--debug` and reproduce the issue.
2. Inspect `data/script.log`. Search for the failing menu ID.
3. Confirm token validity by running menu 11.
4. Try the other output backend, `--output-format csv` or `--output-format sqlite`.
5. Open an issue with the log excerpt. Redact identifiers if your policy requires it.

See also: [SSH Remote Access Troubleshooting](SSH-Remote-Access#troubleshooting) for container-specific issues.
