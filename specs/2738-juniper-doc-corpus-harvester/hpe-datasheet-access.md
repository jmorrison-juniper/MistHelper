# HPE datasheet access

HPE now hosts the Juniper datasheets. A datasheet URL on `www.juniper.net`
answers with an HTTP 301 redirect to `www.hpe.com/psnow/doc/...`. This network
permits `www.juniper.net`, and it blocks `www.hpe.com`.

## The measured finding

A measurement on 2026-09-16 tried the HPE host three times with a 15-second
timeout. Each try gave the same result. DNS resolved `www.hpe.com` in under
0.1 second. The TCP connection to port 443 opened in under 0.1 second. The
HTTPS read never returned, and it timed out at 15 seconds. The host accepts the
connection and then sends no response. A short connect timeout does not help,
because the read is the part that hangs.

## The affected URLs

77 datasheet URLs redirect to the blocked HPE host. 30 URLs sit under
`/content/dam/www/assets/datasheets/`. 47 URLs sit under
`/assets/us/en/local/pdf/`.

## What an operator must do

Run the harvest from a network that permits `www.hpe.com`, such as a home
network or a mobile hotspot. From such a network, the 77 datasheets download
normally. The harvester now detects the blocked host. After 3 no-response
failures on one host, it marks the host unreachable, fails the rest of that
host's URLs at once, and names the host in the failure reason. One blocked host
no longer stalls the whole run.
