### Say that the portal hardware action needs the shell unlock

- **Fixed**: The operator guide and the web portal wiki page now say that the Multi Site action **Collect EX hardware inventory** needs `PORTAL_WS_ENABLE_SHELL=true`. With the default, **Preview targets** answers HTTP 403 and `This stream is locked by the portal settings.` The guide gives the two steps of the fix and the warning that the setting also unlocks the free-form remote shell. Menu 309 in the CLI needs no setting. Issue #4938.
