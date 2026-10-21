#!/bin/bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
TEMP_DIR=$(mktemp -d)
trap 'rm -f "$TEMP_DIR/curl" "$TEMP_DIR/sub2api" "$TEMP_DIR/api.log" "$TEMP_DIR/service.log" "$TEMP_DIR/output.log"; rmdir "$TEMP_DIR"' EXIT

# A newly forked repository may not have a published release yet.
cat > "$TEMP_DIR/curl" <<'EOF'
#!/bin/bash
printf '%s\n' "$@" > "$INSTALL_TEST_API_LOG"
printf '{"message":"Not Found"}\n'
EOF
cat > "$TEMP_DIR/sub2api" <<'EOF'
#!/bin/bash
echo 'sub2api v1.2.3'
EOF
chmod +x "$TEMP_DIR/curl" "$TEMP_DIR/sub2api"

if INSTALL_TEST_API_LOG="$TEMP_DIR/api.log" PATH="$TEMP_DIR:$PATH" \
    UPDATE_GITHUB_TOKEN= bash -c '
        source <(head -n -1 "$1")
        INSTALL_DIR="$2"
        systemctl() {
            printf "%s\n" "$*" >> "$INSTALL_DIR/service.log"
        }
        upgrade
    ' bash "$ROOT_DIR/deploy/install.sh" "$TEMP_DIR" > "$TEMP_DIR/output.log" 2>&1; then
    echo "upgrade unexpectedly succeeded without a published release" >&2
    exit 1
fi

grep -Fxq 'https://api.github.com/repos/xingyu4j/sub2api/releases/latest' "$TEMP_DIR/api.log"
if [ -e "$TEMP_DIR/service.log" ]; then
    echo "upgrade changed the running service before resolving a release" >&2
    exit 1
fi
if [ -e "$TEMP_DIR/sub2api.backup" ]; then
    echo "upgrade replaced the backup before resolving a release" >&2
    exit 1
fi
test "$("$TEMP_DIR/sub2api" --version)" = 'sub2api v1.2.3'

echo "installer missing release upgrade checks passed"
