### Stop VPN creation when inventory is incomplete

- **Fixed**: The WAN VPN builder stops on unreadable VPN records, invalid pagination headers, repeated page links, or SDK error payloads. A valid single-page or empty inventory remains usable. Issue #4792.
