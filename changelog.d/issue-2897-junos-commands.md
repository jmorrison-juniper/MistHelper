### Fixed

- Corrected four Junos commands in the `hardening-junos` skill for issue #2897. Controls
  NET-08, NET-09, and NET-10 told the reader to build a firewall filter. The Juniper hardening
  book uses one system statement for each case. They now use
  `set system internet-options tcp-drop-synfin-set`, `set system no-ping-record-route` with
  `set system no-ping-time-stamp`, and `set system internet-options no-source-quench`.
- Corrected STIG rule JUEX-L2-000180 for issue #2897. It merged the link fault management
  command and the aggregated link command into one line. The XCCDF file gives them as two
  alternatives, and the rule now states both.
