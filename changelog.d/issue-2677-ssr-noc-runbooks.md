### SSR NOC runbook command corrections and four new troubleshooting guides

- **Fixed**: Six PCLI commands in the SSR gateway runbooks do not exist in any
  SSR release. `show system connected`, `show route`, `show bgp neighbor` in the
  singular form, `show sessions summary`, `show events filter type`, and
  `ping <target> source <ip>` all fail at the prompt. Every occurrence now names
  the working command. Issue #2677.
- **Added**: `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md` gives a
  seven-stage console triage sequence. Each step states the reason to run the
  command, the healthy output, and the failure signature with the next action.
  Issue #2677.
- **Added**: `documentation/noc-runbooks/SSR_ALARM_INDEX.md` maps every alarm
  that an SSR raises about itself, and every Mist gateway alarm key, to a runbook.
  Each row carries the trigger threshold and the clear threshold. Issue #2677.
- **Added**: `documentation/noc-runbooks/SSR_APPLICATION_PERFORMANCE.md` covers a
  user complaint about an application, which no runbook covered before.
  Issue #2677.
- **Added**: `documentation/noc-runbooks/SSR_EVIDENCE_CAPTURE.md` covers the
  support archive, the packet capture, and the log level, with the cleanup that
  each one needs. Issue #2677.
- **Added**: `documentation/noc-runbooks/SSR_FIRMWARE_HEALTH.md` covers a fault
  that follows a software change. Issue #2677.
- **Added**: `scripts/verify_ssr_commands.py` checks every command in a runbook
  against the vendor command reference, so this defect cannot return unnoticed.
  Issue #2677.
- **Added**: `scripts/fetch_ssr_docs.py` and `scripts/pdf_to_markdown.py` rebuild
  the vendor reference corpus on demand. Issue #2677.
- **Changed**: `.gitignore` excludes `documentation/references/`. That directory
  holds verbatim Juniper Networks documentation, so it follows the same rule as
  the licensed ASD-STE100 source above it. Issue #2677.
