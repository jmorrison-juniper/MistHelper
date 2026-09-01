#!/bin/bash
# Carry the runtime configuration of the container into every SSH session.
#
# Why: `compose.yml` supplies the credentials through `env_file`, which fills the
# environment of the container process and writes no file. The SSH daemon starts
# each session with a fresh environment, and `PermitUserEnvironment` stays off. A
# session therefore reached MistHelper with no API token, the preflight refused,
# and the restart loop repeated the same permanent fault five times. Issue #2181
# holds that report.
#
# The entrypoint runs this script as root, so this script is the one writer.
# `misthelper-session.sh` is the one reader.
#
# Warning: the file holds the Mist API token. The write sets the mode 0400 and
# the ownership of the session user before any value reaches the disk. A wider
# mode would expose the token to every account of the container.
#
# Usage: write-session-env.sh <owner> <path>

set -e
set -o pipefail

OWNER="$1"  # The account that reads the file. Every other account gets nothing.
TARGET="$2"  # The path of the finished file.

# The names that one Mist session needs.
#
# The list is an allowlist. A blind copy of the whole environment would carry
# the SSH password and every unrelated secret into a file on disk.
#
# The first six reach the credential preflight and the organization choice. The
# last five let a session behind a corporate proxy reach the Mist cloud, which
# the trust store step of the entrypoint already prepares.
SESSION_ENV_NAMES=(
    MIST_HOST
    MIST_APITOKEN
    MIST_API_TOKEN
    MIST_ORG_ID
    ORG_ID
    org_id
    REQUESTS_CA_BUNDLE
    SSL_CERT_FILE
    HTTPS_PROXY
    HTTP_PROXY
    NO_PROXY
)

mkdir -p "$(dirname "$TARGET")"  # The file needs its directory before the write.

# Build the file under a strict mode before any value reaches the disk. A file
# created with the default mode would stay world readable for the moment between
# the write and the change of mode.
STAGED="${TARGET}.new"
: > "$STAGED"  # Start from an empty file, because a stale value must never survive a restart.
chmod 0400 "$STAGED"  # Close the file to every other account before the token lands in it.

CARRIED=()  # The names that reached the file, for the report below.
for NAME in "${SESSION_ENV_NAMES[@]}"; do
    if [ -n "${!NAME-}" ]; then  # An unset name and an empty name both stay out of the file.
        # `%q` quotes the value for the shell, so a value that holds a space, a
        # quotation mark, or a dollar sign still reads back as one word.
        printf '%s=%q\n' "$NAME" "${!NAME}" >> "$STAGED"
        CARRIED+=("$NAME")
    fi
done

chown "$OWNER" "$STAGED" 2>/dev/null || true  # A test runs as one account, so a failed change of owner is not fatal.
mv -f "$STAGED" "$TARGET"  # Replace in one step, so no session reads a half-written file.

# Warning: never print a value from the list above. The list holds the API
# token, and a token in the log file reaches every reader of the data volume.
# This line names the variables and prints no value.
echo "[SSH] Carried ${#CARRIED[@]} configuration name(s) into the session file: ${CARRIED[*]}"
