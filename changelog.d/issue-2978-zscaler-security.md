### Fixed

- The Zscaler probe now accepts only `google.com` and its subdomains when it
  applies the Google captive-portal label. The old check used
  `fqdn.endswith("google.com")`, which also accepted `notgoogle.com` and
  `evilgoogle.com`. The new check also accepts an absolute name that carries a
  trailing dot, which the old check rejected. See issue #2978.

### Security

- Every Zscaler probe connection now sets a TLS 1.2 floor through one shared
  context builder. The code no longer relies on the interpreter default, so a
  future build cannot lower the floor without a test failure. See issue #2978.
