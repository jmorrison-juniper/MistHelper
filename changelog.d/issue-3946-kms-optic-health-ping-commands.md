### NOC runbooks: SSR optic command and Mist cloud path test

- **Fixed**: The SSR runbooks now put the `name` keyword in each
  `show device-interface name <name> ...` command. The optic check gives the
  7.1.0 limit of `optics-statistics`, a procedure for SSR 7.0.x, and a caution
  for the optic of article I95-65908. Issue #3946.
- **Added**: Step D7 of `SSR_CONSOLE_HEALTH_CHECK.md` tests the path from the
  router to the Mist cloud with `show mist detail`. A procedure gives the DNS
  rule and the firewall rule for TCP port 443, and it tells why an ICMP ping is
  not proof. Issue #3946.
